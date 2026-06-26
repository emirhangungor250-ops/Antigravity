const https = require('https');

function callProxy(targetUrl, method, payloadStr = null, headersStr = null) {
  return new Promise((resolve, reject) => {
    const url = new URL(process.env.PHONE_PROXY_URL || '<PHONE_PROXY_URL>');
    url.searchParams.append('url', targetUrl);
    url.searchParams.append('method', method);
    if (headersStr) url.searchParams.append('headers', headersStr);
    if (payloadStr) url.searchParams.append('payload', encodeURIComponent(payloadStr));

    const options = {
      hostname: url.hostname,
      port: 443,
      path: url.pathname + url.search,
      method: 'GET'
    };

    const req = https.request(options, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        try {
          resolve({ status: res.statusCode, body: JSON.parse(data) });
        } catch (e) {
          resolve({ status: res.statusCode, body: data });
        }
      });
    });
    
    req.on('error', reject);
    req.end();
  });
}

const railwayUrl = 'https://<RAILWAY_SERVICE_URL>';
const headers = JSON.stringify({
  'Content-Type': 'application/json'
});

async function runTestB() {
  const transactionId = 99902;
  const firstName = 'TestUser';
  const lastName = 'TestB';
  const email = 'testb@example.com';
  const phone = '+905333666213';

  console.log('Sending new-paid-member...');
  const res1 = await callProxy(`${railwayUrl}/webhook/new-paid-member`, 'POST', JSON.stringify({
    transaction_id: transactionId,
    first_name: firstName,
    last_name: lastName,
    email: email
  }), headers);
  console.log('new-paid-member Response:', res1.status, res1.body);

  // Wait a bit to simulate real world and avoid race condition
  await new Promise(r => setTimeout(r, 2000));

  console.log('Sending membership-questions...');
  const res2 = await callProxy(`${railwayUrl}/webhook/membership-questions`, 'POST', JSON.stringify({
    transaction_id: transactionId,
    first_name: firstName,
    last_name: lastName,
    answer_1: phone
  }), headers);
  console.log('membership-questions Response:', res2.status, res2.body);
}

runTestB();
