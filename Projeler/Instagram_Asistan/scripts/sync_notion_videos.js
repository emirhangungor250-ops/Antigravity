// scripts/sync_notion_videos.js
// Notion video DB scan + chunking + embedding + ig_video_chunks upsert.
// Incremental sync: last_edited_time karşılaştırma ile değişmemiş page'ler atlanır.
// Usage:
//   node scripts/sync_notion_videos.js          # incremental
//   node scripts/sync_notion_videos.js --full   # tüm published'ı yeniden işle
const OpenAI = require('openai');
const { config } = require('../config/env');
const { supabase } = require('../services/memory');
const log = require('../utils/logger');
const notion = require('../services/notion_videos');

const openai = new OpenAI({ apiKey: config.openaiApiKey });

const FULL_MODE = process.argv.includes('--full');

async function embedBatch(texts) {
  const resp = await openai.embeddings.create({
    model: 'text-embedding-3-small',
    input: texts,
    dimensions: 1536
  });
  return resp.data.map(d => d.embedding);
}

async function existingMetaFor(pageId) {
  const { data, error } = await supabase
    .from('ig_video_chunks')
    .select('metadata')
    .eq('notion_page_id', pageId)
    .order('chunk_index', { ascending: true })
    .limit(1);
  if (error || !data || data.length === 0) return null;
  return data[0].metadata || {};
}

async function deleteChunks(pageId) {
  const { error } = await supabase
    .from('ig_video_chunks')
    .delete()
    .eq('notion_page_id', pageId);
  if (error) log.warn(`[sync] delete chunks hatası: ${error.message}`);
}

async function insertChunks(meta, scriptText, captionText) {
  // Strateji:
  //   chunk[0] = Caption özet (her zaman dahil — kullanıcıya araç adını verecek)
  //   chunk[1..N] = Page body script chunks
  const items = [];
  if (captionText && captionText.length > 30) {
    items.push(`[ÖZET]\n${captionText}`);
  }
  const bodyChunks = notion.chunkText(scriptText);
  items.push(...bodyChunks);

  if (items.length === 0) {
    log.warn(`[sync] içerik yok — atlanıyor: ${meta.video_title}`);
    return 0;
  }

  const embeddings = [];
  // OpenAI batch 8'erli (5xx riskini düşür)
  for (let i = 0; i < items.length; i += 8) {
    const batch = items.slice(i, i + 8);
    const emb = await embedBatch(batch);
    embeddings.push(...emb);
    await new Promise(r => setTimeout(r, 150));
  }

  const rows = items.map((content, idx) => ({
    notion_page_id: meta.notion_page_id,
    video_title: meta.video_title,
    video_url: meta.notion_url,
    drive_url: meta.drive_url || null,
    publish_date: meta.publish_date || null,
    trigger_keyword: null,
    content,
    chunk_index: idx,
    embedding: embeddings[idx],
    metadata: { last_edited: meta.last_edited_time, has_caption: !!captionText }
  }));

  const { error } = await supabase.from('ig_video_chunks').insert(rows);
  if (error) {
    log.error(`[sync] insert hatası: ${error.message}`);
    return 0;
  }
  return rows.length;
}

async function main() {
  log.info(`[sync] mode=${FULL_MODE ? 'FULL' : 'INCREMENTAL'}`);
  const pages = await notion.queryPublishedPages();

  let processed = 0, skipped = 0, failed = 0, chunksInserted = 0;

  for (const page of pages) {
    const meta = notion.pageMetadata(page);

    if (!FULL_MODE) {
      const existing = await existingMetaFor(meta.notion_page_id);
      if (existing?.last_edited === meta.last_edited_time) {
        skipped++;
        continue;
      }
    }

    try {
      const blocks = await notion.fetchPageBlocks(meta.notion_page_id);
      const scriptText = notion.extractScriptText(blocks);
      const hasContent = (scriptText && scriptText.length > 80) || (meta.caption && meta.caption.length > 80);
      if (!hasContent) {
        log.warn(`[sync] yetersiz içerik atlanıyor: ${meta.video_title}`);
        skipped++;
        continue;
      }

      await deleteChunks(meta.notion_page_id);
      const inserted = await insertChunks(meta, scriptText, meta.caption);
      chunksInserted += inserted;
      processed++;
      log.info(`[sync] OK ${meta.video_title} → ${inserted} chunk`);
      // rate-limit Notion (3 rps recommended)
      await new Promise(r => setTimeout(r, 350));
    } catch (err) {
      failed++;
      log.error(`[sync] FAIL ${meta.video_title}: ${err.message}`);
    }
  }

  log.info(`[sync] DONE total=${pages.length} processed=${processed} skipped=${skipped} failed=${failed} chunks=${chunksInserted}`);
}

if (require.main === module) {
  main().then(() => process.exit(0)).catch(err => {
    log.error(`[sync] fatal: ${err.message}`, err);
    process.exit(1);
  });
}

module.exports = { main };
