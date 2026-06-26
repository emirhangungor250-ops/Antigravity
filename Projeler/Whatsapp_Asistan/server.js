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
const processingLock = new Map(); // subscriberId -> { queue: string[] }
const COALESCE_INITIAL_MS = parseInt(process.env.COALESCE_INITIAL_MS || '3000', 10);
const COALESCE_STRAGGLER_MS = parseInt(process.env.COALESCE_STRAGGLER_MS || '1500', 10);
const COALESCE_MAX_ITER = 4;

// KVKK Aydinlatma Mesaji
const KVKK_MESSAGE = `Merhaba! \ud83d\udc4b Ben [MARKA ADI]'nin yapay zek\u00e2 asistan\u0131y\u0131m.

Sana yard\u0131mc\u0131 olabilmem i\u00e7in ki\u015fisel verilerin hakk\u0131nda bilgilendirme yapmam gerekiyor.

KVKK Ayd\u0131nlatma Metni: ${process.env.KVKK_URL || '[KVKK_AYDINLATMA_URL]'}

Devam etmek i\u00e7in l\u00fctfen "Onayl\u0131yorum" yaz.`;

// Onboarding Butonları - Bu butonlara tıklandığında Asistan araya girmemeli (Exact Match)
const IGNORED_ONBOARDING_BUTTONS = new Set([
  "Bana mesaj gönderme",
  "Haydi başlayalım",
  "Skool App İndir",
  "[ÜRÜN BUTONU 1]",
  "[ÜRÜN BUTONU 2]",
  "[ÜRÜN BUTONU 3]",
  "Talebi Geri Al",
  "Android kullanıyorum",
  "iPhone kullanıyorum"
]);

// Hosgeldin Mesaji
const WELCOME_MESSAGE = `Te\u015fekk\u00fcrler! \ud83d\ude4f Art\u0131k sana [MARKA/ÜRÜN ADI] hakk\u0131nda her konuda yard\u0131mc\u0131 olabilirim. Sormak istedi\u011fin bir \u015fey var m\u0131?`;

app.post('/webhook/message', async (req, res) => {
  // Shared-secret guard — yapılandırılmışsa zorunlu
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

    // Idempotency: aynı subscriber+content kombosu son 60sn'de işlendiyse atla
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
      
      // Yeni kullaniciya dogrudan KVKK mesaji gonder
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
        await setCustomField(subscriberId, FIELD_ID, "Ozur dilerim, sesli mesajini su an dinleyemiyorum. Lutfen bana yazili olarak iletebilir misin?");
        await sendFlow(subscriberId, FLOW_ID);
        return;
      }
    }

    // Kullanici mesajini kaydet
    await saveMessage(subscriberId, 'user', messageContent);

    // 4. Burst coalesce — aktif işlem varsa kuyruğa düş, tek combined cevap üretilecek
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
      let outerIter = 0;

      while (outerIter < COALESCE_MAX_ITER) {
        // Burst penceresini topla: ilk debounce 3sn, sonra straggler 1.5sn
        let gatherIter = 0;
        while (gatherIter < COALESCE_MAX_ITER) {
          await new Promise(r => setTimeout(r, gatherIter === 0 ? COALESCE_INITIAL_MS : COALESCE_STRAGGLER_MS));
          if (lockEntry.queue.length === 0) break;
          pending = pending.concat(lockEntry.queue.splice(0));
          gatherIter++;
        }
        if (gatherIter >= COALESCE_MAX_ITER && lockEntry.queue.length > 0) {
          pending = pending.concat(lockEntry.queue.splice(0));
          log.warn(`[webhook] burst gather cap reached, AI yine de tetikleniyor`, { subscriberId, totalMsgs: pending.length });
        }

        // RAG için combined query, AI'a son user mesajı (kalanlar history'de zaten var)
        const ragQuery = pending.length === 1 ? pending[0] : pending.join(' ');
        const lastMessage = pending[pending.length - 1];
        if (pending.length > 1) {
          log.info(`[webhook] coalesced ${pending.length} mesaj`, { subscriberId });
        }

        const detectedLanguage = await detectLanguage(ragQuery);
        const aiResponse = await generateResponse(subscriberId, lastMessage, detectedLanguage, subscriberInfo, { ragQueryOverride: ragQuery });

        await saveMessage(subscriberId, 'assistant', aiResponse);
        await setCustomField(subscriberId, FIELD_ID, aiResponse);
        await sendFlow(subscriberId, FLOW_ID);

        // AI cevabı atılırken yeni mesaj gelmiş mi?
        if (lockEntry.queue.length === 0) break;
        pending = lockEntry.queue.splice(0);
        outerIter++;
        log.info(`[webhook] post-response straggler, yeni döngü`, { subscriberId, count: pending.length });
      }

      if (outerIter >= COALESCE_MAX_ITER) {
        log.warn(`[webhook] outer iter cap reached`, { subscriberId });
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

// KB durumu: hangi KB versiyonu Supabase'de aktif + kaç chunk + son seed tarihi
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

// Admin: RAG bilgi tabanini seed et
app.post('/admin/seed-knowledge', async (req, res) => {
  try {
    const fs = require('fs');
    const path = require('path');
    const OpenAI = require('openai');
    const { supabase } = require('./services/memory');
    const openai = new OpenAI({ apiKey: config.openaiApiKey });

    // Body'den markdown icerigi al, yoksa dosyadan oku
    let mdContent = req.body.markdown_content;
    if (!mdContent) {
      const mdPath = path.join(__dirname, 'bilgi-tabani.md');
      if (!fs.existsSync(mdPath)) {
        return res.status(404).json({ error: 'Bilgi tabani dosyasi bulunamadi. Body ile markdown_content gonderin.' });
      }
      mdContent = fs.readFileSync(mdPath, 'utf8');
    }
    
    // Markdown'i chunk'lara ayir
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

    // Eski verileri temizle
    await supabase.from('knowledge_chunks').delete().neq('id', '00000000-0000-0000-0000-000000000000');

    let processedCount = 0;
    for (const chunk of chunks) {
      if (!chunk.content || chunk.content.trim() === '') continue;

      const embeddingResponse = await openai.embeddings.create({
        model: 'text-embedding-3-small',
        input: `[${chunk.section_title}]\n${chunk.content}`,
        dimensions: 1536
      });

      const embedding = embeddingResponse.data[0].embedding;

      const { error } = await supabase.from('knowledge_chunks').insert({
        section: chunk.section,
        section_title: chunk.section_title,
        content: chunk.content,
        embedding: embedding,
        metadata: { source: 'bilgi-tabani' }
      });

      if (error) {
        log.error(`[seed] Kayit hatasi: ${chunk.section_title} - ${error.message}`);
      } else {
        processedCount++;
      }

      await new Promise(r => setTimeout(r, 200));
    }

    log.info(`[seed] ${processedCount} chunk kaydedildi.`);
    res.json({ status: 'ok', chunks_processed: processedCount, total_chunks: chunks.length });
  } catch (error) {
    log.error(`[seed] Seed hatasi: ${error.message}`, error);
    res.status(500).json({ error: error.message });
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

// KB fiyat doğrulama
app.get('/admin/kb/validate', async (req, res) => {
  if (!process.env.ADMIN_SECRET || req.headers['x-admin-key'] !== process.env.ADMIN_SECRET) {
    return res.status(403).json({ error: 'Unauthorized' });
  }
  try {
    const { supabase } = require('./services/memory');
    const { data, error } = await supabase
      .from('knowledge_chunks')
      .select('content');
      
    if (error) throw error;
    
    const combinedContent = data.map(d => d.content).join('\n');
    const bannedPrices = ['$97', '$197', '$297', '$497', '$997', '$1997'];
    const foundBanned = [];
    
    bannedPrices.forEach(price => {
      const regex = new RegExp(`\\${price}\\b`);
      if (regex.test(combinedContent)) {
        foundBanned.push(price);
      }
    });

    res.json({ 
      valid: foundBanned.length === 0,
      banned_prices_found: foundBanned
    });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// Tek chunk güncelleme
app.put('/admin/kb/update/:chunkId', async (req, res) => {
  if (!process.env.ADMIN_SECRET || req.headers['x-admin-key'] !== process.env.ADMIN_SECRET) {
    return res.status(403).json({ error: 'Unauthorized' });
  }
  const chunkId = req.params.chunkId;
  const { content } = req.body;
  if (!content) return res.status(400).json({ error: 'content gerekli' });
  
  try {
    const OpenAI = require('openai');
    const openai = new OpenAI({ apiKey: config.openaiApiKey });
    const { supabase } = require('./services/memory');
    
    const { data: chunkData, error: chunkErr } = await supabase
      .from('knowledge_chunks')
      .select('section_title')
      .eq('id', chunkId)
      .single();
      
    if (chunkErr || !chunkData) return res.status(404).json({ error: 'Chunk bulunamadı' });

    const embeddingResponse = await openai.embeddings.create({
      model: 'text-embedding-3-small',
      input: `[${chunkData.section_title}]\n${content}`,
      dimensions: 1536
    });

    const embedding = embeddingResponse.data[0].embedding;

    const { error: updateErr } = await supabase
      .from('knowledge_chunks')
      .update({ content, embedding })
      .eq('id', chunkId);

    if (updateErr) throw updateErr;

    res.json({ status: 'ok', message: 'Chunk başarıyla güncellendi' });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

app.listen(config.port, () => {
  log.info(`[server] Whatsapp_Asistan ${config.port} portunda calisiyor.`);
});
