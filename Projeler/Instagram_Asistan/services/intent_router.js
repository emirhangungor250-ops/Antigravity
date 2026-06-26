// services/intent_router.js
// F3 cheap — Haiku 4.5 ile intent classification + opsiyonel quick_response.
const { structuredCall } = require('./ai_cheap');
const log = require('../utils/logger');

const INTENTS = ['ai_factory', 'video_source', 'b2b', 'general', 'refuse_contact'];

const CLASSIFIER_TOOL = {
  name: 'classify_and_respond',
  description: "Kullanıcının niyetini sınıflandır ve gerekirse kısa cevap üret.",
  input_schema: {
    type: 'object',
    properties: {
      intent: {
        type: 'string',
        enum: INTENTS,
        description: "Kullanıcının niyeti."
      },
      confidence: {
        type: 'number',
        description: '0.0-1.0, sınıflandırmaya güven.'
      },
      needs_deep_thinking: {
        type: 'boolean',
        description: 'true ise quick_response üretme, daha güçlü modele (Sonnet) devret. false ise quick_response doldur.'
      },
      quick_response: {
        type: 'string',
        description: 'needs_deep_thinking=false ise doğrudan kullanıcıya gidecek kısa cevap. Aksi halde boş bırak.'
      },
      profile_signal: {
        type: 'object',
        description: 'Kullanıcı mesajından çıkarılan profil sinyali (varsa)',
        properties: {
          is_business_owner: { type: 'boolean' },
          employee_count: { type: 'integer' },
          sector: { type: 'string' },
          mentioned_member: { type: 'boolean', description: 'Mevcut üye olduğunu söyledi mi' }
        }
      },
      rationale: { type: 'string' }
    },
    required: ['intent', 'confidence', 'needs_deep_thinking', 'rationale']
  }
};

// Markaya özel intent tanımları aşağıdaki şablonda. Kendi intent'lerinizi ve
// dil kurallarınızı buradan değiştirin. CLASSIFIER_TOOL.input_schema'daki
// `intent` enum'unu eşit tutmaya dikkat edin.
const CHEAP_SYSTEM = `
Sen [MARKA ADI]'nın Instagram DM asistanı'nın hızlı sınıflandırıcısısın.
Görevin: kullanıcının niyetini 5 sınıftan birine sokmak ve sade cevaplanabilecek durumlarda doğrudan kısa cevap üretmek.

5 intent (kendi iş akışınıza göre uyarlayın):
1. ai_factory: [Topluluk/Kurs ürününüz hakkında soru. Paket/fiyat/içerik/kayıt soruları.]
2. video_source: [Sosyal medya yorumu üzerinden gelen kaynak/içerik talepleri.]
3. b2b: [Açık ve doğrudan hizmet/proje teklifi.]
4. general: [Genel sektör/araç soruları, ürününüzle ilgisi olmayan.]
5. refuse_contact: [Saf "seninle birebir görüşmek istiyorum" talebi.]

ÖNEMLİ:
- Şüphede → b2b veya en güvenli intent'e yönlendir.
- Selamlaşma → varsayılan intent.

needs_deep_thinking=true VER:
- Birden çok bağlam içeren veya hassas konular (para iadesi, ödeme problemi)
- Confidence < 0.65

needs_deep_thinking=false VER (quick_response da üret):
- Tek kelime / kısa tetik mesaj (kaynak yönlendirme bilgisi yeterli)
- refuse_contact (sabit template basılacak)

ASLA spesifik fiyat veya marka-özel kuralı kendiniz söyleyin — onlar deep model'in işi.
quick_response yazarken: em-dash (—) YASAK; tek cümlede 12 kelimeyi geçirme; toplam 3 cümleyi geçme.
`.trim();

async function classify(currentMessage, history = []) {
  const trimmedHistory = history.slice(-10).map(m => ({
    role: m.role === 'system' ? 'user' : m.role,
    content: m.content
  }));

  const messages = [
    ...trimmedHistory,
    { role: 'user', content: currentMessage }
  ];

  try {
    const result = await structuredCall({
      system: CHEAP_SYSTEM,
      messages,
      tool: CLASSIFIER_TOOL,
      maxTokens: 600
    });

    // Confidence guard: < 0.65 → zorla deep
    if (typeof result.confidence === 'number' && result.confidence < 0.65) {
      result.needs_deep_thinking = true;
      result.quick_response = '';
    }
    // Refuse_contact için quick_response engelle (deep path sabit template basacak)
    if (result.intent === 'refuse_contact') {
      result.needs_deep_thinking = false; // routing için sinyal — ai_engine sabit template basacak
    }

    log.info(`[intent_router] classified`, {
      intent: result.intent,
      confidence: result.confidence,
      deep: result.needs_deep_thinking
    });
    return result;
  } catch (err) {
    log.error(`[intent_router] classify hatası: ${err.message}`, err);
    return {
      intent: 'ai_factory',
      confidence: 0.0,
      needs_deep_thinking: true,
      quick_response: '',
      rationale: `classifier_error: ${err.message}`
    };
  }
}

module.exports = { classify, INTENTS, CLASSIFIER_TOOL };
