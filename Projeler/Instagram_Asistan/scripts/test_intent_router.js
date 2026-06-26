// scripts/test_intent_router.js
// Intent router için 4 intent × birkaç senaryo. SIMULATION_MODE=true ile çalışır.
process.env.SIMULATION_MODE = 'true';

const { classify } = require('../services/intent_router');
const log = require('../utils/logger');

const SCENARIOS = [
  { msg: 'merhaba', expected: 'ai_factory' },
  { msg: '<TOPLULUK_ADI> paketleri ne kadar?', expected: 'ai_factory' },
  { msg: 'Standard mı Premium mı uygun, kafe zincirim var', expected: 'ai_factory' },
  { msg: 'izle', expected: 'video_source' },
  { msg: 'şu yemek tarifi videosunda kullandığın AI hangisi?', expected: 'video_source' },
  { msg: '50 kişilik fabrikamıza yapay zeka kurun', expected: 'b2b' },
  { msg: 'Şirketim için özel AI projesi yaptırmak istiyorum', expected: 'b2b' },
  { msg: 'Claude ile ChatGPT arasında ne fark var?', expected: 'general' },
  { msg: 'Reels altyazısı için hangi AI iyi?', expected: 'general' },
  { msg: '<KULLANICI_ADI>\'la birebir görüşmek istiyorum', expected: 'refuse_contact' },
  { msg: 'WhatsApp numaranı paylaşır mısın', expected: 'refuse_contact' }
];

async function main() {
  let pass = 0, fail = 0;
  for (const scenario of SCENARIOS) {
    try {
      const result = await classify(scenario.msg, []);
      const ok = result.intent === scenario.expected;
      if (ok) {
        console.log(`✓ "${scenario.msg.substring(0, 40)}" → ${result.intent} (conf=${result.confidence?.toFixed(2)})`);
        pass++;
      } else {
        console.log(`✗ "${scenario.msg.substring(0, 40)}" → got ${result.intent}, expected ${scenario.expected}`);
        console.log(`  rationale: ${result.rationale}`);
        fail++;
      }
    } catch (err) {
      console.log(`✗ "${scenario.msg.substring(0, 40)}" → ERROR ${err.message}`);
      fail++;
    }
    await new Promise(r => setTimeout(r, 500));
  }
  console.log(`\nResult: ${pass}/${SCENARIOS.length} pass`);
  process.exit(fail === 0 ? 0 : 1);
}

main();
