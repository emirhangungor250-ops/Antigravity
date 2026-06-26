// ============================================================
// services/resend.js — Email Fallback (Resend API)
// ============================================================
// Telefon numarası geçersiz olan üyeler için email onboarding.
// Resend kurulu değilse sessizce atlanır (opsiyonel servis).
// ============================================================

const { config } = require('../config/env');
const log = require('../utils/logger');

// Geçici hata (timeout/abort/429/5xx) durumunda inline retry.
// Cron zaten retryOn429 ile sarmalıyor; bu sadece cron-dışı çağrılar
// (server.js webhook fallback path'i) için güvence katmanı.
async function sendWithRetry(fetchFn, label, attempts = 3) {
  const delays = [1000, 3000];
  let lastErr;
  for (let i = 0; i < attempts; i++) {
    try {
      const response = await fetchFn();
      if (response.ok) return response;
      // 5xx veya 429 → retry; 4xx → kalıcı, hemen fırlat
      if (response.status >= 500 || response.status === 429) {
        const text = await response.text();
        lastErr = new Error(`Resend HTTP ${response.status}: ${text}`);
        lastErr.status = response.status;
      } else {
        const text = await response.text();
        const err = new Error(`Resend HTTP ${response.status}: ${text}`);
        err.status = response.status;
        throw err;
      }
    } catch (err) {
      lastErr = err;
      // Permanent hata (4xx) → retry etme
      if (err.status && err.status >= 400 && err.status < 500 && err.status !== 429) {
        throw err;
      }
      // Timeout/abort/network → retry
      const isTransient = err.name === 'AbortError' || err.name === 'TimeoutError'
        || /timeout|aborted|network|ECONNRESET|ETIMEDOUT/i.test(err.message || '')
        || err.status === 429 || (err.status >= 500 && err.status < 600);
      if (!isTransient) throw err;
    }
    if (i < attempts - 1) {
      const wait = delays[i] || 5000;
      log.warn(`[resend:retry] ${label} — ${wait}ms backoff (deneme ${i + 1}/${attempts})`);
      await new Promise(r => setTimeout(r, wait));
    }
  }
  throw lastErr;
}

// Fix: XSS koruması — kullanıcı adlarında <script> vb. engelleme
function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

async function sendOnboardingEmail(toEmail, firstName, dayNumber) {
  if (!config.resendApiKey) {
    log.warn(`[resend] API key yok — email gönderilmedi: ${toEmail} (Gün ${dayNumber})`);
    return null;
  }

  const emailContent = getEmailContent(firstName, dayNumber);
  let html = emailContent.html;

  // Day 0: WhatsApp CTA butonu enjekte et (üye isterse WA'ya geçebilsin)
  if (dayNumber === 0 && config.waBusinessPhone) {
    html = html.replace('<!-- WA_CTA_PLACEHOLDER -->', buildWaCta(config.waBusinessPhone));
    log.info(`[resend] Day 0: WA CTA butonu enjekte edildi`);
  } else {
    html = html.replace('<!-- WA_CTA_PLACEHOLDER -->', '');
  }

  try {
    const response = await sendWithRetry(() => fetch('https://api.resend.com/emails', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${config.resendApiKey}`,
        'Content-Type': 'application/json'
      },
      signal: AbortSignal.timeout(10000),
      body: JSON.stringify({
        from: config.resendFromEmail,
        to: [toEmail],
        subject: emailContent.subject,
        html: html
      })
    }), `EMAIL[day${dayNumber}]`);

    const data = await response.json();
    log.info(`[resend] Email gönderildi: ${toEmail} — Gün ${dayNumber} (${data.id})`);
    return data;

  } catch (error) {
    log.error(`[resend] Email hatası: ${error.message}`, error.stack);
    throw error;
  }
}

// ============================================================
// Rich HTML Email Template Builder
// ============================================================
// Eski n8n workflow'dan birebir alınan HTML yapısı:
// - Beyaz kart (600px max-width, 12px border-radius, #f3f3f3 bg)
// - system-ui font ailesi
// - Tıklanabilir Cloudinary thumbnail → YouTube Short
// - Footer linkleri (güne göre değişen)
// - Disclaimer footer
// - <!-- WA_CTA_PLACEHOLDER --> (hibrit fallback için)
// ============================================================

function buildEmailHtml(firstName, bodyText, videoUrl, thumbnailUrl, footerHtml) {
  return `<!DOCTYPE html>
<html lang="tr">
<head>
  <meta charset="UTF-8">
  <title>[TOPLULUK ADI]</title>
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="margin:0; padding:0; background-color:#f3f3f3;">
  <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="background-color:#f3f3f3;">
    <tr>
      <td align="center" style="padding:24px 12px;">
        <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="max-width:600px; background-color:#ffffff; border-radius:12px; overflow:hidden;">
          <!-- WA_CTA_PLACEHOLDER -->
          <tr>
            <td style="padding:20px 24px 8px 24px; font-family:system-ui,-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif; font-size:20px; font-weight:700; color:#111827;">
              Merhaba ${escapeHtml(firstName)} 👋
            </td>
          </tr>
          <tr>
            <td style="padding:0 24px 16px 24px; font-family:system-ui,-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif; font-size:15px; line-height:1.7; color:#111827;">
              ${bodyText}
            </td>
          </tr>
          <tr>
            <td align="center" style="padding:0 24px 12px 24px;">
              <a href="${videoUrl}" target="_blank" style="text-decoration:none; border:0; display:inline-block;">
                <img src="${thumbnailUrl}"
                     alt="Videoyu izle"
                     style="display:block; width:100%; max-width:552px; height:auto; border-radius:12px; border:0; outline:none; text-decoration:none;">
              </a>
            </td>
          </tr>
          <tr>
            <td style="padding:0 24px 20px 24px; font-family:system-ui,-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif; font-size:13px; line-height:1.6; color:#374151;">
              ${footerHtml}
            </td>
          </tr>
          <tr>
            <td style="padding:12px 24px 20px 24px; font-family:system-ui,-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif; font-size:11px; line-height:1.4; color:#9CA3AF; text-align:center;">
              Bu e-mail [TOPLULUK ADI] topluluğuna kaydolduğun için gönderildi.
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>`;
}

function getEmailContent(firstName, dayNumber) {
  // Yeni YouTube Short linkleri
  // TODO: 7 günlük drip serinizin video linklerini buraya girin (gün -> URL).
  const VIDEOS = {
    0: '[VIDEO_URL_GUN_0]',
    1: '[VIDEO_URL_GUN_1]',
    2: '[VIDEO_URL_GUN_2]',
    3: '[VIDEO_URL_GUN_3]',
    4: '[VIDEO_URL_GUN_4]',
    5: '[VIDEO_URL_GUN_5]',
    6: '[VIDEO_URL_GUN_6]'
  };

  // Cloudinary thumbnail'ler (mevcut — değişmedi)
  // TODO: Her gün için e-mailde gosterilecek thumbnail gorsel URL'lerini girin.
  const THUMBNAILS = {
    0: '[THUMBNAIL_URL_GUN_0]',
    1: '[THUMBNAIL_URL_GUN_1]',
    2: '[THUMBNAIL_URL_GUN_2]',
    3: '[THUMBNAIL_URL_GUN_3]',
    4: '[THUMBNAIL_URL_GUN_4]',
    5: '[THUMBNAIL_URL_GUN_5]',
    6: '[THUMBNAIL_URL_GUN_6]'
  };

  const contents = {
    0: {
      subject: `Merhaba ${escapeHtml(firstName)} - [TOPLULUK ADI]'ne Hoş Geldin`,
      body: `[TOPLULUK ADI] topluluğuna katıldığın için teşekkür ederim.
              <br>
              Senin için çok kısa bir hoş geldin videosu hazırladım.
              <br><br>
              Aşağıdaki videoya tıklayarak izleyebilirsin. 👇
              <br><br>
              Önümüzdeki 6 gün boyunca her gün sana böyle kısa bir video göndereceğim,
              <br>
              e-posta kutunu ara ara kontrol etmeyi unutma. 🚀`,
      footer: `Topluluğu incelemek istersen
              <a href="[TOPLULUK_URL]" target="_blank" style="color:#2563EB; text-decoration:underline;">buraya tıklayabilirsin</a>.`
    },
    1: {
      subject: `Gün 1`,
      body: `Bugün serinin ilk devam videosunu gönderdim.
              <br>
              Senin için yine çok kısa bir kayıt hazırladım.
              <br><br>
              Aşağıdaki videoya tıklayarak izleyebilirsin. 👇
              <br><br>
              Yarın bir e-mail daha gelecek, takipte kal. 👀`,
      footer: `Topluluğa ve uygulamasına aşağıdaki linklerden ulaşabilirsin:
              <br><br>
              Topluluk:
              <a href="[TOPLULUK_URL]" target="_blank" style="color:#2563EB; text-decoration:underline;">[TOPLULUK ADI]</a>
              <br>
              iOS uygulaması:
              <a href="[IOS_APP_URL]" target="_blank" style="color:#2563EB; text-decoration:underline;">App Store</a>
              <br>
              Android uygulaması:
              <a href="[ANDROID_APP_URL]" target="_blank" style="color:#2563EB; text-decoration:underline;">Google Play</a>`
    },
    2: {
      subject: `Gün 2`,
      body: `Bugün de serinin bir sonraki videosunu gönderiyorum.
              <br>
              Her zamanki gibi kısa ve hızlı bir video hazırladım.
              <br><br>
              Aşağıdaki videoya tıklayarak izleyebilirsin. 👇
              <br><br>
              Yarın yeni bir e-mail daha alacaksın. 🔁`,
      footer: `İçerik bölümünü açmak istersen
              <a href="[TOPLULUK_ICERIK_URL]" target="_blank" style="color:#2563EB; text-decoration:underline;">buraya tıklayabilirsin</a>.`
    },
    3: {
      subject: `Gün 3`,
      body: `Serinin üçüncü videosu hazır.
              <br>
              Yine birkaç dakikalık, hızlı tüketilen bir kayıt.
              <br><br>
              Aşağıdaki videoya tıklayarak izleyebilirsin. 👇
              <br><br>
              Yarın serinin bir sonraki adımını göndereceğim. 🔜`,
      footer: `Topluluk sayfasını açmak istersen
              <a href="[TOPLULUK_URL]" target="_blank" style="color:#2563EB; text-decoration:underline;">buraya tıklayabilirsin</a>.`
    },
    4: {
      subject: `Gün 4`,
      body: `Bugün de senin için kısa bir video bıraktım.
              <br>
              Seri boyunca her gün küçük bir adım daha atıyoruz.
              <br><br>
              Aşağıdaki videoya tıklayarak izleyebilirsin. 👇
              <br><br>
              Yarın gelen e-mail'i de kaçırma. 💸`,
      footer: `Affiliate davet linkini almak için topluluğu açmak istersen
              <a href="[TOPLULUK_URL]" target="_blank" style="color:#2563EB; text-decoration:underline;">buraya tıklayabilirsin</a>.
              <br><br>
              İndirim platformu:
              <a href="[INDIRIM_PLATFORMU_URL]" target="_blank" style="color:#2563EB; text-decoration:underline;">İndirim platformu</a>`
    },
    5: {
      subject: `Gün 5`,
      body: `Serinin beşinci videosu e-posta kutuna indi.
              <br>
              Her zamanki gibi kısa tutulmuş bir kayıt.
              <br><br>
              Aşağıdaki videoya tıklayarak izleyebilirsin. 👇
              <br><br>
              Yarın son videoyu göndereceğim. ⚙️`,
      footer: `İçerikleri incelemek istersen
              <a href="[TOPLULUK_ICERIK_URL]" target="_blank" style="color:#2563EB; text-decoration:underline;">buraya tıklayabilirsin</a>.`
    },
    6: {
      subject: `Gün 6`,
      body: `Bu, serinin altıncı ve son videosu.
              <br>
              Her şey yine hızlı ve kısa bir kayıt halinde.
              <br><br>
              Aşağıdaki videoya tıklayarak izleyebilirsin. 👇
              <br><br>
              Toplulukta seni daha uzun süre görmek için sabırsızlanıyorum. 🤝`,
      footer: `Yıllık üyelik planlarını ve indirim platformunu aşağıdaki linklerden görebilirsin:
              <br><br>
              Yıllık üyelik:
              <a href="[TOPLULUK_PLANLAR_URL]" target="_blank" style="color:#2563EB; text-decoration:underline;">Üyelik Planları</a>
              <br>
              İndirim platformu:
              <a href="[INDIRIM_PLATFORMU_URL]" target="_blank" style="color:#2563EB; text-decoration:underline;">İndirim platformu</a>
              <br><br>
              Canlı yayın takvimini görmek ve etkinlikleri takvimine eklemek için
              <a href="[TOPLULUK_TAKVIM_URL]" target="_blank" style="color:#2563EB; text-decoration:underline;">buraya tıklayabilirsin</a>.`
    }
  };

  const day = contents[dayNumber] || contents[0];
  const safeDay = dayNumber in VIDEOS ? dayNumber : 0;

  return {
    subject: day.subject,
    html: buildEmailHtml(firstName, day.body, VIDEOS[safeDay], THUMBNAILS[safeDay], day.footer)
  };
}

// ============================================================
// Hibrit Fallback Email (WhatsApp CTA enjeksiyonlu)
// ============================================================
// WhatsApp teslim başarısız olduğunda gönderilen email.
// waBusinessPhone doluysa → WA CTA bloğu eklenir.
// waBusinessPhone boşsa → normal email gönderilir (graceful degradation).
// ============================================================

// Fix: Dinamik WA CTA — telefon numarası config'den alınır
function buildWaCta(waBusinessPhone) {
  return `<tr>
  <td style="padding:20px 24px 16px 24px;">
    <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="background-color:#f0fdf4; border-radius:8px; overflow:hidden;">
      <tr>
        <td style="padding:16px 20px 8px 20px; font-family:system-ui,-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif; font-size:14px; line-height:1.6; color:#166534;">
          Bu mesajları WhatsApp'tan almak istersen (önerilir) aşağıdaki butona dokun.
          <br>
          Bir şey yapmazsan, e-posta'dan almaya devam edeceksin.
        </td>
      </tr>
      <tr>
        <td align="center" style="padding:8px 20px 16px 20px;">
          <a href="https://wa.me/${waBusinessPhone}?text=Selam!%20videolar%C4%B1m%C4%B1%20buradan%20almak%20istiyorum"
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

async function sendHybridFallbackEmail(toEmail, firstName, dayNumber, waBusinessPhone) {
  if (!config.resendApiKey) {
    log.warn(`[resend] API key yok — hibrit email gönderilmedi: ${toEmail} (Gün ${dayNumber})`);
    return null;
  }

  // O günün email içeriğini al
  const emailContent = getEmailContent(firstName, dayNumber);
  let html = emailContent.html;

  // WA CTA sadece Gün 0 (hoş geldin) mailinde gösterilir.
  // Gün 1-6'da seri zaten email üzerinden ilerliyor; "WhatsApp'a geç" demek anlamsız.
  let subject;
  if (dayNumber === 0 && waBusinessPhone) {
    html = html.replace('<!-- WA_CTA_PLACEHOLDER -->', buildWaCta(waBusinessPhone));
    subject = `Sana WhatsApp'tan ulaşamadık – ${emailContent.subject}`;
    log.info(`[resend] Hibrit fallback: Gün 0 WA CTA enjekte edildi (${waBusinessPhone})`);
  } else {
    html = html.replace('<!-- WA_CTA_PLACEHOLDER -->', '');
    subject = emailContent.subject;
    log.info(`[resend] Hibrit fallback: Gün ${dayNumber} — WA CTA atlandı, normal email`);
  }

  try {
    const response = await sendWithRetry(() => fetch('https://api.resend.com/emails', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${config.resendApiKey}`,
        'Content-Type': 'application/json'
      },
      signal: AbortSignal.timeout(10000),
      body: JSON.stringify({
        from: config.resendFromEmail,
        to: [toEmail],
        subject: subject,
        html: html
      })
    }), `FALLBACK[day${dayNumber}]`);

    const data = await response.json();
    log.info(`[resend] Hibrit fallback email gönderildi: ${toEmail} — Gün ${dayNumber} (${data.id})`);
    return data;

  } catch (error) {
    log.error(`[resend] Hibrit fallback email hatası: ${error.message}`, error.stack);
    throw error;
  }
}

// ============================================================
// Admin Alert Email (Sistem Uyarıları İçin)
// ============================================================
async function sendAdminAlertEmail(subject, errorDetails) {
  if (!config.resendApiKey) {
    log.warn(`[resend] API key yok — Admin alert email gönderilmedi: ${subject}`);
    return null;
  }

  // KVKK: phone/email/token alanlarını maskele (logger ile aynı redaction layer).
  const safeDetails = log._redactDeep ? log._redactDeep(errorDetails) : errorDetails;

  const html = `
    <h2>🚨 Sistem Uyarısı</h2>
    <p><strong>Konu:</strong> ${escapeHtml(subject)}</p>
    <pre style="background: #f4f4f4; padding: 10px; border-radius: 5px; overflow-x: auto;">
${escapeHtml(JSON.stringify(safeDetails, null, 2))}
    </pre>
    <p><small>Zaman: ${new Date().toISOString()}</small></p>
  `;

  try {
    const response = await fetch('https://api.resend.com/emails', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${config.resendApiKey}`,
        'Content-Type': 'application/json'
      },
      // Faz 3 P1 #13: 10s timeout — Resend bazen yavaş yanıt veriyor
      signal: AbortSignal.timeout(10000),
      body: JSON.stringify({
        from: config.resendFromEmail,
        to: [config.adminAlertEmail || 'admin@example.com'],
        subject: `[🚨 UYARI] ${subject}`,
        html: html
      })
    });

    if (!response.ok) {
      const error = await response.text();
      throw new Error(`Resend HTTP ${response.status}: ${error}`);
    }

    const data = await response.json();
    log.info(`[resend] Admin alert email gönderildi: ${subject}`);
    return data;
  } catch (error) {
    log.error(`[resend] Admin alert email hatası: ${error.message}`, error.stack);
    return null; // Alert hatası akışı bozmamalı
  }
}

module.exports = { sendOnboardingEmail, sendHybridFallbackEmail, getEmailContent, sendAdminAlertEmail };
