const { config } = require('./config/env');
const API_URL = "https://api.manychat.com/fb";
async function t() {
    const phones = ['+905333666213', '+5333666213', '5333666213', '%2B905333666213'];
    for (const ph of phones) {
      const response3 = await fetch(`${API_URL}/subscriber/findBySystemField?phone=${ph}`, {
        method: 'GET',
        headers: { 'Authorization': `Bearer ${config.manychatApiToken}` }
      });
      console.log(`phone ${ph}:`, await response3.json());
    }
}
t();
