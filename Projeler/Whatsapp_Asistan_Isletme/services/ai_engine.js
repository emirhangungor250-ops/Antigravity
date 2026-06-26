// services/ai_engine.js
const OpenAI = require('openai');
const { config } = require('../config/env');
const log = require('../utils/logger');
const { queryKnowledge } = require('./knowledge_base');
const { getHistory } = require('./memory');
const { sendEscalationEmail } = require('./escalation');

const openai = new OpenAI({ apiKey: config.openaiApiKey });

const escalationTools = [{
  type: 'function',
  function: {
    name: 'escalate_to_team',
    description: 'Konusmayi satis/destek ekibine eskale et ve email bildirimi gonder. Sadece su durumlarda cagir: (1) Spesifik satin alma/rezervasyon talebi (musteri gerekli bilgileri verdi, teyit ve islem olusturma gerekiyor), (2) Iptal/iade/degisiklik talebi, (3) Sikayet veya kizgin ton, (4) KB\'de cevabi olmayan operasyonel soru. KB\'de cevap varsa eskale etme, cevabi ver.',
    parameters: {
      type: 'object',
      properties: {
        type: {
          type: 'string',
          enum: ['rezervasyon_talebi', 'iptal_iade', 'sikayet', 'bilinmeyen_soru'],
          description: 'Eskalasyon turu.'
        },
        reason: {
          type: 'string',
          description: 'Eskalasyon sebebini kisa ve net acikla (Turkce). Musterinin verdigi tarih/villa/kisi sayisi gibi spesifik bilgileri dahil et.'
        }
      },
      required: ['type', 'reason']
    }
  }
}];

// ============================================================================
// POST-PROCESS SANITIZER
// ============================================================================
// LLM cevabı user'a gitmeden önce burada denetlenir.

const BANNED_PHRASES = [
  // Sahte randevu / kesin söz cümleleri
  { id: 'kesin_rezervasyon', re: /\b(kesin\s+rezervasyon\s+olu[şs]tur|villay[ıi]\s+blok\s+ettim|rezervasyonu\s+onaylad[ıi]m)\b/i, label: 'asistan kendi başına rezervasyon onayı verdi' },
  { id: 'fake_discount', re: /(indirim\s+paketi\s+a[çc][ıi]l|kampanya\s+(ba[şs]l|a[çc][ıi]l|devrede)|özel\s+f[ıi]rsat|promosyon\s+devrede)/i, label: 'uydurma indirim/kampanya bahsi' },
];

const ILETIM_PATTERNS = [
  /\bileti(yor|r)um\b/i,
  /\biletece[ğg]im\b/i,
  /\bilettim\b/i,
  /\bekibimiz\s+(donecek|d[öo]necek|ulaşacak)\b/i,
  /\brezervasyon\s+ekibi(miz)?\s+(donecek|d[öo]necek|ulaşacak)\b/i,
];

function checkViolations(text, toolCalled, userContext = '') {
  const violations = [];

  // 1) Yasak ifadeler
  for (const p of BANNED_PHRASES) {
    if (p.re.test(text)) violations.push({ id: p.id, label: p.label });
  }

  // 2) Em-dash (madde işareti veya cümle ayırıcı olarak kullanımı)
  if (/ — /.test(text) || /(\n|^)—\s/.test(text) || /:\s*—/.test(text)) {
    violations.push({ id: 'em_dash', label: 'em-dash karakteri' });
  }

  // 3) İletim cümlesi var ama tool çağrılmadı
  const hasIletim = ILETIM_PATTERNS.some(re => re.test(text));
  if (hasIletim && !toolCalled) {
    violations.push({ id: 'iletim_without_tool', label: '"iletirim/ekibimiz dönecek" cümlesi tool çağrısı olmadan kullanıldı' });
  }

  return violations;
}

async function regenerateWithFeedback(originalMessages, violations) {
  const violationList = violations.map(v => `- ${v.label}`).join('\n');
  const feedback = `Önceki cevabın aşağıdaki kuralları çiğnedi:\n${violationList}\n\nLütfen aynı içeriği bu kurallara UYARAK yeniden üret.`;

  const retryMessages = [
    ...originalMessages,
    { role: 'system', content: feedback }
  ];

  const response = await openai.chat.completions.create({
    model: 'gpt-4.1-mini',
    messages: retryMessages,
    temperature: 0.2
  });

  return response.choices[0].message.content.trim();
}

// ============================================================================
// MAIN: generateResponse
// ============================================================================

async function generateResponse(subscriberId, currentMessage, detectedLanguage, subscriberInfo, options = {}) {
  try {
    log.info(`[ai_engine] AI cevabı üretiliyor...`, { subscriberId, language: detectedLanguage });

    const ragChunks = await queryKnowledge(currentMessage);
    const history = options.skipHistory ? [] : await getHistory(subscriberId, 20);
    const todayDate = new Date().toLocaleDateString('tr-TR', { day: 'numeric', month: 'long', year: 'numeric' });

    const systemPrompt = `
[ROL]
Sen ${config.businessName} işletmesinin WhatsApp danışmanısın. ${config.businessName}, ${config.businessSector} alanında hizmet veren bir işletmedir. İşletmeye dair tüm bilgiler aşağıdaki [İLGİLİ BİLGİLER] bölümünden (bilgi tabanı) gelir.

Sen FAQ botu değilsin. Müşteriyi dinler, ihtiyacını anlar, doğru ürün/hizmeti önerirsin ve satış aşamasında ekibe devredersin. Cevap üretirken ${detectedLanguage} dilinde yaz.

[KONUŞMA AKIŞI]
1. Açılış keşfi (2-3 kısa soru): müşterinin ihtiyacını anlamak için sorular sor (bilgi tabanındaki konuşma akışını izle).
2. Profil eşleştirmesi: müşterinin özel ihtiyaçlarını tespit et.
3. Uygun seçenekleri öner: KB'de geçen kategorilerden müşterinin profiline uyanları sun. Spesifik ürün adı veya fiyat söylemeden önce KB'de o bilgi var mı kontrol et.
4. Kapanış: Satış için ekip devralacak; talep netse escalate_to_team tool'u çağrılır.

[İLETİŞİM KURALLARI VE TON]
- Kısa ve öz yaz. İdeal 2-4 cümle, maksimum 6-8 cümle.
- Cümleleri kısa tut; tek cümlede 15 kelimeyi geçirme.
- Özel biçimlendirme kullanma (*, **, \`, #, > gibi). Sadece düz metin.
- Emoji çok az veya hiç.
- Sade Türkçe kullan. Samimi ol, "siz" dili kullan.
- Em-dash (—) YASAK. Liste yapacaksan satır başına yeni cümle yaz.

[FİYAT KURALI]
KB'de fiyat veriliyorsa o fiyatı söyle. KB'de yoksa fiyatın koşullara göre değiştiğini söyle ve bilgi topla. Kendin fiyat uydurma.

KB'de güncel kampanya/indirim yoksa sahte kampanya/indirim uydurma.

[ESKALASYON KURALLARI]
escalate_to_team tool'unu şu durumlarda çağır:
1. Müşteri spesifik bir satın alma/rezervasyon talep etti (gerekli bilgiler netleşti).
2. İptal, iade veya değişiklik talebi.
3. Şikayet veya kızgın ton.
4. KB'de cevabı olmayan operasyonel soru.

Tool çağırdıktan sonra kullanıcıya: "Ekibimiz en kısa sürede size dönecek. WhatsApp veya e-posta ile ulaşılacaksınız."

Tool çağırmadan "ekibimiz dönecek / iletiyorum / ileteceğim" CÜMLELERİNİ KESİNLİKLE YAZMA. Alternatif: KB'deki iletişim bilgisini ver.

[İLETİŞİM BİLGİLERİ]
İşletmenin telefon, WhatsApp, e-posta, ofis ve web bilgileri [İLGİLİ BİLGİLER] bölümündeki bilgi tabanından gelir. Oradaki güncel bilgiyi kullan; bilgi yoksa uydurma.

[KRİTİK YASAKLAR]
- KB dışı fiyat uydurma.
- Sahte satış/rezervasyon onayı verme. "Siparişinizi oluşturdum / ürünü ayırdım" YASAK. Onayı ekip verir.
- Sahte indirim veya kampanya uydurma.
- Yapay zeka olduğunu inkar etme. Sorulursa dürüstçe söyle.
- Em-dash kullanma.
- Müşteri başka bir dilde yazıyorsa o dilde cevap ver (İngilizce, Almanca, Rusça vb.).

[BUGÜNÜN TARİHİ]
${todayDate}

[İLGİLİ BİLGİLER]
${ragChunks}
    `.trim();

    const messages = [
      { role: 'system', content: systemPrompt }
    ];

    for (const msg of history) {
      messages.push({ role: msg.role, content: msg.content });
    }

    messages.push({ role: 'user', content: currentMessage });

    log.debug(`[ai_engine] OpenAI API'sine istek atılıyor...`);
    const response = await openai.chat.completions.create({
      model: 'gpt-4.1-mini',
      messages: messages,
      tools: escalationTools,
      tool_choice: 'auto',
      temperature: 0.2
    });

    const responseMessage = response.choices[0].message;
    let toolCalled = false;
    let aiResponse;
    let lastMessageStack = messages;

    if (responseMessage.tool_calls && responseMessage.tool_calls.length > 0) {
      toolCalled = true;
      for (const tool_call of responseMessage.tool_calls) {
        if (tool_call.function.name === 'escalate_to_team') {
          try {
            const args = JSON.parse(tool_call.function.arguments);
            const { type, reason } = args;

            const recentMessages = history.slice(-5);

            sendEscalationEmail({
              type,
              subscriberId: subscriberInfo.subscriberId,
              phoneNumber: subscriberInfo.phoneNumber,
              reason,
              recentMessages
            }).catch(err => log.error(`[ai_engine] sendEscalationEmail hatası: ${err.message}`, err));

            messages.push(responseMessage);
            messages.push({
              role: 'tool',
              tool_call_id: tool_call.id,
              content: 'Eskalasyon emaili gonderildi.'
            });

          } catch (e) {
            log.error(`[ai_engine] Tool parse hatasi: ${e.message}`);
          }
        }
      }

      const secondResponse = await openai.chat.completions.create({
        model: 'gpt-4.1-mini',
        messages: messages,
        temperature: 0.3
      });

      aiResponse = secondResponse.choices[0].message.content.trim();
      lastMessageStack = messages;
      log.info(`[ai_engine] AI cevabı (eskalasyon sonrasi) başarıyla üretildi.`);
    } else {
      aiResponse = responseMessage.content.trim();
      log.info(`[ai_engine] AI cevabı başarıyla üretildi.`);
    }

    // ----- POST-PROCESS SANITIZE -----
    const userContext = [
      ...history.filter(m => m.role === 'user').slice(-5).map(m => m.content),
      currentMessage
    ].join(' \n ');

    const violations = checkViolations(aiResponse, toolCalled, userContext);

    if (violations.length > 0) {
      log.warn(`[ai_engine] sanitize_violations_first_pass: ${violations.map(v => v.id).join(',')}`);

      try {
        const retried = await regenerateWithFeedback(lastMessageStack, violations);
        const retryViolations = checkViolations(retried, toolCalled, userContext);

        if (retryViolations.length === 0) {
          log.info(`[ai_engine] sanitize_retry_clean`);
          aiResponse = retried;
        } else {
          log.error(`[ai_engine] sanitize_violations_persist_after_retry: ${retryViolations.map(v => v.id).join(',')}`, {
            subscriberId,
            firstPassViolations: violations.map(v => v.id),
            retryViolations: retryViolations.map(v => v.id),
          });
          aiResponse = retryViolations.length < violations.length ? retried : aiResponse;

          // Hard fallback
          const criticalIds = new Set(retryViolations.map(v => v.id));
          if (criticalIds.has('fake_discount')) {
            aiResponse = 'Güncel kampanya ve indirimler için ekibimiz size bilgi verebilir. Sizi ekibimize yönlendireyim.';
            log.warn(`[ai_engine] hard_fallback_applied: fake_discount`);
          } else if (criticalIds.has('kesin_rezervasyon')) {
            aiResponse = 'Ekibimiz müsaitlik kontrolü sonrası size kesin teklif iletir. Gerekli bilgileri paylaşırsanız hemen yönlendireyim.';
            log.warn(`[ai_engine] hard_fallback_applied: kesin_rezervasyon`);
          }
        }
      } catch (err) {
        log.error(`[ai_engine] retry_exception: ${err.message}`);
      }
    }

    if (options.returnMeta) {
      return { text: aiResponse, toolCalled, violations };
    }
    return aiResponse;
  } catch (error) {
    log.error(`[ai_engine] generateResponse hatası: ${error.message}`, error);
    throw error;
  }
}

module.exports = {
  generateResponse,
  _internal: { checkViolations, BANNED_PHRASES }
};
