// server.js
const express = require('express');
const crypto = require('crypto');
const { config } = require('./config/env');
const log = require('./utils/logger');

// Webhook secret — bir kez warn at, runtime'da spam etme
let _webhookSecretWarned = false;
function verifyWebhookSecret(req) {
  if (!config.webhookSecret) {
    if (!_webhookSecretWarned) {
      log.warn('[webhook] WHATSAPP_WEBHOOK_SECRET tanımlı değil — istekler kimlik doğrulamasız kabul ediliyor.');
      _webhookSecretWarned = true;
    }
    return true;
  }
  const provided = req.headers['x-webhook-secret'];
  if (typeof provided !== 'string' || provided.length === 0) return false;
  const a = Buffer.from(provided);
  const b = Buffer.from(config.webhookSecret);
  if (a.length !== b.length) return false;
  try {
    return crypto.timingSafeEqual(a, b);
  } catch (_) {
    return false;
  }
}

// ManyChat field ve flow ID'leri
const FIELD_ID = config.manychatFieldId;
const FLOW_ID = config.manychatFlowId;

// Servisler
const { getSubscriber, createSubscriber, acceptKVKK, saveMessage, wasRecentlyProcessed } = require('./services/memory');
const { isAudioUrl, transcribeAudio } = require('./services/transcription');
const { detectLanguage } = require('./services/language_detector');
const { generateResponse } = require('./services/ai_engine');
const { setCustomField, sendFlow } = require('./services/manychat');
const { checkKVKKIntent } = require('./services/intent_classifier');

const app = express();
app.use(express.json({ limit: '5mb' }));

// Per-subscriber processing lock — kullanıcı kısa aralıkla birden fazla mesaj attığında
// bot her birine ayrı cevap üretmesin. Aynı subscriber için aktif işlem varsa yeni gelen
// mesaj kuyruğa düşer ve mevcut işleme dahil edilir, tek combined cevap döner.
const processingLock = new Map();
const COALESCE_INITIAL_MS = parseInt(process.env.COALESCE_INITIAL_MS || '3000', 10);
const COALESCE_STRAGGLER_MS = parseInt(process.env.COALESCE_STRAGGLER_MS || '1500', 10);
const COALESCE_MAX_ITER = 4;

// İşletme adı — prompt ve mesajlarda kullanılır
const BUSINESS_NAME = process.env.BUSINESS_NAME || 'İşletme';

// KVKK Aydinlatma Mesaji — env'den override edilebilir
const KVKK_URL = process.env.KVKK_URL || 'https://<ISLETME_WEBSITE>/kvkk';
const KVKK_MESSAGE = process.env.KVKK_MESSAGE || `Merhaba! Ben ${BUSINESS_NAME}'nin yapay zeka asistanıyım.

Size yardımcı olabilmem için kişisel verileriniz hakkında bilgilendirme yapmam gerekiyor.

KVKK Aydınlatma Metni: ${KVKK_URL}

Devam etmek için lütfen "Onaylıyorum" yazın.`;

// Onboarding Butonları — bot bunlara cevap üretmesin (Exact Match)
const IGNORED_ONBOARDING_BUTTONS = new Set([
  "Bana mesaj gönderme",
  "Haydi başlayalım"
]);

// Hosgeldin Mesaji
const WELCOME_MESSAGE = process.env.WELCOME_MESSAGE || `Teşekkürler! Artık ${BUSINESS_NAME} hakkında size yardımcı olabilirim. Size nasıl yardımcı olabilirim?`;

app.post('/webhook/message', async (req, res) => {
  if (!verifyWebhookSecret(req)) {
    log.warn('[webhook] Geçersiz veya eksik x-webhook-secret — istek reddedildi.');
    return res.status(401).send({ error: 'unauthorized' });
  }

  // ManyChat webhook timeoutlari icin hemen 200 donulur
  res.status(200).send({ status: 'received' });

  try {
    const payload = req.body;
    const subscriberId = payload.kullanici_id;
    let messageContent = payload.last_text_input;
    const phoneNumber = payload.phone_number || '';

    if (!subscriberId || !messageContent) {
      log.warn(`[webhook] Eksik payload verisi.`, { subscriberId, messageContent: !!messageContent });
      return;
    }

    if (IGNORED_ONBOARDING_BUTTONS.has(messageContent.trim())) {
      log.info(`[webhook] Onboarding butonu atlandi (Asistan islem yapmiyor).`, { subscriberId, messageContent });
      return;
    }

    if (await wasRecentlyProcessed(subscriberId, messageContent, 60)) {
      log.info(`[webhook] duplicate_webhook_ignored`, { event: 'duplicate_webhook_ignored', subscriberId });
      return;
    }

    log.info(`[webhook] Yeni mesaj alindi.`, { subscriberId });

    // 1. Subscriber kontrolu
    let subscriber = await getSubscriber(subscriberId);
    if (!subscriber) {
      log.info(`[webhook] Yeni subscriber olusturuluyor...`, { subscriberId });
      subscriber = await createSubscriber(subscriberId, phoneNumber);

      await setCustomField(subscriberId, FIELD_ID, KVKK_MESSAGE);
      await sendFlow(subscriberId, FLOW_ID);
      return;
    }

    // 2. KVKK kontrolu
    if (!subscriber.kvkk_accepted) {
      const isAccepted = await checkKVKKIntent(messageContent);

      if (isAccepted) {
        log.info(`[webhook] Kullanici KVKK onayladi.`, { subscriberId });
        await acceptKVKK(subscriberId);

        await setCustomField(subscriberId, FIELD_ID, WELCOME_MESSAGE);
        await sendFlow(subscriberId, FLOW_ID);
      } else {
        log.info(`[webhook] Kullanici henuz KVKK onaylamadi, hatirlatma gonderiliyor.`, { subscriberId });
        await setCustomField(subscriberId, FIELD_ID, KVKK_MESSAGE);
        await sendFlow(subscriberId, FLOW_ID);
      }
      return;
    }

    // 3. Ses mesaji kontrolu ve transkripsiyon
    if (isAudioUrl(messageContent)) {
      log.info(`[webhook] Ses mesaji algilandi, transkribe ediliyor...`, { subscriberId });
      try {
        messageContent = await transcribeAudio(messageContent);
      } catch (err) {
        log.error(`[webhook] Ses mesaji cevrilemedi, kullaniciya bilgi veriliyor.`, err);
        await setCustomField(subscriberId, FIELD_ID, "Özür dilerim, sesli mesajınızı şu an dinleyemiyorum. Lütfen yazılı olarak iletebilir misiniz?");
        await sendFlow(subscriberId, FLOW_ID);
        return;
      }
    }

    await saveMessage(subscriberId, 'user', messageContent);

    // 4. Burst coalesce
    const existingLock = processingLock.get(subscriberId);
    if (existingLock) {
      existingLock.queue.push(messageContent);
      log.info(`[webhook] burst — kuyruğa eklendi`, { subscriberId, queueLen: existingLock.queue.length });
      return;
    }

    const lockEntry = { queue: [] };
    processingLock.set(subscriberId, lockEntry);

    try {
      let pending = [messageContent];
      const subscriberInfo = { subscriberId, phoneNumber };

      for (let iter = 0; iter < COALESCE_MAX_ITER; iter++) {
        await new Promise(r => setTimeout(r, iter === 0 ? COALESCE_INITIAL_MS : COALESCE_STRAGGLER_MS));

        if (lockEntry.queue.length > 0) {
          pending = pending.concat(lockEntry.queue.splice(0));
          continue;
        }

        const combinedMessage = pending.length === 1 ? pending[0] : pending.join('\n');
        if (pending.length > 1) {
          log.info(`[webhook] coalesced ${pending.length} mesaj`, { subscriberId });
        }

        const detectedLanguage = await detectLanguage(combinedMessage);
        const aiResponse = await generateResponse(subscriberId, combinedMessage, detectedLanguage, subscriberInfo);

        await saveMessage(subscriberId, 'assistant', aiResponse);
        await setCustomField(subscriberId, FIELD_ID, aiResponse);
        await sendFlow(subscriberId, FLOW_ID);

        if (lockEntry.queue.length === 0) {
          pending = [];
          break;
        }
        pending = lockEntry.queue.splice(0);
        log.info(`[webhook] post-response straggler, yeni döngü`, { subscriberId, count: pending.length });
      }

      log.info(`[webhook] Islem basariyla tamamlandi.`, { subscriberId });
    } finally {
      processingLock.delete(subscriberId);
    }

  } catch (error) {
    log.error(`[webhook] Beklenmeyen hata: ${error.message}`, error);
  }
});

app.get('/health', (req, res) => {
  res.status(200).json({ status: 'ok', timestamp: new Date().toISOString() });
});

// KB durumu
app.get('/admin/kb-status', async (req, res) => {
  if (!process.env.ADMIN_SECRET || req.headers['x-admin-key'] !== process.env.ADMIN_SECRET) {
    return res.status(403).json({ error: 'Unauthorized' });
  }
  try {
    const { supabase } = require('./services/memory');
    const { count, error: countErr } = await supabase
      .from('knowledge_chunks')
      .select('id', { count: 'exact', head: true });
    if (countErr) throw countErr;

    const { data: sample, error: sampleErr } = await supabase
      .from('knowledge_chunks')
      .select('metadata, created_at')
      .order('created_at', { ascending: false })
      .limit(1);
    if (sampleErr) throw sampleErr;

    const meta = sample && sample[0] ? sample[0].metadata || {} : {};
    res.json({
      source: meta.source || 'unknown',
      chunks: count || 0,
      last_seed: meta.seeded_at || (sample && sample[0] ? sample[0].created_at : null)
    });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// KB chunk listesi
app.get('/admin/kb/list', async (req, res) => {
  if (!process.env.ADMIN_SECRET || req.headers['x-admin-key'] !== process.env.ADMIN_SECRET) {
    return res.status(403).json({ error: 'Unauthorized' });
  }
  try {
    const { supabase } = require('./services/memory');
    const { data, error } = await supabase
      .from('knowledge_chunks')
      .select('id, section, section_title, content, created_at')
      .order('section');

    if (error) throw error;

    const formattedData = data.map(chunk => ({
      id: chunk.id,
      section: chunk.section,
      section_title: chunk.section_title,
      length: chunk.content ? chunk.content.length : 0,
      created_at: chunk.created_at
    }));

    res.json({ chunks: formattedData });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// KB chunk arama
app.get('/admin/kb/search', async (req, res) => {
  if (!process.env.ADMIN_SECRET || req.headers['x-admin-key'] !== process.env.ADMIN_SECRET) {
    return res.status(403).json({ error: 'Unauthorized' });
  }
  const query = req.query.q;
  if (!query) return res.status(400).json({ error: 'q parametresi gerekli' });

  try {
    const { supabase } = require('./services/memory');
    const { data, error } = await supabase
      .from('knowledge_chunks')
      .select('id, section, section_title, content')
      .ilike('content', `%${query}%`);

    if (error) throw error;
    res.json({ results: data });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

app.listen(config.port, () => {
  log.info(`[server] ${BUSINESS_NAME} WhatsApp Asistan ${config.port} portunda calisiyor.`);
});
