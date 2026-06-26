// server.js — Instagram DM Asistanı
const express = require('express');
const crypto = require('crypto');
const { config } = require('./config/env');
const log = require('./utils/logger');

const FIELD_ID = config.manychatFieldId;
const FLOW_ID = config.manychatFlowId;

const { getSubscriber, createSubscriber, saveMessage, wasRecentlyProcessed, updateProfile } = require('./services/memory');
const { generateResponse } = require('./services/ai_engine');
const { setCustomField, sendFlow, sendProductCards } = require('./services/manychat');
const rateLimiter = require('./services/rate_limiter');
const kbFactory = require('./services/kb_factory');
const kbVideos = require('./services/kb_videos');
const { transcribeAudio, isAudioUrl, isImageUrl } = require('./services/transcription');
const { describeImage } = require('./services/vision');

let _webhookSecretWarned = false;
function verifyWebhookSecret(req) {
  if (!config.webhookSecret) {
    if (!_webhookSecretWarned) {
      log.warn('[webhook] INSTAGRAM_WEBHOOK_SECRET tanımlı değil — istekler kimlik doğrulamasız kabul ediliyor.');
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

function requireAdminSecret(req, res) {
  if (!config.adminSecret || req.headers['x-admin-key'] !== config.adminSecret) {
    res.status(403).json({ error: 'Unauthorized' });
    return false;
  }
  return true;
}

const app = express();
app.use(express.json({ limit: '5mb' }));

// ============================================================================
// F2 — Burst coalesce lock
// ============================================================================
const processingLock = new Map();
const COALESCE_INITIAL_MS = config.coalesceInitialMs;
const COALESCE_STRAGGLER_MS = config.coalesceStragglerMs;
const COALESCE_MAX_ITER = config.coalesceMaxIter;

// ============================================================================
// Webhook — ManyChat external_request hedefi
// ============================================================================
app.post('/webhook/instagram', async (req, res) => {
  if (!verifyWebhookSecret(req)) {
    log.warn('[webhook] Geçersiz x-webhook-secret');
    return res.status(401).send({ error: 'unauthorized' });
  }

  // ManyChat timeout için hemen 200
  res.status(200).send({ status: 'received' });

  try {
    const payload = req.body || {};
    const subscriberId = payload.kullanici_id || payload.subscriber_id;
    let messageContent = payload.last_text_input;
    const igUsername = payload.username || payload.ig_username || payload.ig_user_handle || null;
    const firstName = payload.first_name || null;

    if (!subscriberId || !messageContent) {
      log.warn('[webhook] eksik payload', { hasSub: !!subscriberId, hasMsg: !!messageContent });
      return;
    }

    // Media handling — ses ise transkribe et, görsel ise describe et
    let mediaContext = null;
    if (isAudioUrl(messageContent)) {
      log.info('[webhook] ses mesajı algılandı, transkribe ediliyor', { subscriberId });
      try {
        const transcribed = await transcribeAudio(messageContent);
        if (transcribed && transcribed.length > 1) {
          messageContent = transcribed;
        } else {
          messageContent = '[sesli mesaj transkribe edilemedi]';
        }
      } catch (err) {
        log.error(`[webhook] ses transkripti başarısız: ${err.message}`);
        await setCustomField(subscriberId, FIELD_ID, 'Sesli mesajını şu an çeviremedim. Lütfen yazılı olarak iletebilir misin?');
        await sendFlow(subscriberId, FLOW_ID);
        return;
      }
    } else if (isImageUrl(messageContent)) {
      log.info('[webhook] görsel algılandı, analiz ediliyor', { subscriberId });
      try {
        const description = await describeImage(messageContent, '');
        mediaContext = description ? `(Kullanıcı bir görsel attı. Görsel özeti: ${description})` : null;
        // Görselin yerine description + sahte kullanıcı mesajı: "şu görseli paylaştım" tarzı
        messageContent = mediaContext
          ? `[Kullanıcı bir görsel attı.]\n${description}`
          : '[Kullanıcı bir görsel attı ama açıklayamadım.]';
      } catch (err) {
        log.error(`[webhook] görsel analizi başarısız: ${err.message}`);
        messageContent = '[Kullanıcı bir görsel attı, içeriğini analiz edemedim.]';
      }
    }

    // Idempotency
    if (await wasRecentlyProcessed(subscriberId, messageContent, 60)) {
      log.info('[webhook] duplicate_webhook_ignored', { subscriberId });
      return;
    }

    // 1. Subscriber kontrolü (KVKK akışı YOK — IG'de ManyChat policy halleder)
    let subscriber = await getSubscriber(subscriberId);
    if (!subscriber) {
      subscriber = await createSubscriber(subscriberId, igUsername);
      log.info('[webhook] yeni subscriber', { subscriberId });
    }

    // 2. F1 — Rate limit (burst lock'tan önce)
    const rate = await rateLimiter.checkAndConsume(subscriberId);
    if (!rate.allowed) {
      log.info('[webhook] rate_limited', { subscriberId, count: rate.count, max: rate.max });
      await saveMessage(subscriberId, 'user', messageContent, { intent: 'rate_limited' });
      await saveMessage(subscriberId, 'assistant', rateLimiter.RATE_LIMIT_MSG, { intent: 'rate_limited', modelUsed: 'static' });
      await setCustomField(subscriberId, FIELD_ID, rateLimiter.RATE_LIMIT_MSG);
      await sendFlow(subscriberId, FLOW_ID);
      return;
    }

    await saveMessage(subscriberId, 'user', messageContent);

    // 3. F2 — Burst coalesce
    const existingLock = processingLock.get(subscriberId);
    if (existingLock) {
      existingLock.queue.push(messageContent);
      log.info('[webhook] burst — kuyruğa eklendi', { subscriberId, queueLen: existingLock.queue.length });
      return;
    }

    const lockEntry = { queue: [] };
    processingLock.set(subscriberId, lockEntry);

    try {
      let pending = [messageContent];
      const subscriberInfo = { subscriberId, igUsername, firstName };
      let outerIter = 0;

      while (outerIter < COALESCE_MAX_ITER) {
        let gatherIter = 0;
        while (gatherIter < COALESCE_MAX_ITER) {
          await new Promise(r => setTimeout(r, gatherIter === 0 ? COALESCE_INITIAL_MS : COALESCE_STRAGGLER_MS));
          if (lockEntry.queue.length === 0) break;
          pending = pending.concat(lockEntry.queue.splice(0));
          gatherIter++;
        }
        if (gatherIter >= COALESCE_MAX_ITER && lockEntry.queue.length > 0) {
          pending = pending.concat(lockEntry.queue.splice(0));
        }

        const ragQuery = pending.length === 1 ? pending[0] : pending.join(' ');
        const lastMessage = pending[pending.length - 1];
        if (pending.length > 1) log.info('[webhook] coalesced', { subscriberId, total: pending.length });

        const aiResult = await generateResponse(subscriberId, lastMessage, 'tr', subscriberInfo, {
          ragQueryOverride: ragQuery,
          returnMeta: true
        });

        const aiText = typeof aiResult === 'string' ? aiResult : aiResult.text;
        const meta = typeof aiResult === 'object' ? aiResult : {};

        await saveMessage(subscriberId, 'assistant', aiText, {
          intent: meta.intent,
          modelUsed: meta.modelUsed
        });
        await setCustomField(subscriberId, FIELD_ID, aiText);
        await sendFlow(subscriberId, FLOW_ID);

        // Product Card flow tetiklendiyse, metin flow'undan sonra hemen kartları gönder
        if (meta.triggerProductCards) {
          const variant = meta.productCardsVariant || 'otomasyonlar';
          log.info('[webhook] Product Card flow tetikleniyor', { subscriberId, variant });
          await sendProductCards(subscriberId, variant);
        }

        if (lockEntry.queue.length === 0) break;
        pending = lockEntry.queue.splice(0);
        outerIter++;
        log.info('[webhook] post-response straggler', { subscriberId, count: pending.length });
      }

      if (outerIter >= COALESCE_MAX_ITER) {
        log.warn('[webhook] outer_iter_cap', { subscriberId });
      }
    } finally {
      processingLock.delete(subscriberId);
    }
  } catch (err) {
    log.error(`[webhook] ${err.message}`, err);
  }
});

// ============================================================================
// Admin
// ============================================================================
app.get('/health', (req, res) => {
  res.status(200).json({ status: 'ok', service: 'instagram-asistan', timestamp: new Date().toISOString() });
});

app.get('/admin/kb-status', async (req, res) => {
  if (!requireAdminSecret(req, res)) return;
  try {
    const [factory, videos] = await Promise.all([kbFactory.countChunks(), kbVideos.countChunks()]);
    res.json({
      rag_a_factory_chunks: factory,
      rag_b_video_chunks: videos
    });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

app.get('/admin/rate-status', async (req, res) => {
  if (!requireAdminSecret(req, res)) return;
  const subscriberId = req.query.subscriber_id;
  if (!subscriberId) return res.status(400).json({ error: 'subscriber_id gerekli' });
  const count = await rateLimiter.currentCount(subscriberId);
  res.json({ subscriber_id: subscriberId, count, max: config.rateLimitMax, window_h: config.rateLimitWindowH });
});

app.post('/admin/reset-rate', async (req, res) => {
  if (!requireAdminSecret(req, res)) return;
  const subscriberId = req.query.subscriber_id;
  if (!subscriberId) return res.status(400).json({ error: 'subscriber_id gerekli' });
  await rateLimiter.resetSubscriber(subscriberId);
  res.json({ status: 'ok', subscriber_id: subscriberId });
});

// RAG-A seed — Whatsapp_Asistan main-asistan-bilgi-tabani-v7.md'yi source='main' ile yükler
app.post('/admin/seed-kb-factory', async (req, res) => {
  if (!requireAdminSecret(req, res)) return;
  try {
    const fs = require('fs');
    const path = require('path');
    const OpenAI = require('openai');
    const { supabase } = require('./services/memory');
    const openai = new OpenAI({ apiKey: config.openaiApiKey });

    let mdContent = req.body?.markdown_content;
    if (!mdContent) {
      // Lokal/Railway için olası path'leri dene
      const candidates = [
        path.join(__dirname, 'data', 'main-asistan-bilgi-tabani-v7.md'),
        path.join(__dirname, '..', 'Whatsapp_Asistan', 'main-asistan-bilgi-tabani-v7.md')
      ];
      for (const p of candidates) {
        if (fs.existsSync(p)) { mdContent = fs.readFileSync(p, 'utf8'); break; }
      }
    }
    if (!mdContent) {
      return res.status(404).json({ error: 'KB dosyası bulunamadı. Body ile markdown_content gönder.' });
    }

    const chunks = [];
    const lines = mdContent.split('\n');
    let currentSection = '', currentTitle = '', currentContent = [];
    for (const line of lines) {
      if (line.startsWith('## ') || line.startsWith('### ')) {
        if (currentContent.length > 0 && currentTitle) {
          chunks.push({ section: currentSection || '0', section_title: currentTitle, content: currentContent.join('\n').trim() });
          currentContent = [];
        }
        const titleText = line.replace(/^#+\s/, '');
        const sectionMatch = titleText.match(/^([\d.]+)\s*/);
        if (sectionMatch) {
          currentSection = sectionMatch[1].trim();
          currentTitle = titleText.substring(sectionMatch[0].length).trim();
        } else {
          currentTitle = titleText;
        }
      } else {
        currentContent.push(line);
      }
    }
    if (currentContent.length > 0 && currentTitle) {
      chunks.push({ section: currentSection || '0', section_title: currentTitle, content: currentContent.join('\n').trim() });
    }

    // Eski source='main' kayıtlarını temizle
    await supabase.from('knowledge_chunks').delete().eq('source', 'main');

    let processed = 0;
    for (const chunk of chunks) {
      if (!chunk.content || chunk.content.trim() === '') continue;
      const e = await openai.embeddings.create({
        model: 'text-embedding-3-small',
        input: `[${chunk.section_title}]\n${chunk.content}`,
        dimensions: 1536
      });
      const { error } = await supabase.from('knowledge_chunks').insert({
        section: chunk.section,
        section_title: chunk.section_title,
        content: chunk.content,
        embedding: e.data[0].embedding,
        metadata: { seeded_at: new Date().toISOString() },
        source: 'main'
      });
      if (!error) processed++;
      await new Promise(r => setTimeout(r, 150));
    }

    log.info(`[seed] ${processed} chunk yüklendi`);
    res.json({ status: 'ok', chunks_processed: processed, total: chunks.length });
  } catch (err) {
    log.error(`[seed] hata: ${err.message}`, err);
    res.status(500).json({ error: err.message });
  }
});

// RAG-B sync — Notion video DB
app.post('/admin/sync-notion-videos', async (req, res) => {
  if (!requireAdminSecret(req, res)) return;
  // Fire-and-forget — uzun süren işlem; response hemen dön
  const fullMode = !!req.body?.full;
  res.json({ status: 'started', full: fullMode });
  try {
    if (fullMode) process.argv.push('--full');
    const sync = require('./scripts/sync_notion_videos');
    await sync.main();
  } catch (err) {
    log.error(`[sync] async error: ${err.message}`, err);
  }
});

app.listen(config.port, () => {
  log.info(`[server] IG_Asistan ${config.port} portunda çalışıyor.`);
});
