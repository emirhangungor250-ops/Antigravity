const https = require('https');

const postData = JSON.stringify({
  transaction_id: 'test_txn_' + Date.now(),
  first_name: 'Test',
  last_name: 'User',
  email: 'test@example.com',
  date: '2026-04-23'
});

const options = {
  hostname: '151.101.2.15', // Railway Proxy IP
  port: 443,
  path: '/webhook/new-paid-member',
  method: 'POST',
  headers: {
    'Host': '<RAILWAY_SERVICE_URL>',
    'Content-Type': 'application/json',
    'Content-Length': Buffer.byteLength(postData)
  },
  rejectUnauthorized: false // Bypass SSL cert validation mismatch against IP
};

const req = https.request(options, (res) => {
  console.log(`STATUS: ${res.statusCode}`);
  res.setEncoding('utf8');
  res.on('data', (chunk) => {
    console.log(`BODY: ${chunk}`);
  });
});

req.on('error', (e) => {
  console.error(`problem with request: ${e.message}`);
});

req.write(postData);
req.end();
