// HTML render test — Day 0 emailinin WA butonlu halini dosyaya yazar
process.env.RESEND_API_KEY = 'dummy';
process.env.WA_BUSINESS_PHONE = process.env.WA_BUSINESS_PHONE || '<WA_BUSINESS_PHONE>';
process.env.NOTION_API_KEY = 'dummy';
process.env.NOTION_DATABASE_ID = 'dummy';
process.env.MANYCHAT_API_TOKEN = 'dummy';
process.env.GROQ_API_KEY = 'dummy';

const { getEmailContent } = require('./services/resend');
const fs = require('fs');

// buildWaCta'yı burada tekrar tanımlayalım (export edilmiyor)
function buildWaCta(waBusinessPhone) {
  return `<tr>
  <td style="padding:0 24px 16px 24px;">
    <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="background-color:#f0fdf4; border-radius:8px; overflow:hidden;">
      <tr>
        <td style="padding:16px 20px 8px 20px; font-family:system-ui,-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif; font-size:14px; line-height:1.6; color:#166534;">
          Bu mesajları WhatsApp'tan almak istersen aşağıdaki butona dokun.
          <br>
          Bir şey yapmazsan, e-posta'dan almaya devam edeceksin.
        </td>
      </tr>
      <tr>
        <td align="center" style="padding:8px 20px 16px 20px;">
          <a href="https://wa.me/${waBusinessPhone}?text=Selam!%20AI%20Factory%20videolar%C4%B1m%C4%B1%20buradan%20almak%20istiyorum"
             target="_blank"
             style="display:inline-block; background-color:#25D366; color:#ffffff; font-family:system-ui,-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif; font-size:15px; font-weight:600; padding:12px 28px; border-radius:8px; text-decoration:none;">
            WhatsApp'tan Al
          </a>
        </td>
      </tr>
    </table>
  </td>
</tr>`;
}

const emailContent = getEmailContent('Test User', 0);
let html = emailContent.html;
html = html.replace('<!-- WA_CTA_PLACEHOLDER -->', buildWaCta(process.env.WA_BUSINESS_PHONE || '<WA_BUSINESS_PHONE>'));

fs.writeFileSync('test_day0_preview.html', html);
console.log('✅ HTML dosyası oluşturuldu: test_day0_preview.html');
console.log('Subject:', emailContent.subject);

// JSON payload for curl
const payload = {
  from: process.env.RESEND_FROM_EMAIL || 'Onboarding <onboarding@example.com>',
  to: [process.env.TEST_EMAIL || 'test@example.com'],
  subject: emailContent.subject,
  html: html
};
fs.writeFileSync('test_day0_payload.json', JSON.stringify(payload));
console.log('✅ Curl payload oluşturuldu: test_day0_payload.json');
