const { config } = require('./config/env');
async function test() {
   const res = await fetch('https://api.manychat.com/fb/page/getSystemFields', {
      headers: { 'Authorization': `Bearer ${config.manychatApiToken}` }
   });
   console.log("System Fields:", await res.text());
}
test();
