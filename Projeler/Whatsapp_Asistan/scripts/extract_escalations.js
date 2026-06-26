#!/usr/bin/env node
/**
 * Geriye dönük eskalasyon çıkarımı.
 *
 * Whatsapp_Asistan eskalasyon mailleri yönetici inbox'ına gidiyor
 * ve DB'ye loglanmıyor. Birikmiş soruları çıkarmak için: conversations
 * tablosundaki asistan cevaplarında zorunlu eskalasyon imzasını
 * (eskalasyon imza pattern'ı, sistem prompt'unda explicitly required)
 * ara, her match'in ÖNCESİNDEKİ user mesajını orijinal soru olarak al,
 * bağlam için birkaç mesaj daha çek.
 *
 * Kullanım:
 *   node scripts/extract_escalations.js [SINCE_ISO]
 *   node scripts/extract_escalations.js 2026-05-01
 */

require('dotenv').config({ path: require('path').join(__dirname, '..', '.env') });
const { createClient } = require('@supabase/supabase-js');

const SUPABASE_URL = process.env.SUPABASE_URL;
const SUPABASE_KEY = process.env.SUPABASE_SERVICE_ROLE_KEY;
if (!SUPABASE_URL || !SUPABASE_KEY) {
  console.error('SUPABASE_URL veya SUPABASE_SERVICE_ROLE_KEY .env\'de bulunamadı.');
  process.exit(1);
}

const since = process.argv[2] || '2026-05-01';
const supabase = createClient(SUPABASE_URL, SUPABASE_KEY);

// NOT: Bu pattern'lar botun kendi eskalasyon cevabindaki imza cumlesini yakalar.
// Bilgi tabaninizdaki eskalasyon imzasina gore bu listeyi guncelleyin.
const ESCALATION_PATTERNS = [
  /yetkili(?:ye|mize)?\s+ileti(?:yorum|yorum\.|yor\.|leceğim|lecek)/i,
  /yetkili(?:ye|mize)?\s+yönlendir/i,
  /en\s+kısa\s+sürede\s+(?:sana\s+ulaş|size\s+ulaş)/i,
  /yöneticime\s+ileti/i,
  /admin'?e\s+ileti/i,
];

const HASSAS_KEYWORDS = [
  'iade', 'geri ödeme', 'refund', 'şikayet', 'şikâyet', 'fatura',
  'üyeliğimi dondur', 'üyeliği dondur', 'üyeliğimi iptal', 'iptal et',
  'tier', 'paket değiş', 'paketimi değiş', 'paketimi yükselt',
  'paketimi düşür', 'kızgın', 'memnun değil', 'memnun değilim',
  'çok kötü', 'aldatıldım', 'kandırıldım', 'sahtekar',
];

function categorize(userQuestion) {
  const lower = userQuestion.toLowerCase();
  for (const kw of HASSAS_KEYWORDS) if (lower.includes(kw)) return 'HASSAS';
  return 'BİLİNMEYEN';
}

function isEscalationReply(content) {
  if (!content) return false;
  return ESCALATION_PATTERNS.some(p => p.test(content));
}

async function fetchAllConversations(sinceIso) {
  const all = [];
  let from = 0;
  const PAGE = 1000;
  while (true) {
    const { data, error } = await supabase
      .from('conversations')
      .select('id, subscriber_id, role, content, created_at')
      .gte('created_at', sinceIso)
      .order('subscriber_id', { ascending: true })
      .order('created_at', { ascending: true })
      .range(from, from + PAGE - 1);
    if (error) throw error;
    all.push(...data);
    if (data.length < PAGE) break;
    from += PAGE;
  }
  return all;
}

async function fetchSubscriberPhones(ids) {
  if (ids.length === 0) return new Map();
  const { data, error } = await supabase
    .from('subscribers')
    .select('subscriber_id, phone_number')
    .in('subscriber_id', ids);
  if (error) throw error;
  const map = new Map();
  for (const row of data) map.set(row.subscriber_id, row.phone_number);
  return map;
}

(async () => {
  const sinceIso = new Date(since).toISOString();
  console.error(`[extract] Çekiliyor: created_at >= ${sinceIso}`);
  const all = await fetchAllConversations(sinceIso);
  console.error(`[extract] Toplam mesaj: ${all.length}`);

  const bySubscriber = new Map();
  for (const m of all) {
    if (!bySubscriber.has(m.subscriber_id)) bySubscriber.set(m.subscriber_id, []);
    bySubscriber.get(m.subscriber_id).push(m);
  }

  const escalations = [];
  for (const [sid, msgs] of bySubscriber) {
    for (let i = 0; i < msgs.length; i++) {
      const m = msgs[i];
      if (m.role !== 'assistant') continue;
      if (!isEscalationReply(m.content)) continue;

      let userQuestion = null;
      for (let j = i - 1; j >= 0; j--) {
        if (msgs[j].role === 'user') { userQuestion = msgs[j]; break; }
      }
      if (!userQuestion) continue;

      const ctxStart = Math.max(0, i - 5);
      const context = msgs.slice(ctxStart, i + 1).map(x => ({
        role: x.role, content: x.content, ts: x.created_at,
      }));

      escalations.push({
        subscriberId: sid,
        timestamp: m.created_at,
        category: categorize(userQuestion.content),
        userQuestion: userQuestion.content,
        userQuestionTs: userQuestion.created_at,
        assistantReply: m.content,
        context,
      });
    }
  }

  const phones = await fetchSubscriberPhones([...bySubscriber.keys()]);
  for (const e of escalations) e.phoneNumber = phones.get(e.subscriberId) || null;

  escalations.sort((a, b) => a.timestamp.localeCompare(b.timestamp));

  console.error(`[extract] Bulunan eskalasyon: ${escalations.length}`);
  console.log(JSON.stringify({
    since: sinceIso,
    totalMessages: all.length,
    uniqueSubscribers: bySubscriber.size,
    escalations,
  }, null, 2));
})().catch(err => {
  console.error('[extract] Hata:', err.message);
  console.error(err.stack);
  process.exit(1);
});
