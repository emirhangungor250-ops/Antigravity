// scripts/test_rate_limit.js
// 11 ardışık mesaj at, 11. mesajda allowed=false dönmeli.
process.env.SIMULATION_MODE = 'true';

const { checkAndConsume, resetSubscriber } = require('../services/rate_limiter');

const TEST_SUB = `sim-rate-${Date.now()}`;

async function main() {
  await resetSubscriber(TEST_SUB).catch(() => {});
  let passes = 0;
  let denials = 0;
  for (let i = 1; i <= 12; i++) {
    const r = await checkAndConsume(TEST_SUB, { max: 10, windowHours: 24 });
    console.log(`#${i} allowed=${r.allowed} count=${r.count}`);
    if (r.allowed) passes++; else denials++;
  }
  await resetSubscriber(TEST_SUB).catch(() => {});

  // İlk 10 PASS, sonra 2 DENY beklenir
  const ok = passes === 10 && denials === 2;
  console.log(`\nResult: ${ok ? 'PASS' : 'FAIL'} (passes=${passes} denials=${denials})`);
  process.exit(ok ? 0 : 1);
}

main();
