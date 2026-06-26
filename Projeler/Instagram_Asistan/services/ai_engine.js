// services/ai_engine.js
// Instagram DM asistanı orchestrator.
// Akış: rate-limit→intent→F4 refuse → cheap quick → RAG → Sonnet → sanitize → reply.
const fs = require('fs');
const path = require('path');
const log = require('../utils/logger');
const { config } = require('../config/env');
const intentRouter = require('./intent_router');
const aiExpensive = require('./ai_expensive');
const aiCheap = require('./ai_cheap');
const kbFactory = require('./kb_factory');
const kbVideos = require('./kb_videos');
const { getHistory, updateProfile, getSubscriber } = require('./memory');
const { sendEscalationEmail } = require('./escalation');
const { sendProductCards } = require('./manychat');
const sanitize = require('../utils/sanitize');

// ============================================================================
// F4 — sabit refuse template
// ============================================================================
// Kendi marka politikanıza göre doldurun. Direkt birebir mesajlaşmaya kapalı
// olduğunuzu ve alternatif kanalı (topluluk, Discord, forum vb.) duyurabilirsiniz.
const REFUSE_TEMPLATE = `Birebir mesajlaşmaya zamanım çok kısıtlı. Topluluğumuza katılırsan oradan birebir cevap verebiliyorum.

<TOPLULUK_URL>`;

// Trigger-word DM kabulü (kullanıcı sadece tek kelime atmış)
const TRIGGER_GUIDANCE_TEMPLATE = `Bu kelime Reels'in altına yorum olarak yazılınca otomatik kaynak DM'i tetikliyor. İlgili videonun altına yorum olarak yazarsan birkaç saniye içinde kaynak DM olarak gelir.`;

// ============================================================================
// Tools (Anthropic Sonnet)
// ============================================================================
const ESCALATE_TOOL = {
  name: 'escalate_to_human',
  description: "KB'de cevabı olmayan veya hassas durumları yöneticiye e-posta ile bildir. KULLAN: para iadesi, ödeme problemi, şikayet/kızgın ton, ürün/politika sorusu KB'de yok. KULLANMA: üye teknik sorusu (forum/topluluğa yönlendir), kapsam dışı sorular ('kapsamım dışında' de), tekrar eden eskalasyon (re_escalation_guard).",
  input_schema: {
    type: 'object',
    properties: {
      type: {
        type: 'string',
        enum: ['hassas_konu', 'bilinmeyen_soru', 'b2b_uygun'],
        description: "hassas_konu: para iadesi/şikayet. bilinmeyen_soru: KB gap. b2b_uygun: B2B kriterleri tutuyor."
      },
      reason: { type: 'string', description: 'Kısa açıklama' }
    },
    required: ['type', 'reason']
  }
};

const LOOKUP_VIDEO_TOOL = {
  name: 'lookup_video',
  description: "Yayınlanmış video transcript/caption RAG'inde semantic arama yap. KULLAN: kullanıcı 'şu işi hangi araç yapar', 'şu videodaki tool ne' tarzı içerik sorduğunda. Sonuç: ilgili videoların başlığı + içeriği + URL.",
  input_schema: {
    type: 'object',
    properties: {
      query: { type: 'string', description: 'Aranacak konu/araç/işlev' }
    },
    required: ['query']
  }
};

const RECORD_PROFILE_TOOL = {
  name: 'record_profile',
  description: 'Kullanıcı hakkında öğrenilen profili kaydet (sticky, tekrar sorma). Sadece açık verilerle.',
  input_schema: {
    type: 'object',
    properties: {
      is_business_owner: { type: 'boolean' },
      employee_count: { type: 'integer' },
      sector: { type: 'string' },
      is_member: { type: 'boolean' },
      notes: { type: 'string' }
    }
  }
};

const SHOW_PRODUCT_CARDS_TOOL = {
  name: 'show_product_cards',
  description: "ManyChat üzerinden kullanıcıya görsel Product Card seti gönder. Kart variant'ları kullanıcının ihtiyacına göre seçilir. Tool tetiklenince sen kısa bir tanıtım metni de üretirsin (1-2 cümle); o metin kartların hemen öncesinde gider.\n\n[VARIANT'LARI BURADA TANIMLAYIN — kendi ürün/hizmet setinize göre.]\n\nThread başına her variant MAX 1 kez gösterilir.",
  input_schema: {
    type: 'object',
    properties: {
      variant: {
        type: 'string',
        description: 'Hangi kart seti gösterilecek (kendi variant adlarınızı tanımlayın)'
      },
      reason: { type: 'string', description: 'Neden bu variant seçildi — kısa açıklama' }
    },
    required: ['variant', 'reason']
  }
};

// ============================================================================
// System prompt builder
// ============================================================================
// Sistem prompt'unu prompts/system_prompt.md dosyasından okuruz. Bu dosya MARKA
// SAHIBININ kendi tonunu, kurallarını ve URL'lerini içerir; sadece template
// olarak verilmiştir, kendi içeriğinizi yazın.
const SYSTEM_PROMPT_TEMPLATE = (() => {
  const promptPath = path.join(__dirname, '..', 'prompts', 'system_prompt.md');
  try {
    return fs.readFileSync(promptPath, 'utf8');
  } catch (err) {
    log.warn(`[ai_engine] system_prompt.md okunamadı: ${err.message}`);
    return 'Sen yardımsever bir asistansın. {{DETECTED_LANGUAGE}} dilinde cevap ver.\n\n'
      + '[BİLGİ TABANI]\n{{RAG_CHUNKS}}\n\n'
      + '[PROFİL]\n{{PROFILE_BLOCK}}\n\n'
      + '[INTENT]\n{{INTENT}}\n\n'
      + 'TODO: Kurallarınızı prompts/system_prompt.md içinde netleştirin.';
  }
})();

function todayStr() {
  return new Date().toLocaleDateString('tr-TR', { day: 'numeric', month: 'long', year: 'numeric' });
}

function buildProfileBlock(profile) {
  if (!profile || typeof profile !== 'object') return '(profil bilinmiyor)';
  const parts = [];
  if (profile.is_business_owner === true) parts.push('işletme sahibi');
  if (profile.is_business_owner === false) parts.push('bireysel');
  if (typeof profile.employee_count === 'number') parts.push(`${profile.employee_count} personel`);
  if (profile.sector) parts.push(`sektör: ${profile.sector}`);
  if (profile.is_member === true) parts.push('mevcut üye');
  if (profile.notes) parts.push(`not: ${profile.notes}`);
  return parts.length ? parts.join(', ') : '(profil bilinmiyor)';
}

function buildSystemPrompt(intent, ragContext, profile = {}, firstName = null, language = 'tr') {
  return SYSTEM_PROMPT_TEMPLATE
    .replace(/\{\{DETECTED_LANGUAGE\}\}/g, language)
    .replace(/\{\{TODAY_DATE\}\}/g, todayStr())
    .replace(/\{\{INTENT\}\}/g, intent || 'general')
    .replace(/\{\{FIRST_NAME\}\}/g, firstName || '')
    .replace(/\{\{PROFILE_BLOCK\}\}/g, buildProfileBlock(profile))
    .replace(/\{\{RAG_CHUNKS\}\}/g, ragContext || '(yok)');
}

// ============================================================================
// RAG seçimi
// ============================================================================
async function pickRag(intent, query) {
  if (intent === 'ai_factory' || intent === 'b2b') {
    return await kbFactory.query(query);
  }
  if (intent === 'video_source') {
    const v = await kbVideos.query(query);
    return v.formatted || '';
  }
  if (intent === 'general') {
    const [a, v] = await Promise.all([
      kbFactory.query(query, { count: 4 }),
      kbVideos.query(query, { count: 3 })
    ]);
    return [a, v.formatted].filter(Boolean).join('\n\n');
  }
  return '';
}

// ============================================================================
// MAIN
// ============================================================================
async function generateResponse(subscriberId, currentMessage, language, subscriberInfo = {}, options = {}) {
  try {
    log.info(`[ai_engine] generateResponse start`, { subscriberId });

    const history = options.skipHistory ? [] : await getHistory(subscriberId, 20);
    const subscriber = await getSubscriber(subscriberId).catch(() => null);
    const profile = subscriber?.profile_json || {};

    // 1. Intent classify (cheap)
    const classifyMessage = options.ragQueryOverride || currentMessage;
    const routerResult = await intentRouter.classify(classifyMessage, history);

    // 2. F4 — refuse_contact (sabit template)
    if (routerResult.intent === 'refuse_contact') {
      // İstisna: profile_json.is_business_owner === true ise b2b'ye relay
      if (profile?.is_business_owner === true && (profile?.employee_count || 0) >= 20) {
        log.info(`[ai_engine] refuse→b2b (profile sticky)`, { subscriberId });
        routerResult.intent = 'b2b';
        routerResult.needs_deep_thinking = true;
      } else {
        log.info(`[ai_engine] refuse_contact → sabit template`);
        return _wrap(REFUSE_TEMPLATE, { intent: 'refuse_contact', modelUsed: 'static' }, options);
      }
    }

    // 3. Tek tetik kelime (video_source intent + needs_deep_thinking false + kısa kelime)
    if (routerResult.intent === 'video_source' && !routerResult.needs_deep_thinking) {
      const reply = routerResult.quick_response && routerResult.quick_response.length > 30
        ? routerResult.quick_response
        : TRIGGER_GUIDANCE_TEMPLATE;
      return _wrap(reply, { intent: 'video_source', modelUsed: 'haiku' }, options);
    }

    // 4. Cheap quick_response (deep thinking gerekmiyorsa)
    if (!routerResult.needs_deep_thinking && routerResult.quick_response && routerResult.quick_response.length > 20) {
      return _wrap(routerResult.quick_response, { intent: routerResult.intent, modelUsed: 'haiku' }, options);
    }

    // 5. Deep path — RAG + Sonnet
    const ragContext = await pickRag(routerResult.intent, classifyMessage);
    const systemPrompt = buildSystemPrompt(routerResult.intent, ragContext, profile, subscriberInfo.firstName, language);

    // History'i Anthropic formatına çevir (system mesajı dışarıda)
    const messages = [];
    for (const m of history) {
      if (m.role !== 'user' && m.role !== 'assistant') continue;
      messages.push({ role: m.role, content: m.content });
    }
    messages.push({ role: 'user', content: currentMessage });

    // Tool seti intent'e göre
    const tools = [ESCALATE_TOOL, RECORD_PROFILE_TOOL];
    if (routerResult.intent === 'video_source' || routerResult.intent === 'general') {
      tools.push(LOOKUP_VIDEO_TOOL);
    }
    if (routerResult.intent === 'ai_factory' || routerResult.intent === 'general' || routerResult.intent === 'b2b') {
      tools.push(SHOW_PRODUCT_CARDS_TOOL);
    }

    let toolEscalated = false;
    let escalationCall = null;
    let profilePatch = null;
    let productCardsQueued = false;
    let productCardsVariant = null;

    async function handleTool(name, input) {
      log.info(`[ai_engine] tool_use: ${name}`, input);
      if (name === 'escalate_to_human') {
        toolEscalated = true;
        escalationCall = input;
        return JSON.stringify({ status: 'queued', message: 'Eskalasyon kuyruğa alındı, kullanıcıya cevap üretmeye devam et.' });
      }
      if (name === 'record_profile') {
        profilePatch = input;
        return JSON.stringify({ status: 'ok' });
      }
      if (name === 'lookup_video') {
        const v = await kbVideos.query(input.query || currentMessage, { count: 4 });
        if (!v.formatted) return JSON.stringify({ status: 'empty', message: 'İlgili video bulunamadı.' });
        return JSON.stringify({ status: 'ok', context: v.formatted.substring(0, 4000) });
      }
      if (name === 'show_product_cards') {
        productCardsQueued = true;
        productCardsVariant = input.variant || 'default';
        return JSON.stringify({
          status: 'sent',
          message: 'Kartlar arayüze gönderildi. Senin görevin sadece 1-2 cümle kısa bir giriş cümlesi yazmak.'
        });
      }
      return 'unknown_tool';
    }

    const result = await aiExpensive.generate({
      system: systemPrompt,
      messages,
      tools,
      handleTool,
      maxTokens: 1024,
      maxToolHops: 3
    });

    let aiResponse = result.text || '';
    if (!aiResponse || aiResponse.length < 3) {
      aiResponse = 'Sorununu tam anlamadım, biraz daha açar mısın?';
    }

    // 6. Sanitize
    const userContext = [
      ...history.filter(m => m.role === 'user').slice(-5).map(m => m.content),
      currentMessage
    ].join(' \n ');

    const regenerateFn = async (violations) => {
      const feedback = `Önceki cevabın kuralları çiğnedi: ${violations.map(v => v.label).join(', ')}. Aynı içeriği bu kurallara UYARAK yeniden üret.`;
      const retry = await aiExpensive.generate({
        system: systemPrompt + '\n\n[KURAL HATIRLATMA]\n' + feedback,
        messages,
        tools: [],
        handleTool: null,
        maxTokens: 800
      });
      return retry.text || aiResponse;
    };

    const sanitized = await sanitize.run({
      response: aiResponse,
      toolCalled: toolEscalated,
      userContext,
      history,
      regenerateFn,
      logger: log
    });
    aiResponse = sanitized.response;
    if (sanitized.toolBypassed) toolEscalated = false;

    // 7. Profile sticky update
    if (profilePatch) {
      updateProfile(subscriberId, profilePatch).catch(() => {});
    }

    // 8. Eskalasyon mail (async, sonucu beklemiyoruz)
    if (toolEscalated && escalationCall) {
      const recentMessages = history.slice(-5).concat([{ role: 'user', content: currentMessage }, { role: 'assistant', content: aiResponse }]);
      sendEscalationEmail({
        type: escalationCall.type,
        subscriberId,
        igUsername: subscriberInfo.igUsername,
        reason: escalationCall.reason,
        recentMessages
      }).catch(err => log.error(`[ai_engine] escalation gönderim hatası: ${err.message}`));
    }

    return _wrap(aiResponse, {
      intent: routerResult.intent,
      modelUsed: 'sonnet',
      escalated: toolEscalated,
      sanitized: !!sanitized.fallback,
      fallback: sanitized.fallback,
      triggerProductCards: productCardsQueued,
      productCardsVariant: productCardsVariant
    }, options);
  } catch (err) {
    log.error(`[ai_engine] generateResponse hatası: ${err.message}`, err);
    return _wrap("Şu an küçük bir teknik aksaklık var, birazdan tekrar deneyebilir misin?", { intent: 'error', modelUsed: 'static' }, options);
  }
}

function _wrap(text, meta, options) {
  if (options && options.returnMeta) {
    return { text, ...meta };
  }
  return text;
}

module.exports = {
  generateResponse,
  buildSystemPrompt,
  REFUSE_TEMPLATE,
  TRIGGER_GUIDANCE_TEMPLATE
};
