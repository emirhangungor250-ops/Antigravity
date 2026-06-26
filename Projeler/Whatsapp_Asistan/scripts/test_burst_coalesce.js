// scripts/test_burst_coalesce.js
// Burst coalesce regression: kullanıcı kısa aralıkla 2 mesaj gönderdiğinde bot tek combined cevap üretmeli.
// Bu test webhook'a 200ms aralıkla iki POST atar, sonra Supabase'den assistant mesajlarını sayar.
// ManyChat bypass'lı (sim- prefix). OpenAI çağrısı yapar (~1-2 cent).
//
// Çalıştırma:
//   WEBHOOK_URL=http://localhost:3000/webhook/message node scripts/test_burst_coalesce.js
//   veya
//   WEBHOOK_URL=https://<RAILWAY_SERVICE_URL>/webhook/message node scripts/test_burst_coalesce.js

require('dotenv').config();
process.env.SIMULATION_MODE = 'true';

const { createClient } = require('@supabase/supabase-js');
const fetch = require('node-fetch');

const WEBHOOK_URL = process.env.WEBHOOK_URL || 'http://localhost:3000/webhook/message';
const WEBHOOK_SECRET = process.env.WHATSAPP_WEBHOOK_SECRET || '';
const SUPABASE_URL = process.env.SUPABASE_URL;
const SUPABASE_KEY = process.env.SUPABASE_SERVICE_ROLE_KEY;

if (!SUPABASE_URL || !SUPABASE_KEY) {
  console.error('SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY .env içinde gerekli.');
  process.exit(1);
}

const supabase = createClient(SUPABASE_URL, SUPABASE_KEY);
const subscriberId = `sim-burst-${Date.now()}`;
const phoneNumber = '+900000000099';

async function seedSubscriber() {
  const { error } = await supabase.from('subscribers').insert({
    subscriber_id: subscriberId,
    phone_number: phoneNumber,
    kvkk_accepted: true,
    kvkk_accepted_at: new Date().toISOString()
  });
  if (error) throw error;
}

async function postWebhook(message) {
  const headers = { 'Content-Type': 'application/json' };
  if (WEBHOOK_SECRET) headers['x-webhook-secret'] = WEBHOOK_SECRET;
  const r = await fetch(WEBHOOK_URL, {
    method: 'POST',
    headers,
    body: JSON.stringify({
      kullanici_id: subscriberId,
      last_text_input: message,
      phone_number: phoneNumber
    })
  });
  return r.status;
}

async function countAssistantMessages() {
  const { data, error } = await supabase
    .from('conversations')
    .select('id, content, created_at')
    .eq('subscriber_id', subscriberId)
    .eq('role', 'assistant')
    .order('created_at', { ascending: true });
  if (error) throw error;
  return data;
}

async function cleanup() {
  await supabase.from('conversations').delete().eq('subscriber_id', subscriberId);
  await supabase.from('subscribers').delete().eq('subscriber_id', subscriberId);
}

async function main() {
  console.log(`\n[test] Endpoint: ${WEBHOOK_URL}`);
  console.log(`[test] Sim subscriber: ${subscriberId}`);
  console.log('[test] Subscriber seed ediliyor...');
  await seedSubscriber();

  try {
    console.log('[test] Webhook #1 atılıyor (t=0ms): "Otomasyona nasıl başlıyorum?"');
    const r1 = await postWebhook('Otomasyona nasıl başlıyorum?');
    console.log(`[test] HTTP ${r1}`);

    await new Promise(r => setTimeout(r, 200));

    console.log('[test] Webhook #2 atılıyor (t=200ms): "Hangi paket önerirsin?"');
    const r2 = await postWebhook('Hangi paket önerirsin?');
    console.log(`[test] HTTP ${r2}`);

    const waitMs = 18000;
    console.log(`[test] AI cevabını beklemek için ${waitMs/1000}sn bekleniyor...`);
    await new Promise(r => setTimeout(r, waitMs));

    const assistantMsgs = await countAssistantMessages();
    console.log(`\n[test] Bulunan assistant mesaj sayısı: ${assistantMsgs.length}`);
    assistantMsgs.forEach((m, i) => {
      const preview = (m.content || '').substring(0, 120).replace(/\n/g, ' ');
      console.log(`  [${i+1}] ${m.created_at} :: ${preview}`);
    });

    if (assistantMsgs.length === 1) {
      console.log('\n[test] PASS — burst coalesce çalışıyor, tek combined cevap üretildi.');
      process.exitCode = 0;
    } else if (assistantMsgs.length === 0) {
      console.log('\n[test] FAIL — hiç cevap üretilmedi.');
      process.exitCode = 2;
    } else {
      console.log(`\n[test] FAIL — coalesce başarısız, ${assistantMsgs.length} ayrı cevap üretildi.`);
      process.exitCode = 1;
    }
  } finally {
    console.log('[test] Cleanup...');
    await cleanup();
    console.log('[test] Bitti.');
  }
}

main().catch(err => {
  console.error('[test] Beklenmeyen hata:', err);
  cleanup().finally(() => process.exit(3));
});
