// services/knowledge_base.js
const OpenAI = require('openai');
const { config } = require('../config/env');
const { supabase } = require('./memory');
const log = require('../utils/logger');

const openai = new OpenAI({ apiKey: config.openaiApiKey });

// Keyword pin'leri — KENDİ sektörünüze göre uyarlayın. Aşağıdaki listeler bir villa
// kiralama işletmesi için örnektir; kendi ürün/hizmet terimlerinizle değiştirin.
// Section numaralandırma: 0=Rol/Akış, 1=Şirket, 2=Bölge/Kategori, 3=Ürün Kategorileri,
// 4=Politikalar (ödeme/iptal), 5=SSS, 6=İletişim, 7=Operasyonel (ek hizmet)
const PRICING_KEYWORDS = ['fiyat', 'ücret', 'price', 'cost', 'ne kadar', 'kaç tl', 'kaç euro', 'kaç dolar', 'gece', 'gecelik', 'haftalık', 'aylık'];
const POLICY_KEYWORDS = ['ödeme', 'odeme', 'iptal', 'iade', 'kapora', 'depozito', 'taksit', 'kredi kartı', 'iade politikası', 'indirim', 'erken rezervasyon'];
const VILLA_KEYWORDS = ['villa', 'havuz', 'pool', 'deniz manzaralı', 'infinity', 'balayı', 'aile', 'evcil', 'pet', 'lüks', 'müstakil', 'jakuzi', 'sauna', 'oda', 'yatak'];
const REGION_KEYWORDS = ['kaş', 'kas', 'kalkan', 'fethiye', 'antalya', 'bölge', 'lokasyon', 'plaj', 'transfer', 'havaalanı', 'havalimanı'];

async function pinSection(sectionLike) {
  const { data } = await supabase
    .from('knowledge_chunks')
    .select('section, section_title, content')
    .like('section', sectionLike)
    .order('section', { ascending: true });
  return data || [];
}

function formatChunks(chunks) {
  return chunks.map(c => `[${c.section_title}]\n${c.content}`).join('\n\n');
}

async function queryKnowledge(question) {
  try {
    log.debug(`[knowledge_base] Soru embed ediliyor...`);
    const embeddingResponse = await openai.embeddings.create({
      model: 'text-embedding-3-small',
      input: question,
      dimensions: 1536
    });

    const embedding = embeddingResponse.data[0].embedding;

    log.debug(`[knowledge_base] Supabase similarity search yapılıyor...`);
    const { data, error } = await supabase.rpc('match_knowledge_chunks', {
      query_embedding: embedding,
      match_threshold: 0.35,
      match_count: 8
    });

    if (error) throw error;

    let contextText = "";
    if (!data || data.length === 0) {
      log.warn(`[knowledge_base] İlgili chunk bulunamadı (semantic).`);
    } else {
      log.info(`[knowledge_base] ${data.length} adet chunk bulundu (semantic).`);
      contextText = data.map(chunk => `[${chunk.section_title}]\n${chunk.content}`).join('\n\n');
    }

    // ROLE & FLOW: her sorguda Bölüm 0 chunk'larını başa pinle
    const roleChunks = await pinSection('0.%');
    const rolePinned = formatChunks(roleChunks);

    const lowerQuestion = question.toLowerCase();

    if (PRICING_KEYWORDS.some(kw => lowerQuestion.includes(kw))) {
      const a = await pinSection('3.%');
      const b = await pinSection('4.%');
      const all = [...a, ...b];
      const pinned = formatChunks(all);
      log.info(`[knowledge_base] pricing_pin: ${all.length} chunk`);
      return [rolePinned, pinned, contextText].filter(Boolean).join('\n\n');
    }

    if (POLICY_KEYWORDS.some(kw => lowerQuestion.includes(kw))) {
      const policyChunks = await pinSection('4.%');
      const pinned = formatChunks(policyChunks);
      log.info(`[knowledge_base] policy_pin: ${policyChunks.length} chunk`);
      return [rolePinned, pinned, contextText].filter(Boolean).join('\n\n');
    }

    if (VILLA_KEYWORDS.some(kw => lowerQuestion.includes(kw))) {
      const villaChunks = await pinSection('3.%');
      const pinned = formatChunks(villaChunks);
      log.info(`[knowledge_base] villa_pin: ${villaChunks.length} chunk`);
      return [rolePinned, pinned, contextText].filter(Boolean).join('\n\n');
    }

    if (REGION_KEYWORDS.some(kw => lowerQuestion.includes(kw))) {
      const a = await pinSection('2.%');
      const b = await pinSection('7.%');
      const all = [...a, ...b];
      const pinned = formatChunks(all);
      log.info(`[knowledge_base] region_pin: ${all.length} chunk`);
      return [rolePinned, pinned, contextText].filter(Boolean).join('\n\n');
    }

    return [rolePinned, contextText].filter(Boolean).join('\n\n');
  } catch (error) {
    log.error(`[knowledge_base] queryKnowledge hatası: ${error.message}`, error);
    return "";
  }
}

module.exports = {
  queryKnowledge
};
