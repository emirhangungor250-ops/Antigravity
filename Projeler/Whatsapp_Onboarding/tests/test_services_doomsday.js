require('dotenv').config();
const notion = require('./services/notion');
const manychat = require('./services/manychat');
const { validatePhone } = require('./services/phoneValidator');
const resend = require('./services/resend');
const { ONBOARDING_FLOWS } = require('./config/templates');

const testCases = [
  {
    name: "1. Tamamen Alakasız Metin (Telefon Yok)",
    payload: {
      transaction_id: "test_tx_002",
      first_name: "NoPhone",
      last_name: "Test",
      answer_1: "Ben telefon kullanmıyorum, güvercinle haberleşiyorum."
    }
  },
  {
    name: "2. Karmaşık Cevap İçinden Telefon Çıkarma",
    payload: {
      transaction_id: "test_tx_003",
      first_name: "ComplexText",
      last_name: "Test",
      answer_1: "bana şu numaradan ulaşabilirsiniz: sıfır beş yüz otuz üç altı yüz altmış altı yirmi bir on üç"
    }
  },
  {
    name: "3. Race Condition (New Paid Member gelmemiş)",
    payload: {
      transaction_id: "test_tx_004_race",
      first_name: "Race",
      last_name: "Condition",
      answer_1: "05331234567"
    }
  },
  {
    name: "4. Çoklu Numara (Açık bağlam)",
    payload: {
      transaction_id: "test_tx_005",
      first_name: "MultiPhone1",
      last_name: "Test",
      answer_1: "Eski numaram 05321112233 ama iptal oldu, yenisi ve aktif olanı 05445556677."
    }
  },
  {
    name: "5. Çoklu Numara (Belirsiz bağlam)",
    payload: {
      transaction_id: "test_tx_006",
      first_name: "MultiPhone2",
      last_name: "Test",
      answer_1: "Annemin numarası 05551112233. 05332224455 da yazılabilir. Son olarak 05448889900."
    }
  }
];

async function simulateWebhookHandler(reqBody) {
  const { transaction_id, first_name, last_name, answer_1 } = reqBody;
  console.log(`[Webhook Simülasyon] Gelen Veri:`, reqBody);

  if (!answer_1) return { error: 'answer_1 zorunlu' };

  // 1. Phone validation
  const phoneResult = await validatePhone(answer_1);
  console.log(` -> Validasyon Sonucu:`, phoneResult);

  // 2. Notion find
  let member = await notion.findByTransactionId(transaction_id);
  if (!member) {
    console.log(` -> Kayıt bulunamadı (Race condition). Yeni oluşturuluyor...`);
    member = await notion.createMember({
      firstName: first_name,
      lastName: last_name || '',
      transactionId: transaction_id,
      onboardingStatus: "bekliyor"
    });
  }

  // 3. Dedup
  if (member.onboardingStatus === 'whatsapp' || member.onboardingStatus === 'tamamlandı') {
    return { success: true, skipped: true, reason: 'Already in onboarding' };
  }

  if (phoneResult.valid && phoneResult.confidence >= 0.5) {
    const existingPhone = await notion.findByPhone(phoneResult.normalized);
    if (existingPhone && existingPhone.id !== member.id) {
       console.log(` -> Telefon başka hesapta mevcut! Dedup tetiklendi.`);
       return { success: true, skipped: true, reason: 'Duplicate phone' };
    }
    console.log(` -> Notion WhatsApp statüsü güncelleniyor... (Güven: ${phoneResult.confidence})`);
    // mock update
    // await notion.updatePage(...)
    console.log(` -> ManyChat tetikleniyor...`);
    // mock manychat
    // await manychat.ensureSubscriberAndSendFlow(...)
    return { success: true, channel: 'whatsapp', phone: phoneResult.normalized };
  } else {
    console.log(` -> Geçersiz numara veya Düşük Güven. Email fallback tetikleniyor...`);
    return { success: true, channel: 'email', reason: !phoneResult.valid ? phoneResult.reason : "Düşük güven skoru", confidence: phoneResult.confidence };
  }
}

async function runTests() {
  console.log("🔥 WHATSAPP ONBOARDING SERVİS KIYAMET TESTİ BAŞLIYOR 🔥\n");
  for (const test of testCases) {
    console.log(`\n⏳ TEST: ${test.name}`);
    try {
      const result = await simulateWebhookHandler(test.payload);
      console.log(`✅ SONUÇ:`, result);
    } catch (e) {
      console.error(`❌ HATA:`, e.message);
    }
  }
  console.log(`\n🏁 Testler tamamlandı.`);
}

runTests();
