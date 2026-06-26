require('dotenv').config();
const { ensureSubscriberAndSendFlow } = require('./services/manychat');

async function test() {
  try {
    const phone = '+905051234567'; // Change as needed
    const name = 'Test User';
    const flowId = 'content20240315124036_778641'; // Dummy flow ID
    
    console.log('Testing ensureSubscriberAndSendFlow...');
    await ensureSubscriberAndSendFlow(phone, name, flowId);
    console.log('Success!');
  } catch (error) {
    console.error('Test Failed:', error.message);
  }
}

test();
