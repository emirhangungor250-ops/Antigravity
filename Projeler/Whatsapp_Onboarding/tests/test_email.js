require('dotenv').config();
const { sendOnboardingEmail } = require('./services/resend');

async function testEmail() {
  try {
    console.log("Test email gönderiliyor...");
    const result = await sendOnboardingEmail(process.env.TEST_EMAIL || 'test@example.com', 'Test User', 0);
    console.log("Email gönderim sonucu:", result);
  } catch (error) {
    console.error("Hata oluştu:", error);
  }
}

testEmail();
