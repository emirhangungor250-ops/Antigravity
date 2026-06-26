const BASE_URL = 'http://localhost:3001/webhook';
const TX_ID = 'test_tx_fulya_' + Date.now();

const payload1 = {
  transaction_id: TX_ID,
  first_name: 'Fulya',
  last_name: 'User',
  email: 'fulya113@mail.com',
  date: new Date().toISOString().split('T')[0]
};

const payload2 = {
  transaction_id: TX_ID,
  first_name: 'Fulya',
  last_name: 'User',
  email: 'fulya113@mail.com',
  answer_1: '+905335273513'
};

async function runTest() {
  try {
    console.log('🚀 [MOCK] Zap #1: new-paid-member gönderiliyor...');
    const res1 = await fetch(`${BASE_URL}/new-paid-member`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload1)
    });
    
    let data1;
    try { data1 = await res1.json(); } catch(e) { data1 = await res1.text(); }
    console.log(`✅ [MOCK] Zap #1 Sonuç: HTTP ${res1.status}`, data1);

    // Race condition testini gerçekçi yapmak için 2-3 saniye bekle
    console.log('\n⏳ 2 saniye bekleniyor...');
    await new Promise(r => setTimeout(r, 2000));

    console.log('🚀 [MOCK] Zap #2: membership-questions gönderiliyor...');
    const res2 = await fetch(`${BASE_URL}/membership-questions`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload2)
    });
    
    let data2;
    try { data2 = await res2.json(); } catch(e) { data2 = await res2.text(); }
    console.log(`✅ [MOCK] Zap #2 Sonuç: HTTP ${res2.status}`, data2);

  } catch (err) {
    console.error('\n❌ [MOCK] TEST BAŞARISIZ OLDU!');
    console.error('Hata:', err.message);
    if (err.cause) console.error('Detay:', err.cause);
    console.log('\n💡 İPUCU: Sunucu çalışmıyor olabilir. Ayrı bir terminalde "node server.js" çalıştırdığınızdan emin olun.');
  }
}

runTest();
