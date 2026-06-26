// services/knowledge_base.js
const OpenAI = require('openai');
const { config } = require('../config/env');
const { supabase } = require('./memory');
const log = require('../utils/logger');

const openai = new OpenAI({ apiKey: config.openaiApiKey });

// SABLON: Bu anahtar kelime listeleri, kullanicinin sorusuna gore bilgi
// tabaninin belirli BOLUMLERINI (section) sabitlemeye (pin) yarar. Kendi bilgi
// tabaninizin konularina gore bu listeleri ve asagidaki pinSection() cagrilarindaki
// section numaralarini guncelleyin.
const PRICING_KEYWORDS = ['fiyat', 'ücret', 'price', 'ne kadar', 'paket', 'aylık', 'yıllık', 'indirim', 'kampanya'];
const AUTOMATION_KEYWORDS = ['otomasyon', 'automation', 'ürün', 'hizmet', 'özellik', 'nasıl çalışıyor'];
const LINK_KEYWORDS = [
  'link', 'odeme', 'ödeme', 'uyelik', 'üyelik', 'nasil ulasacagim', 'nasil erisecegim',
  'nereden basla', 'nereden başla', 'kayit', 'kayıt', 'uye ol', 'üye ol',
  'nereden uye', 'nereden üye', 'giris', 'giriş',
  'nereden baslayacagim', 'nereden başlayacağım', 'ulasamiyorum', 'ulaşamıyorum', 'erisim', 'erişim',
  'gorus', 'görüş', 'gorusebilir', 'görüşebilir', 'gorusmek', 'görüşmek',
  'ilet', 'iletim', 'iletisim', 'iletişim', 'konus', 'konuş', 'konusmak', 'konuşmak',
  'destek', 'yardim', 'yardım', 'birebir',
  'arar mi', 'arar mı', 'arayacak', 'aranacak',
  'ulasmak', 'ulaşmak', 'ulasabilir', 'ulaşabilir'
];
const MEMBER_TECH_KEYWORDS = ['kayit oldum', 'kayıt oldum', 'uye oldum', 'üye oldum', 'paket aldim', 'paket aldım', 'goremiyorum', 'göremiyorum', 'hata veriyor', 'çalışmıyor', 'calismiyor', 'error', 'kuramadim', 'kuramadım'];

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

    // Fiyat sorusu → Bölüm 2.% chunk'ları
    if (PRICING_KEYWORDS.some(kw => lowerQuestion.includes(kw))) {
      const pricingChunks = await pinSection('2.%');
      const pinned = formatChunks(pricingChunks);
      log.info(`[knowledge_base] pricing_pin: ${pricingChunks.length} chunk`);
      return [rolePinned, pinned, contextText].filter(Boolean).join('\n\n');
    }

    // Urun/hizmet sorusu → ilgili KB bolumlerini sabitle (kendi section no'larinizla degistirin)
    if (AUTOMATION_KEYWORDS.some(kw => lowerQuestion.includes(kw))) {
      const a = await pinSection('3.%');
      const b = await pinSection('3.5.%');
      const c = await pinSection('4.%');
      const all = [...a, ...b, ...c];
      const seen = new Set();
      const dedup = all.filter(ch => {
        const k = ch.section + ch.section_title;
        if (seen.has(k)) return false;
        seen.add(k);
        return true;
      });
      const pinned = formatChunks(dedup);
      log.info(`[knowledge_base] automation_pin: ${dedup.length} chunk`);
      return [rolePinned, pinned, contextText].filter(Boolean).join('\n\n');
    }

    // Mevcut üye teknik sorusu → 13.2.% (üye teknik) + 5.% (onboarding)
    if (MEMBER_TECH_KEYWORDS.some(kw => lowerQuestion.includes(kw))) {
      const a = await pinSection('13.%');
      const b = await pinSection('5.%');
      const all = [...a, ...b];
      const pinned = formatChunks(all);
      log.info(`[knowledge_base] member_tech_pin: ${all.length} chunk`);
      return [rolePinned, pinned, contextText].filter(Boolean).join('\n\n');
    }

    // Link / iletisim / eskalasyon sorusu → ilgili KB bolumlerini sabitle
    if (LINK_KEYWORDS.some(kw => lowerQuestion.includes(kw))) {
      const a = await pinSection('10.%');
      const b = await pinSection('13.%');
      const c = await pinSection('16.%');
      const d = await pinSection('17.2%');
      const all = [...a, ...b, ...c, ...d];
      const pinned = formatChunks(all);
      log.info(`[knowledge_base] link_pin: ${all.length} chunk`);
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
