require('dotenv').config({ path: './.env' });
const { validatePhone } = require('./services/phoneValidator');

async function runTests() {
  const tests = [
    "05321234567",
    "+905321234567",
    "905321234567",
    "Tel: 0532 123 45 67",
    "whatsapp: +90 532 123 4567",
    "Telefon numaram 0532 123 45 67", // LLM'e gitmesi beklenen durum
    "0532 123 45 67 numarasına ulaşın"
  ];

  console.log("--- PHONE VALIDATION TESTS ---");
  for (const t of tests) {
    const res = await validatePhone(t);
    console.log(`Input: "${t}"`);
    console.log(`Result:`, res);
    console.log("-----------------------");
  }
}

runTests();
