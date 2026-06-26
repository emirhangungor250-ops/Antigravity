// scripts/test_conversation.js
// Asistanın canlı KB + prompt + RAG zincirinden geçerek doğru cevap ürettiğini doğrulayan
// scripted regression test. ManyChat'i bypass eder, doğrudan generateResponse() çağırır.
// Çalıştırma: npm run test:flows
// Gereksinim: .env'de OPENAI_API_KEY, SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY tanımlı.

require('dotenv').config();
const { generateResponse } = require('../services/ai_engine');

const TEST_SUBSCRIBER_ID = 'test-runner-scripted';
const PHONE = '+900000000000';

// Yardımcı assertion'lar
function mustContain(text, needles) {
  const lower = text.toLowerCase();
  const missing = needles.filter(n => !lower.includes(n.toLowerCase()));
  return missing.length === 0 ? null : `eksik: ${missing.join(' | ')}`;
}

function mustNotContain(text, needles) {
  const lower = text.toLowerCase();
  const found = needles.filter(n => lower.includes(n.toLowerCase()));
  return found.length === 0 ? null : `yasak ifade gecti: ${found.join(' | ')}`;
}

// SABLON: Asagidaki senaryolar ornek/placeholder'dir. Kendi bilgi tabaniniza
// gore guncelleyin.
//   - message: kullanicinin yazdigi mesaj
//   - must:    cevapta MUTLAKA gecmesi gereken ifadeler
//   - mustNot: cevapta KESINLIKLE gecmemesi gereken ifadeler (em-dash, yasak vaatler vb.)
const scenarios = [
  {
    name: 'Ornek 1 — bilgi tabaninda olan bir soru, dogru link donmeli',
    message: '[KULLANICI SORUSU — orn: kayit oldum, nereden baslayayim?]',
    must: ['[CEVAPTA GECMESI GEREKEN IFADE / LINK]'],
    mustNot: ['—']
  },
  {
    name: 'Ornek 2 — hassas durum (iade/sikayet), eskalasyon beklenir',
    message: '[HASSAS KULLANICI MESAJI — orn: param iade edilsin]',
    must: [],
    mustNot: []
  },
  {
    name: 'Ornek 3 — bilgi tabani disi soru, yanlis vaat verilmemeli',
    message: '[KAPSAM DISI SORU]',
    must: [],
    mustNot: ['[VERILMEMESI GEREKEN VAAT]']
  }
];

async function runOne(scn, idx) {
  const subId = `${TEST_SUBSCRIBER_ID}-${idx}`;
  let response;
  try {
    response = await generateResponse(
      subId,
      scn.message,
      'Turkish',
      { subscriberId: subId, phoneNumber: PHONE },
      { skipHistory: true }
    );
  } catch (err) {
    return { ok: false, name: scn.name, reason: `crash: ${err.message}`, response: '' };
  }

  const errors = [];
  if (scn.must && scn.must.length > 0) {
    const r = mustContain(response, scn.must);
    if (r) errors.push(r);
  }
  if (scn.mustNot && scn.mustNot.length > 0) {
    const r = mustNotContain(response, scn.mustNot);
    if (r) errors.push(r);
  }

  return {
    ok: errors.length === 0,
    name: scn.name,
    reason: errors.join(' ; '),
    response
  };
}

async function main() {
  console.log('\n=== Whatsapp_Asistan scripted regression ===\n');
  const results = [];
  for (let i = 0; i < scenarios.length; i++) {
    const scn = scenarios[i];
    process.stdout.write(`[${i + 1}/${scenarios.length}] ${scn.name} ... `);
    const r = await runOne(scn, i);
    results.push(r);
    console.log(r.ok ? 'PASS' : 'FAIL');
    if (!r.ok) {
      console.log(`    sebep: ${r.reason}`);
      console.log(`    cevap: ${r.response.replace(/\n/g, ' | ').slice(0, 280)}`);
    }
  }

  const pass = results.filter(r => r.ok).length;
  const fail = results.length - pass;
  console.log(`\n=== Sonuc: ${pass}/${results.length} PASS, ${fail} FAIL ===\n`);

  // Detayli rapor
  if (process.env.VERBOSE) {
    for (const r of results) {
      console.log('\n---', r.name, '---');
      console.log(r.response);
    }
  }

  process.exit(fail === 0 ? 0 : 1);
}

main().catch(err => {
  console.error('Test runner crashed:', err);
  process.exit(2);
});
