// scripts/test_burst_coalesce.js
// 5 hızlı mesaj at, tek cevap dönmeli. Webhook'a paralel POST atar.
process.env.SIMULATION_MODE = 'true';

const PORT = process.env.PORT || 3457;
const URL = `http://localhost:${PORT}/webhook/instagram`;
const fetch = require('node-fetch');

const SUB = `sim-burst-${Date.now()}`;

async function send(text) {
  return fetch(URL, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ kullanici_id: SUB, last_text_input: text, ig_username: 'simtest' })
  });
}

async function main() {
  console.log(`Burst test başlıyor (subscriber=${SUB}, url=${URL})...`);
  const msgs = ['merhaba', '<TOPLULUK_ADI>', 'paketler ne', 'fiyat?', 'cevap ver'];
  const start = Date.now();
  const results = await Promise.all(msgs.map(send));
  const dur = Date.now() - start;
  console.log(`Webhook'a ${msgs.length} POST tamam (${dur}ms). Status'lar:`, results.map(r => r.status));

  console.log('Coalesce penceresi için 10sn bekliyor...');
  await new Promise(r => setTimeout(r, 10000));
  console.log('Test tamam. Server log\'larında "coalesced" satırı görmen gerekiyor; tek bir AI cevabı üretilmeli.');
  process.exit(0);
}

main().catch(err => {
  console.error(err);
  process.exit(1);
});
