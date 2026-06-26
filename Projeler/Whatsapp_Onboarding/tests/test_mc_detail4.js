const { config } = require('./config/env');
const API_URL = "https://api.manychat.com/fb";
async function t() {
    const response2 = await fetch(`${API_URL}/subscriber/findBySystemField?whatsapp_phone=905333666213`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${config.manychatApiToken}`,
      }
    });
    console.log("whatsapp_phone:", await response2.json());

    const response3 = await fetch(`${API_URL}/subscriber/findBySystemField?phone=905333666213`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${config.manychatApiToken}`,
      }
    });
    console.log("phone:", await response3.json());
}
t();
