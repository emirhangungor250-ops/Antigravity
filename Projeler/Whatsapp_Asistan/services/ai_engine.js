// services/ai_engine.js
const fs = require('fs');
const path = require('path');
const OpenAI = require('openai');
const { config } = require('../config/env');
const log = require('../utils/logger');
const { queryKnowledge } = require('./knowledge_base');
const { getHistory } = require('./memory');
const { sendEscalationEmail } = require('./escalation');

const openai = new OpenAI({ apiKey: config.openaiApiKey });

// Sistem prompt'u prompts/system_prompt.md dosyasindan okunur.
// Kendi is akisinizi orada [KOSELI PARANTEZ] alanlarini doldurarak tanimlarsiniz.
const SYSTEM_PROMPT_TEMPLATE = fs.readFileSync(
  path.join(__dirname, '..', 'prompts', 'system_prompt.md'),
  'utf-8'
);

const escalationTools = [{
  type: 'function',
  function: {
    name: 'escalate_to_human',
    description: 'Konusmayi insan yetkiliye eskale et ve email bildirimi gonder. '
      + 'Asistan ON DANISMA hattidir; bilgi tabaninda cevap olan sorular eskale EDILMEZ, cevap verilir. '
      + 'Eskalasyon su durumlarda cagrilir: hassas konular (para iadesi, odeme problemi, '
      + 'sikayet/kizgin ton) ve bilgi tabaninda KESINLIKLE cevabi olmayan urun/politika sorulari. '
      + 'TODO: Eskalasyon kurallarinizi prompts/system_prompt.md icinde netlestirin.',
    parameters: {
      type: 'object',
      properties: {
        type: {
          type: 'string',
          enum: ['hassas_konu', 'bilinmeyen_soru'],
          description: 'hassas_konu: para iadesi, odeme problemi, sikayet/kizgin ton vb. '
            + 'bilinmeyen_soru: bilgi tabaninda kesinlikle cevap yok ve guvenle cevaplayamiyorsun.'
        },
        reason: {
          type: 'string',
          description: 'Eskalasyonun spesifik sebebini kisa ve net acikla.'
        }
      },
      required: ['type', 'reason']
    }
  }
}];

// ============================================================================
// POST-PROCESS SANITIZER
// ============================================================================
// LLM cevabi user'a gitmeden once burada denetlenir. Yasak rakam / isim /
// em-dash / iletim-tool eslesmemesi tespit edilirse bir kez retry tetiklenir.
//
// TODO: Asagidaki kurallar SIZIN is akisiniza gore doldurulmali. Bu bir
// sablondur — markaniza ozgu yasak rakamlari, yasak ifadeleri ve link
// kurallarini kendiniz tanimlayin.

// Asistanin telaffuz etmesi YASAK olan rakamlar (orn: eski/yanlis fiyatlar).
// Kendi yasak rakamlarinizi buraya yazin, yoksa bos birakin.
const BANNED_AMOUNTS = [];

// Asistanin kullanmasi YASAK ifadeler. Her biri { id, re, label }.
// Ornek olarak yaygin "sahte randevu vaadi" pattern'leri birakildi.
const BANNED_PHRASES = [
  { id: 'team_call', re: /\bekibimiz\s+(arayacak|d[öo]necek|seni)/i, label: '"ekibimiz arayacak/dönecek"' },
  { id: 'call_user', re: /\bseni\s+arayal[ıi]m\b/i, label: '"seni arayalım"' },
  { id: 'randevu', re: /\brandevu\s*(ayarlayal[ıi]m|alal[ıi]m|verel[ıi]m|talep|olu[şs]tural[ıi]m|verme)/i, label: '"randevu ayarlayalım"' },
  { id: 'gun_belirle', re: /g[üu]n\s+belirleyel[ıi]m/i, label: '"gün belirleyelim"' },
  // TODO: Markaniza ozgu yasak ifadeleri (yanlis paket iddiasi, uydurma urun adi,
  // ekip uyesi ismi vb.) buraya ekleyin.
];

// Eskalasyon imza cumlesini yakalayan pattern'ler. Asistan bu cumleyi
// yazdiysa tool da cagrilmis olmali.
const ILETIM_PATTERNS = [
  /\bileti(yor|r)um\b/i,
  /\biletece[ğg]im\b/i,
  /\bilettim\b/i,
  /\bsana\s+d[öo]n[üu][şs]\s+yap[ıi]l(acak|aca[ğg][ıi]z)\b/i,
  /\byetkili(ye|mize)?\s+(ula[şs]acak|d[öo]necek)\b/i,
];

// App link push: kullanici app/uygulama/iPhone/Android sormadikca asistan
// kendiliginden link verirse ihlal.
const APP_LINK_RE = /(apps\.apple\.com|play\.google\.com)/i;
const APP_INTENT_RE = /(\bapp\b|uygulama|iphone|android|mobil\b|playstore|app\s*store)/i;

// Sahte indirim / kampanya uydurma.
const FAKE_DISCOUNT_RE = /(indirim\s+paketi\s+açıl|kampanya\s+(başl|açıl|devrede)|özel\s+fırsat|promosyon\s+devrede)/i;

function checkViolations(text, toolCalled, userContext = '') {
  const violations = [];

  // 1) Yasak rakamlar — $X, X$, "X dolar" formlarinin hepsi
  for (const amount of BANNED_AMOUNTS) {
    const reDollarBefore = new RegExp(`\\$\\s*${amount}(?!\\d)`);
    const reDollarAfter = new RegExp(`(?<!\\d)${amount}\\s*\\$`);
    const reSpelled = new RegExp(`(?<!\\d)${amount}\\s+(dolar|usd|dolara)\\b`, 'i');
    if (reDollarBefore.test(text) || reDollarAfter.test(text) || reSpelled.test(text)) {
      violations.push({ id: `price_$${amount}`, label: `yasak fiyat $${amount}` });
    }
  }

  // 2) Yasak ifadeler
  for (const p of BANNED_PHRASES) {
    if (p.re.test(text)) violations.push({ id: p.id, label: p.label });
  }

  // 3) Em-dash (madde işareti veya cümle ayırıcı olarak kullanımı)
  if (/ — /.test(text) || /(\n|^)—\s/.test(text) || /:\s*—/.test(text)) {
    violations.push({ id: 'em_dash', label: 'em-dash karakteri' });
  }

  // 4) İletim cümlesi var ama tool çağrılmadı
  const hasIletim = ILETIM_PATTERNS.some(re => re.test(text));
  if (hasIletim && !toolCalled) {
    violations.push({ id: 'iletim_without_tool', label: '"iletirim" cümlesi tool çağrısı olmadan kullanıldı' });
  }

  // 5) App link push (kullanıcı sormadan iPhone/Android link sunmuş)
  if (APP_LINK_RE.test(text) && !APP_INTENT_RE.test(userContext)) {
    violations.push({ id: 'app_link_unprompted', label: 'app linki kullanıcı sormadan sunuldu' });
  }

  // 6) Sahte indirim/kampanya uydurma
  if (FAKE_DISCOUNT_RE.test(text)) {
    violations.push({ id: 'fake_discount', label: 'uydurma indirim/kampanya/promosyon bahsi' });
  }

  return violations;
}

async function regenerateWithFeedback(originalMessages, violations) {
  const violationList = violations.map(v => `- ${v.label}`).join('\n');
  const feedback = `Önceki cevabın aşağıdaki kuralları çiğnedi:\n${violationList}\n\nLütfen aynı içeriği bu kurallara UYARAK yeniden üret. Yasak ifadelerin yerine sistem prompt'undaki alternatifleri kullan.`;

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

    const ragChunks = await queryKnowledge(options.ragQueryOverride || currentMessage);
    const history = options.skipHistory ? [] : await getHistory(subscriberId, 20);
    const todayDate = new Date().toLocaleDateString('tr-TR', { day: 'numeric', month: 'long', year: 'numeric' });

    // Sistem prompt'u sablondan uretilir; placeholder'lar runtime degerlerle doldurulur.
    const systemPrompt = SYSTEM_PROMPT_TEMPLATE
      .replace(/\{\{DETECTED_LANGUAGE\}\}/g, detectedLanguage)
      .replace(/\{\{TODAY_DATE\}\}/g, todayDate)
      .replace(/\{\{RAG_CHUNKS\}\}/g, ragChunks)
      .trim();

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
        if (tool_call.function.name === 'escalate_to_human') {
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
    // userContext: son N user mesajı + current message (app/intent kontrolü için)
    const userContext = [
      ...history.filter(m => m.role === 'user').slice(-5).map(m => m.content),
      currentMessage
    ].join(' \n ');

    // Re-escalation guard: history'de daha önce iletim cümlesi geçtiyse, yeni iletim cümlesi tekrar etmesin
    const priorIletim = history
      .filter(m => m.role === 'assistant')
      .some(m => ILETIM_PATTERNS.some(re => re.test(m.content || '')));
    const currentHasIletim = ILETIM_PATTERNS.some(re => re.test(aiResponse));
    if (priorIletim && currentHasIletim) {
      log.warn(`[ai_engine] re_escalation_guard_triggered — sabit cevap dönülüyor`);
      // TODO: Kendi "daha önce iletildi" sabit cevabinizi yazin.
      aiResponse = 'Bu konuyu daha önce yetkiliye ilettim. Henüz dönüş olmadıysa alternatif iletişim kanalımızdan da yazabilirsin.';
      toolCalled = false; // Mail re-tetiklenmesin — ai_engine seviyesinde kararı override
    }

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
          // Retry de kirli; daha temiz olanı seç
          aiResponse = retryViolations.length < violations.length ? retried : aiResponse;

          // Hard fallback: kritik kilit kategorileri için deterministik cevap.
          // TODO: Kendi kritik kategorileriniz icin sabit guvenli cevaplar tanimlayin.
          const criticalIds = new Set(retryViolations.map(v => v.id));
          if (criticalIds.has('fake_discount')) {
            aiResponse = 'Sabit kampanya veya indirim uygulamıyoruz. Güncel fiyatlar için kayıt sayfamıza bakabilirsin.';
            log.warn(`[ai_engine] hard_fallback_applied: fake_discount`);
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
  // Test/debug için ihraç
  _internal: { checkViolations, BANNED_AMOUNTS, BANNED_PHRASES }
};
