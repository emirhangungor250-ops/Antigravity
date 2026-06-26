// services/kb_videos.js
// RAG-B — Notion video transcript chunks (ig_video_chunks tablosu).
const OpenAI = require('openai');
const { config } = require('../config/env');
const { supabase } = require('./memory');
const log = require('../utils/logger');

const openai = new OpenAI({ apiKey: config.openaiApiKey });

async function embedQuery(question) {
  const resp = await openai.embeddings.create({
    model: 'text-embedding-3-small',
    input: question,
    dimensions: 1536
  });
  return resp.data[0].embedding;
}

async function query(question, opts = {}) {
  try {
    const embedding = await embedQuery(question);
    const { data, error } = await supabase.rpc('match_video_chunks', {
      query_embedding: embedding,
      match_threshold: opts.threshold ?? 0.32,
      match_count: opts.count ?? 6
    });
    if (error) {
      log.error(`[kb_videos] match hatası: ${error.message}`);
      return { chunks: [], formatted: '' };
    }
    const chunks = data || [];
    if (chunks.length === 0) return { chunks: [], formatted: '' };

    // Aynı video page'inden gelen birden fazla chunk'ı grupla
    const grouped = new Map();
    for (const c of chunks) {
      const arr = grouped.get(c.notion_page_id) || [];
      arr.push(c);
      grouped.set(c.notion_page_id, arr);
    }
    const formatted = Array.from(grouped.entries()).map(([pageId, list]) => {
      const head = list[0];
      const body = list.map(c => c.content).join('\n');
      const urlLine = head.drive_url || head.video_url ? `Link: ${head.video_url || head.drive_url}` : '';
      return `[${head.video_title || 'Video'}]\n${body}\n${urlLine}`.trim();
    }).join('\n\n');

    log.info(`[kb_videos] ${chunks.length} chunk, ${grouped.size} video`);
    return { chunks, formatted, grouped };
  } catch (err) {
    log.error(`[kb_videos] query hatası: ${err.message}`, err);
    return { chunks: [], formatted: '' };
  }
}

async function lookupByKeyword(keyword) {
  try {
    const { data, error } = await supabase
      .from('ig_video_chunks')
      .select('notion_page_id, video_title, video_url, drive_url, content, chunk_index')
      .eq('trigger_keyword', keyword)
      .order('chunk_index', { ascending: true });
    if (error) throw error;
    return data || [];
  } catch (err) {
    log.error(`[kb_videos] lookupByKeyword hatası: ${err.message}`, err);
    return [];
  }
}

async function countChunks() {
  const { count, error } = await supabase
    .from('ig_video_chunks')
    .select('id', { count: 'exact', head: true });
  if (error) return -1;
  return count || 0;
}

module.exports = { query, lookupByKeyword, countChunks };
