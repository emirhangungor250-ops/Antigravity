const { config } = require('./config/env');
const API_URL = "https://api.manychat.com/fb";
async function t() {
    const response2 = await fetch(`${API_URL}/subscriber/createSubscriber`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${config.manychatApiToken}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        first_name: 'Test',
        whatsapp_phone: '533 366 6213', 
        consent_phrase: "onboarding"
      })
    });
    console.log(JSON.stringify(await response2.json(), null, 2));
}
t();
