// Mock test: WA_ID_INVALID + happy path + generic error + dual-cron geçiş.
// Run: node tests/test_wa_optin_invalid.js

const fs = require('fs');

// ─── Env setup (config/env modülünün crash etmemesi için) ────────
process.env.MANYCHAT_API_TOKEN = 'fake_token_for_test';
process.env.NOTION_API_KEY = 'fake';
process.env.NOTION_DATABASE_ID = 'fake';
process.env.RESEND_API_KEY = 'fake';
process.env.WEBHOOK_SECRET = 'fake';
process.env.ADMIN_TOKEN = 'fake';
process.env.MANYCHAT_FLOW_ID_DAY_0 = 'content20240101000000_000001';

// ─── Mock fetch — senaryoya göre cevap döndür ─────────────────
const ORIG_FETCH = global.fetch;
let scenario = 'wa_id_invalid';

function setScenario(s) { scenario = s; }

global.fetch = async (url, options) => {
  const u = String(url);

  if (u.includes('/page/getCustomFields')) {
    return new Response(JSON.stringify({
      status: 'success',
      data: [{ id: 999, name: 'whatsapp_phone_text' }]
    }), { status: 200, headers: { 'content-type': 'application/json' } });
  }

  if (u.includes('/subscriber/findByCustomField')
      || u.includes('/subscriber/findBySystemField')
      || u.includes('/subscriber/findByName')) {
    return new Response(JSON.stringify({ status: 'success', data: [] }), {
      status: 200, headers: { 'content-type': 'application/json' }
    });
  }

  if (u.includes('/subscriber/createSubscriber')) {
    if (scenario === 'wa_id_invalid') {
      return new Response(JSON.stringify({
        status: 'error',
        message: 'Validation error',
        details: { messages: { wa_id: ['WhatsApp account not found'] } }
      }), { status: 200, headers: { 'content-type': 'application/json' } });
    }
    if (scenario === 'happy') {
      return new Response(JSON.stringify({
        status: 'success',
        data: { id: 12345 }
      }), { status: 200, headers: { 'content-type': 'application/json' } });
    }
    if (scenario === 'generic_error') {
      return new Response(JSON.stringify({
        status: 'error',
        message: 'Some unexpected ManyChat error'
      }), { status: 200, headers: { 'content-type': 'application/json' } });
    }
  }

  if (u.includes('/subscriber/setCustomFields')) {
    return new Response(JSON.stringify({ status: 'success' }), {
      status: 200, headers: { 'content-type': 'application/json' }
    });
  }

  if (u.includes('/sending/sendFlow')) {
    return new Response(JSON.stringify({ status: 'success' }), {
      status: 200, headers: { 'content-type': 'application/json' }
    });
  }

  return new Response(JSON.stringify({ status: 'error', message: `Unhandled URL: ${u}` }), {
    status: 500, headers: { 'content-type': 'application/json' }
  });
};

// ─── Helpers ──────────────────────────────────────────────────
function freshManychat() {
  delete require.cache[require.resolve('../services/manychat')];
  delete require.cache[require.resolve('../config/env')];
  return require('../services/manychat');
}

// ─── TEST 1: WA_ID_INVALID → typed error ──────────────────────
async function test1() {
  setScenario('wa_id_invalid');
  const manychat = freshManychat();
  let caught;
  try {
    await manychat.ensureSubscriberAndSendFlow('+905301594810', 'Test', 'content20240101000000_000001');
  } catch (e) { caught = e; }
  if (!caught || caught.code !== 'WA_ID_INVALID') {
    throw new Error(`TEST 1 FAIL: WA_ID_INVALID atılmadı. code=${caught?.code}, msg=${caught?.message}`);
  }
  console.log('✅ TEST 1 PASS: createSubscriber wa_id validation → WA_ID_INVALID typed error.');
}

// ─── TEST 2: Happy path — flow tetiklenir, hata yok ───────────
async function test2() {
  setScenario('happy');
  const manychat = freshManychat();
  const subscriberId = await manychat.ensureSubscriberAndSendFlow('+905300000001', 'Happy', 'content20240101000000_000001');
  if (subscriberId !== 12345) {
    throw new Error(`TEST 2 FAIL: subscriberId beklenmedik. Aldık: ${subscriberId}`);
  }
  console.log('✅ TEST 2 PASS: Happy path → subscriber created + flow sent (subscriberId=12345).');
}

// ─── TEST 3: Generic ManyChat hatası → throw eder, WA_ID değil ──
async function test3() {
  setScenario('generic_error');
  const manychat = freshManychat();
  let caught;
  try {
    await manychat.ensureSubscriberAndSendFlow('+905300000002', 'Generic', 'content20240101000000_000001');
  } catch (e) { caught = e; }
  if (!caught) throw new Error('TEST 3 FAIL: generic error throw etmedi.');
  if (caught.code === 'WA_ID_INVALID') {
    throw new Error('TEST 3 FAIL: generic error yanlışlıkla WA_ID_INVALID olarak işaretlendi.');
  }
  if (!/ManyChat API Hatası|Some unexpected/.test(caught.message)) {
    throw new Error(`TEST 3 FAIL: generic error mesajı beklenmedik: ${caught.message}`);
  }
  console.log('✅ TEST 3 PASS: Generic ManyChat hatası → throw (WA_ID_INVALID değil).');
}

// ─── TEST 4: server.js wa-optin handler kaynak audit ──────────
async function test4() {
  const src = fs.readFileSync(require.resolve('../server.js'), 'utf8');
  const startIdx = src.indexOf("app.post('/webhook/wa-optin'");
  const endIdx = src.indexOf("app.post('/webhook/wa-confirmed'", startIdx);
  const h = src.slice(startIdx, endIdx);

  if (!/WA_ID_INVALID/.test(h)) throw new Error('TEST 4 FAIL: WA_ID_INVALID yakalama yok.');
  if (!/skipped:\s*true/.test(h)) throw new Error('TEST 4 FAIL: skipped:true response yok.');
  if (!/appendNote\(member\.id,/.test(h)) throw new Error('TEST 4 FAIL: Notion appendNote yok.');
  // Generic catch hâlâ admin alert atmalı (regression koruması)
  if (!/sendAdminAlertEmail\(`Webhook Hatası: wa-optin`/.test(h)) {
    throw new Error('TEST 4 FAIL: generic catch admin alert kaybolmuş — diğer hatalar artık sessizce ölüyor.');
  }
  console.log('✅ TEST 4 PASS: wa-optin handler — WA_ID_INVALID skipped + generic catch alert korunuyor.');
}

// ─── TEST 5: cron.js isPermanentError + dual-cron geçiş ───────
async function test5() {
  const src = fs.readFileSync(require.resolve('../cron.js'), 'utf8');

  const fnMatch = src.match(/function isPermanentError\(err\)\s*\{([\s\S]*?)\n\}/);
  if (!fnMatch) throw new Error('TEST 5 FAIL: isPermanentError fonksiyonu bulunamadı.');
  if (!/err\.code\s*===\s*['"]WA_ID_INVALID['"]/.test(fnMatch[1])) {
    throw new Error('TEST 5 FAIL: isPermanentError içinde WA_ID_INVALID kontrolü yok.');
  }

  // Dual cron'da WA_ID_INVALID + email başarılı → email-only geçiş bloku var mı?
  if (!/waErr\.code\s*===\s*['"]WA_ID_INVALID['"]/.test(src)) {
    throw new Error('TEST 5 FAIL: cron dual flow\'da WA_ID_INVALID branchi yok.');
  }
  if (!/onboardingStatus:\s*['"]email['"]/.test(src)) {
    throw new Error('TEST 5 FAIL: cron dual fallback email status update yok.');
  }
  console.log('✅ TEST 5 PASS: cron isPermanentError + dual-cron WA_ID_INVALID → email-only geçişi.');
}

// ─── TEST 6: feedback regression — Validation error ama farklı detail ──
// wa_id YOK ama "Validation error" → eski koşul tutmasın, generic throw etsin.
async function test6() {
  global.fetch = async (url) => {
    const u = String(url);
    if (u.includes('/page/getCustomFields')) {
      return new Response(JSON.stringify({ status: 'success', data: [{ id: 999, name: 'whatsapp_phone_text' }] }),
        { status: 200, headers: { 'content-type': 'application/json' } });
    }
    if (u.includes('/subscriber/find')) {
      return new Response(JSON.stringify({ status: 'success', data: [] }),
        { status: 200, headers: { 'content-type': 'application/json' } });
    }
    if (u.includes('/subscriber/createSubscriber')) {
      // Validation error AMA wa_id alanı yok — sadece first_name
      return new Response(JSON.stringify({
        status: 'error',
        message: 'Validation error',
        details: { messages: { first_name: ['Required'] } }
      }), { status: 200, headers: { 'content-type': 'application/json' } });
    }
    return new Response(JSON.stringify({ status: 'error' }), { status: 500 });
  };

  const manychat = freshManychat();
  let caught;
  try {
    await manychat.ensureSubscriberAndSendFlow('+905300000003', '', 'content20240101000000_000001');
  } catch (e) { caught = e; }
  if (!caught) throw new Error('TEST 6 FAIL: throw etmedi.');
  if (caught.code === 'WA_ID_INVALID') {
    throw new Error('TEST 6 FAIL: wa_id alanı olmayan Validation error yanlış WA_ID_INVALID olarak işaretlendi.');
  }
  console.log('✅ TEST 6 PASS: wa_id\'siz Validation error yanlış branch\'e düşmüyor.');
}

(async () => {
  try {
    await test1();
    await test2();
    await test3();
    await test4();
    await test5();
    await test6();
    console.log('\n🟢 TÜM TESTLER GEÇTİ (6/6). Fix doğrulandı.');
  } catch (e) {
    console.error('\n🔴 TEST HATASI:', e.message);
    process.exit(1);
  } finally {
    global.fetch = ORIG_FETCH;
  }
})();
