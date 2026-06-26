require('dotenv').config();
const { ensureSubscriberAndSendFlow } = require('./services/manychat');
const { ONBOARDING_FLOWS } = require('./config/templates');

(async () => {
  try {
    const phoneNumber = "+905333666213";
    const firstName = "Test";
    const flowId = ONBOARDING_FLOWS[0].flow_id;

    console.log(`\n===========================================`);
    console.log(`TEST BAŞLIYOR: Gün 0 Flow Tetikleme`);
    console.log(`Telefon: ${phoneNumber}`);
    console.log(`Flow ID: ${flowId}`);
    console.log(`===========================================\n`);

    const result = await ensureSubscriberAndSendFlow(phoneNumber, firstName, flowId);
    
    console.log(`\n✅ TEST BAŞARILI. ManyChat ID: ${result}`);
  } catch (error) {
    console.error(`\n❌ TEST HATASI:`, error);
  }
})();
