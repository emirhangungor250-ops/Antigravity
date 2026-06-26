// services/kb_factory.js
// RAG-A — Marka KB (knowledge_chunks tablosu, source filtreli).
// Pinning stratejisi Whatsapp_Asistan knowledge_base.js'ten port.
// SOURCE değerini kendi KB source adınızla değiştirin.
const OpenAI = require('openai');
const { config } = require('../config/env');
const { supabase } = require('./memory');
const log = require('../utils/logger');

const openai = new OpenAI({ apiKey: config.openaiApiKey });

// Kategori-bazlı pinning anahtar kelimeleri — kendi ürün/hizmet alanınıza göre uyarlayın.
const PRICING_KEYWORDS = ['fiyat', 'ücret', 'price', 'ne kadar', 'paket', 'aylık', 'yıllık', 'indirim'];
const AUTOMATION_KEYWORDS = ['otomasyon', 'automation', 'youtube', 'e-ticaret', 'influencer', 'içerik üret', 'shorts', 'reels'];
const LINK_KEYWORDS = [
  'link', 'ödeme', 'üyelik', 'eğitim', 'nereden başla',
  'kayıt', 'üye ol', 'görüş', 'iletişim', 'destek', 'yardım'
];
const MEMBER_TECH_KEYWORDS = ['kayıt oldum', 'üye oldum', 'paket aldım', 'göremiyorum', 'hata veriyor', 'çalışmıyor'];

const SOURCE = 'main';

async function pinSection(sectionLike) {
  const { data } = await supabase
    .from('knowledge_chunks')
    .select('section, section_title, content, source')
    .like('section', sectionLike)
    .eq('source', SOURCE)
    .order('section', { ascending: true });
  return data || [];
}

function formatChunks(chunks) {
  return (chunks || []).map(c => `[${c.section_title}]\n${c.content}`).join('\n\n');
}

async function embedQuery(question) {
  const resp = await openai.embeddings.create({
    model: 'text-embedding-3-small',
    input: question,
    dimensions: 1536
  });
  return resp.data[0].embedding;
}

async function semanticSearch(embedding, threshold = 0.35, count = 8) {
  const { data, error } = await supabase.rpc('match_knowledge_chunks_filtered', {
    query_embedding: embedding,
    source_filter: SOURCE,
    match_threshold: threshold,
    match_count: count
  });
  if (error) {
    log.error(`[kb_factory] semantic search hatası: ${error.message}`);
    return [];
  }
  return data || [];
}

async function query(question, opts = {}) {
  try {
    const embedding = await embedQuery(question);
    const semantic = await semanticSearch(embedding, opts.threshold, opts.count);
    const contextText = semantic.length > 0
      ? semantic.map(c => `[${c.section_title}]\n${c.content}`).join('\n\n')
      : '';

    const roleChunks = await pinSection('0.%');
    const rolePinned = formatChunks(roleChunks);

    const lower = question.toLowerCase();

    if (PRICING_KEYWORDS.some(kw => lower.includes(kw))) {
      const pricingChunks = await pinSection('2.%');
      log.info(`[kb_factory] pricing_pin: ${pricingChunks.length}`);
      return [rolePinned, formatChunks(pricingChunks), contextText].filter(Boolean).join('\n\n');
    }
    if (AUTOMATION_KEYWORDS.some(kw => lower.includes(kw))) {
      const a = await pinSection('3.%');
      const b = await pinSection('3.5.%');
      const c = await pinSection('4.%');
      const seen = new Set();
      const dedup = [...a, ...b, ...c].filter(ch => {
        const k = ch.section + ch.section_title;
        if (seen.has(k)) return false;
        seen.add(k);
        return true;
      });
      log.info(`[kb_factory] automation_pin: ${dedup.length}`);
      return [rolePinned, formatChunks(dedup), contextText].filter(Boolean).join('\n\n');
    }
    if (MEMBER_TECH_KEYWORDS.some(kw => lower.includes(kw))) {
      const a = await pinSection('13.%');
      const b = await pinSection('5.%');
      log.info(`[kb_factory] member_tech_pin: ${a.length + b.length}`);
      return [rolePinned, formatChunks([...a, ...b]), contextText].filter(Boolean).join('\n\n');
    }
    if (LINK_KEYWORDS.some(kw => lower.includes(kw))) {
      const a = await pinSection('10.%');
      const b = await pinSection('13.%');
      const c = await pinSection('16.%');
      const d = await pinSection('17.2%');
      log.info(`[kb_factory] link_pin: ${a.length + b.length + c.length + d.length}`);
      return [rolePinned, formatChunks([...a, ...b, ...c, ...d]), contextText].filter(Boolean).join('\n\n');
    }

    return [rolePinned, contextText].filter(Boolean).join('\n\n');
  } catch (err) {
    log.error(`[kb_factory] query hatası: ${err.message}`, err);
    return '';
  }
}

async function countChunks() {
  const { count, error } = await supabase
    .from('knowledge_chunks')
    .select('id', { count: 'exact', head: true })
    .eq('source', SOURCE);
  if (error) return -1;
  return count || 0;
}

module.exports = { query, countChunks, SOURCE };
