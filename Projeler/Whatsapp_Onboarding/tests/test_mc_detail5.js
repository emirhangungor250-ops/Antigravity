const { config } = require('./config/env');
const API_URL = "https://api.manychat.com/fb";
async function t() {
    const response2 = await fetch(`${API_URL}/subscriber/findBySystemField?whatsapp_phone=905333666213`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${config.manychatApiToken}`,
      }
    });
    console.log(JSON.stringify(await response2.json(), null, 2));
}
t();
