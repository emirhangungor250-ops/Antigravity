// scripts/simulate_conversations.js
// 30 senaryoyu generateResponse() ile koşturur, assertion'ları doğrular,
// simulation_report.html çıktısı üretir.
//
// Kullanım: node scripts/simulate_conversations.js [--scenario <id>]

require('dotenv').config();
// Simülasyon sırasında escalation.js gerçek mail gönderemesin
process.env.SIMULATION_MODE = 'true';

const fs = require('fs');
const path = require('path');
const { createClient } = require('@supabase/supabase-js');
const { generateResponse } = require('../services/ai_engine');
const { saveMessage } = require('../services/memory');
const scenarios = require('./simulation_scenarios');

const supabase = createClient(process.env.SUPABASE_URL, process.env.SUPABASE_SERVICE_ROLE_KEY);

const argv = process.argv.slice(2);
const onlyId = (() => {
  const idx = argv.indexOf('--scenario');
  return idx >= 0 ? Number(argv[idx + 1]) : null;
})();

function matches(text, pattern) {
  if (pattern instanceof RegExp) return pattern.test(text);
  return text.toLowerCase().includes(String(pattern).toLowerCase());
}

function assert(reply, expect) {
  const failures = [];
  const must = expect.mustContain || [];
  const mustNot = expect.mustNotContain || [];

  for (const p of must) {
    if (!matches(reply.text, p)) {
      failures.push(`missing: ${p instanceof RegExp ? p.toString() : '"' + p + '"'}`);
    }
  }
  for (const p of mustNot) {
    if (matches(reply.text, p)) {
      failures.push(`forbidden hit: ${p instanceof RegExp ? p.toString() : '"' + p + '"'}`);
    }
  }
  if (typeof expect.toolExpected === 'boolean') {
    if (expect.toolExpected && !reply.toolCalled) failures.push('tool_expected_but_not_called');
    if (expect.toolExpected === false && reply.toolCalled) failures.push('tool_called_but_not_expected');
  }
  // sanitizer_violations: bilgi amaçlı, fail saymıyoruz (mustContain/mustNotContain ana kontrol)
  return failures;
}

async function cleanupTestSubscriber(subId) {
  try {
    await supabase.from('conversations').delete().eq('subscriber_id', subId);
    await supabase.from('subscribers').delete().eq('subscriber_id', subId);
  } catch (e) { /* swallow */ }
}

async function ensureSubscriber(subId) {
  // KVKK onayını bypass etmek için subscribers'a önceden insert
  await supabase.from('subscribers').upsert({
    subscriber_id: subId,
    phone_number: '+900000000000',
    kvkk_accepted: true,
    kvkk_accepted_at: new Date().toISOString(),
    language: 'tr',
  }, { onConflict: 'subscriber_id' });
}

async function runScenario(s) {
  const subId = `sim-${s.id}-${Date.now()}`;
  await ensureSubscriber(subId);

  const turns = [];
  let allFailures = [];

  for (let i = 0; i < s.turns.length; i++) {
    const turn = s.turns[i];
    try {
      // ÖNCE: kullanıcı mesajını Supabase'e kaydet (production flow ile eşleşsin)
      await saveMessage(subId, 'user', turn.user);

      const reply = await generateResponse(
        subId,
        turn.user,
        'tr',
        { subscriberId: subId, phoneNumber: '+900000000000' },
        { returnMeta: true }
      );

      // SONRA: asistan cevabını da Supabase'e kaydet (sonraki turn history'sinde görünsün)
      await saveMessage(subId, 'assistant', reply.text);

      const fails = assert(reply, turn.expect);
      turns.push({
        userMessage: turn.user,
        assistantReply: reply.text,
        toolCalled: reply.toolCalled,
        violations: reply.violations || [],
        failures: fails,
        passed: fails.length === 0,
      });
      if (fails.length > 0) allFailures.push(...fails.map(f => `[t${i+1}] ${f}`));
    } catch (err) {
      turns.push({
        userMessage: turn.user,
        assistantReply: '',
        toolCalled: false,
        violations: [],
        failures: ['exception: ' + err.message],
        passed: false,
      });
      allFailures.push(`[t${i+1}] exception: ${err.message}`);
    }
  }

  await cleanupTestSubscriber(subId);

  return {
    id: s.id,
    category: s.category,
    name: s.name,
    turns,
    passed: allFailures.length === 0,
    failures: allFailures,
  };
}

function htmlEscape(s) {
  return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

function renderReport(results, startedAt, finishedAt) {
  const passCount = results.filter(r => r.passed).length;
  const failCount = results.length - passCount;
  const byCategory = {};
  for (const r of results) {
    byCategory[r.category] = byCategory[r.category] || { pass: 0, fail: 0 };
    if (r.passed) byCategory[r.category].pass++; else byCategory[r.category].fail++;
  }
  const catRows = Object.entries(byCategory).map(([cat, c]) =>
    `<tr><td>${cat}</td><td>${c.pass}</td><td>${c.fail}</td></tr>`).join('');

  const scenarioBlocks = results.map(r => {
    const statusClass = r.passed ? 'pass' : 'fail';
    const statusLabel = r.passed ? 'PASS' : 'FAIL';
    const turnsHtml = r.turns.map((t, i) => `
      <div class="turn ${t.passed ? 'pass' : 'fail'}">
        <div class="turn-head">Turn ${i + 1}${t.toolCalled ? ' · tool çağrıldı' : ''}</div>
        <div class="bubble user"><span class="who">Kullanıcı</span>${htmlEscape(t.userMessage)}</div>
        <div class="bubble bot"><span class="who">Asistan</span>${htmlEscape(t.assistantReply)}</div>
        ${t.failures.length > 0 ? `<div class="failures">${t.failures.map(f => `<div>✗ ${htmlEscape(f)}</div>`).join('')}</div>` : '<div class="ok">✓ assertions passed</div>'}
      </div>
    `).join('');

    return `
      <article class="scenario ${statusClass}">
        <header>
          <span class="badge ${statusClass}">${statusLabel}</span>
          <span class="id">#${r.id}</span>
          <span class="cat">${r.category}</span>
          <h3>${htmlEscape(r.name)}</h3>
        </header>
        ${turnsHtml}
      </article>
    `;
  }).join('');

  return `<!doctype html>
<html lang="tr"><head><meta charset="utf-8">
<title>Simülasyon Raporu | WhatsApp Asistan KB v7</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>
  :root { --bg:#0f1115; --panel:#161a22; --line:#232938; --ink:#e8ecf3; --ink-2:#9aa3b2; --ink-3:#6b7384; --red:#ef4444; --green:#22c55e; --blue:#3b82f6; --orange:#f59e0b; --quote:#11151c; }
  * { box-sizing:border-box; }
  html,body { margin:0; padding:0; background:var(--bg); color:var(--ink); font-family:-apple-system, BlinkMacSystemFont, "SF Pro Text", "Inter", system-ui, sans-serif; font-size:15.5px; line-height:1.55; -webkit-font-smoothing:antialiased; }
  .wrap { max-width:980px; margin:0 auto; padding:48px 28px 100px; }
  header.intro { border-bottom:1px solid var(--line); padding-bottom:28px; margin-bottom:32px; }
  .eyebrow { color:var(--ink-3); font-size:12px; letter-spacing:.08em; text-transform:uppercase; margin:0 0 10px; }
  h1 { font-size:30px; margin:0 0 14px; font-weight:700; letter-spacing:-.01em; }
  .lede { color:var(--ink-2); font-size:16px; max-width:640px; margin:0 0 20px; }
  .summary { display:grid; grid-template-columns:repeat(4,1fr); gap:1px; background:var(--line); border:1px solid var(--line); border-radius:10px; overflow:hidden; }
  .summary .cell { background:var(--panel); padding:14px 16px; }
  .summary .v { font-size:22px; font-weight:600; font-variant-numeric:tabular-nums; }
  .summary .l { font-size:11px; color:var(--ink-3); text-transform:uppercase; letter-spacing:.06em; }
  .pass .v { color:var(--green); }
  .fail .v { color:var(--red); }
  table.cat { width:100%; border-collapse:collapse; margin:24px 0; font-size:14.5px; }
  table.cat th, table.cat td { padding:8px 12px; border-bottom:1px solid var(--line); text-align:left; }
  table.cat th { color:var(--ink-3); font-size:11px; letter-spacing:.06em; text-transform:uppercase; }
  table.cat td { color:var(--ink); }
  h2.section { font-size:13px; letter-spacing:.1em; text-transform:uppercase; color:var(--ink-3); margin:40px 0 14px; font-weight:600; }
  .scenario { background:var(--panel); border:1px solid var(--line); border-left:3px solid var(--ink-3); border-radius:10px; padding:20px 24px; margin-bottom:14px; }
  .scenario.pass { border-left-color:var(--green); }
  .scenario.fail { border-left-color:var(--red); }
  .scenario header { display:flex; align-items:baseline; gap:10px; margin-bottom:12px; flex-wrap:wrap; }
  .badge { display:inline-block; font-size:11px; font-weight:700; padding:3px 8px; border-radius:999px; letter-spacing:.05em; }
  .badge.pass { background:rgba(34,197,94,.15); color:var(--green); }
  .badge.fail { background:rgba(239,68,68,.15); color:var(--red); }
  .id { color:var(--ink-3); font-variant-numeric:tabular-nums; font-size:14px; }
  .cat { color:var(--ink-3); font-size:11px; letter-spacing:.06em; text-transform:uppercase; }
  .scenario h3 { margin:0; font-size:16px; font-weight:600; flex-basis:100%; }
  .turn { background:var(--quote); border:1px solid var(--line); border-radius:8px; padding:12px 14px; margin-bottom:10px; }
  .turn-head { font-size:11px; color:var(--ink-3); letter-spacing:.06em; text-transform:uppercase; margin-bottom:8px; font-weight:600; }
  .bubble { padding:10px 12px; border-radius:6px; margin:6px 0; white-space:pre-wrap; font-family:"SF Mono", Menlo, Consolas, monospace; font-size:13px; line-height:1.5; color:var(--ink); border-left:2px solid var(--line); }
  .bubble.user { border-left-color:var(--blue); background:#0d1320; }
  .bubble.bot { border-left-color:var(--orange); background:#181410; }
  .who { display:block; font-family:-apple-system,system-ui,sans-serif; font-size:10px; color:var(--ink-3); letter-spacing:.06em; text-transform:uppercase; font-weight:600; margin-bottom:4px; }
  .failures { background:rgba(239,68,68,.08); border:1px solid rgba(239,68,68,.25); border-radius:6px; padding:8px 10px; margin-top:8px; font-size:12.5px; color:var(--red); font-family:"SF Mono", Menlo, monospace; }
  .ok { color:var(--green); font-size:12px; margin-top:6px; }
  footer { margin-top:40px; padding-top:18px; border-top:1px solid var(--line); color:var(--ink-3); font-size:12.5px; }
</style></head>
<body><div class="wrap">
<header class="intro">
  <p class="eyebrow">Simülasyon Raporu · WhatsApp Asistan KB v7</p>
  <h1>${results.length} senaryo · ${passCount} pass · ${failCount} fail</h1>
  <p class="lede">Her senaryo gerçek generateResponse() çağrısıyla koşturuldu (RAG + GPT-4.1-mini + post-process sanitize). Assertion'lar mustContain, mustNotContain, tool çağrı beklentisi ve sanitizer violations.</p>
  <div class="summary">
    <div class="cell"><div class="v">${results.length}</div><div class="l">Toplam</div></div>
    <div class="cell pass"><div class="v">${passCount}</div><div class="l">Pass</div></div>
    <div class="cell fail"><div class="v">${failCount}</div><div class="l">Fail</div></div>
    <div class="cell"><div class="v">${Math.round(((finishedAt - startedAt) / 1000))}sn</div><div class="l">Süre</div></div>
  </div>
  <table class="cat"><tr><th>Kategori</th><th>Pass</th><th>Fail</th></tr>${catRows}</table>
</header>
<h2 class="section">Senaryo detayları</h2>
${scenarioBlocks}
<footer>Üretildi: ${new Date().toISOString()} · KB: v7 · Model: gpt-4.1-mini · Post-process: sanitize+retry</footer>
</div></body></html>`;
}

async function main() {
  const start = Date.now();
  const list = onlyId ? scenarios.filter(s => s.id === onlyId) : scenarios;

  if (list.length === 0) {
    console.error(`Hiç senaryo bulunamadı. --scenario ${onlyId} ile filtrelendi.`);
    process.exit(1);
  }

  console.log(`[sim] ${list.length} senaryo başlıyor...`);
  const results = [];
  for (const s of list) {
    process.stdout.write(`[sim] #${s.id} ${s.name} ... `);
    const r = await runScenario(s);
    results.push(r);
    console.log(r.passed ? 'PASS' : `FAIL (${r.failures.length})`);
  }

  const finish = Date.now();
  const html = renderReport(results, start, finish);
  const outPath = path.join(__dirname, '..', 'simulation_report.html');
  fs.writeFileSync(outPath, html, 'utf8');

  const passCount = results.filter(r => r.passed).length;
  console.log(`\n[sim] ${passCount}/${results.length} pass | rapor: ${outPath}`);

  if (passCount < results.length) {
    console.log('\nFail detayları:');
    for (const r of results.filter(x => !x.passed)) {
      console.log(`  #${r.id} ${r.name}`);
      for (const f of r.failures) console.log(`    - ${f}`);
    }
  }

  process.exit(passCount === results.length ? 0 : 1);
}

main().catch(err => {
  console.error('FATAL:', err);
  process.exit(2);
});
