const { config } = require('./config/env');
const API_URL = "https://api.manychat.com/fb";
async function t() {
    const response2 = await fetch(`${API_URL}/subscriber/findByCustomField`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${config.manychatApiToken}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        field_name: "whatsapp_phone",
        field_value: "905333666213"
      })
    });
    console.log(JSON.stringify(await response2.json(), null, 2));
}
t();
