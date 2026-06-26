const fetch = require('node-fetch');
const token = process.env.MANYCHAT_API_TOKEN || '<MANYCHAT_API_TOKEN>';
const TEST_PHONE = process.env.TEST_PHONE || '<TEST_PHONE>';
const API_URL = "https://api.manychat.com/fb";

async function test() {
    const headers = {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
    };

    const endpoints = [
        `${API_URL}/subscriber/findBySystemField?phone=%2B${TEST_PHONE}`,
        `${API_URL}/subscriber/findBySystemField?whatsapp_phone=%2B${TEST_PHONE}`,
        `${API_URL}/subscriber/findBySystemField?phone=${TEST_PHONE}`,
        `${API_URL}/subscriber/findBySystemField?whatsapp_phone=${TEST_PHONE}`
    ];

    for (const url of endpoints) {
        console.log("Testing:", url);
        const res = await fetch(url, { headers });
        const data = await res.json();
        console.log(JSON.stringify(data));
    }
}
test();
