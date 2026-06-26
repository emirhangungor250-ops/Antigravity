const { config } = require('./config/env');
const API_URL = "https://api.manychat.com/fb";
async function t() {
    const endpoints = [
      `/subscriber/getInfoByWhatsApp?whatsapp_phone=905333666213`,
      `/subscriber/findBySystemField?whatsapp_phone=905333666213`,
      `/subscriber/findByWhatsApp?phone=905333666213`
    ];
    for (const ep of endpoints) {
      const response = await fetch(`${API_URL}${ep}`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${config.manychatApiToken}`,
        }
      });
      console.log(ep, ":", await response.json());
    }
}
t();
