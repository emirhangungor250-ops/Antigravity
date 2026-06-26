const { config } = require('../config/env');
const log = require('../utils/logger');

// In-memory dedup — aynı subscriber'a 30dk içinde mükerrer eskalasyon mailı atma
const ESCALATION_DEDUP_WINDOW_MS = 30 * 60 * 1000;
const _lastEscalationAt = new Map();

function _shouldDedupEscalation(subscriberId) {
  if (!subscriberId) return false;
  const last = _lastEscalationAt.get(subscriberId);
  if (!last) return false;
  return (Date.now() - last) < ESCALATION_DEDUP_WINDOW_MS;
}

function _markEscalationSent(subscriberId) {
  if (!subscriberId) return;
  _lastEscalationAt.set(subscriberId, Date.now());
  // Bellek koruması: 1000 üstü kayıt olursa en eskileri at
  if (_lastEscalationAt.size > 1000) {
    const cutoff = Date.now() - ESCALATION_DEDUP_WINDOW_MS;
    for (const [id, ts] of _lastEscalationAt) {
      if (ts < cutoff) _lastEscalationAt.delete(id);
    }
  }
}

// Resend ile admin'e alarm bildirimi — sadece ana mail fail olduğunda
async function notifyAdminOfFailure(subscriberId, originalError) {
  if (!config.adminNotifyEmail || !config.resendApiKey) return;
  try {
    const fromAddress = `WhatsApp Asistan <${config.escalationEmail}>`;
    const response = await fetch('https://api.resend.com/emails', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${config.resendApiKey}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        from: fromAddress,
        to: [config.adminNotifyEmail],
        subject: '[ALARM] Escalation email gönderilemedi',
        text: `Subscriber: ${subscriberId}\n\nOriginal error:\n${originalError}`
      })
    });
    if (!response.ok) {
      const txt = await response.text();
      log.error(`[escalation] Admin alarm fallback de başarısız: HTTP ${response.status} - ${txt}`);
    } else {
      log.info(`[escalation] Admin alarm bildirimi gönderildi: ${config.adminNotifyEmail}`);
    }
  } catch (err) {
    log.error(`[escalation] Admin alarm fallback exception: ${err.message}`);
  }
}

// XSS korumasi icin HTML escape fonksiyonu
function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

/**
 * WhatsApp Asistanı Eskalasyon Maili Gönderir
 * @param {Object} params
 * @param {string} params.type - "hassas_konu" veya "bilinmeyen_soru"
 * @param {string} params.subscriberId - ManyChat subscriber ID
 * @param {string} [params.phoneNumber] - Telefon numarası
 * @param {string} params.reason - Eskalasyon sebebi (LLM açıklaması)
 * @param {Array} params.recentMessages - Son 5 mesaj ({ role, content })
 */
async function sendEscalationEmail({ type, subscriberId, phoneNumber, reason, recentMessages }) {
  // Test guard: regression test'leri (test-runner-* veya sim-* subscriber ID'leri) gerçek mail atmasın
  if (subscriberId && /^(test-runner|sim-)/.test(String(subscriberId))) {
    log.info(`[escalation] test_guard_skip — ${subscriberId} için mail atılmadı (${type}): ${reason}`);
    return false;
  }

  // Simülasyon modu env flag'i
  if (process.env.SIMULATION_MODE === 'true') {
    log.info(`[escalation] SIMULATION_MODE — mail gönderilmedi: ${type} (subscriber=${subscriberId})`);
    return false;
  }

  if (!config.resendApiKey) {
    log.warn(`[escalation] RESEND_API_KEY yok — email gönderilmedi: ${type}`);
    return false;
  }

  // 30 dakikalık dedup — aynı subscriber'a mükerrer mail atma
  if (_shouldDedupEscalation(subscriberId)) {
    log.info(`[escalation] dedup_skip — subscriber ${subscriberId} son 30 dakikada zaten eskale edildi (${type})`);
    return false;
  }

  const typeLabels = {
    rezervasyon_talebi: 'REZERVASYON',
    iptal_iade: 'İPTAL/İADE',
    sikayet: 'ŞİKAYET',
    bilinmeyen_soru: 'BİLİNMEYEN',
  };
  const escalationTypeStr = typeLabels[type] || String(type).toUpperCase();
  const shortReason = reason.length > 60 ? reason.substring(0, 60) + '...' : reason;
  const subject = `[${escalationTypeStr}] ${config.businessName} WhatsApp - ${shortReason}`;
  const toEmail = config.escalationEmail;
  const fromAddress = `${config.businessName} Asistan <${process.env.RESEND_FROM_EMAIL || toEmail}>`;

  // İstanbul saati ile zaman damgası
  const dateStr = new Date().toLocaleString('tr-TR', { timeZone: 'Europe/Istanbul' });

  // Son mesajları HTML'e çevir
  let messagesHtml = '';
  if (recentMessages && recentMessages.length > 0) {
    messagesHtml = recentMessages.map(m => {
      const roleName = m.role === 'user' ? 'Kullanıcı' : 'Asistan';
      const color = m.role === 'user' ? '#2563EB' : '#16A34A';
      return `<div style="margin-bottom: 12px;">
        <strong style="color: ${color};">${roleName}:</strong>
        <div style="margin-top: 4px; background: #f9fafb; padding: 10px; border-radius: 6px; border: 1px solid #e5e7eb; white-space: pre-wrap; font-family: system-ui, sans-serif; font-size: 14px;">${escapeHtml(m.content)}</div>
      </div>`;
    }).join('');
  } else {
    messagesHtml = '<p style="color: #6b7280; font-style: italic;">Son konuşma bulunamadı.</p>';
  }

  const html = `
    <div style="font-family: system-ui, -apple-system, sans-serif; color: #111827; max-width: 600px; margin: 0 auto; border: 1px solid #e5e7eb; border-radius: 8px; padding: 24px;">
      <h2 style="margin-top: 0; color: #dc2626; border-bottom: 2px solid #fee2e2; padding-bottom: 12px;">🚨 WhatsApp Eskalasyon Bildirimi</h2>
      
      <table border="0" cellpadding="10" cellspacing="0" style="width: 100%; border-collapse: collapse; margin-bottom: 24px;">
        <tr>
          <td style="background: #f3f4f6; width: 120px; border-bottom: 1px solid #e5e7eb;"><strong>Tarih (TSİ)</strong></td>
          <td style="border-bottom: 1px solid #e5e7eb;">${dateStr}</td>
        </tr>
        <tr>
          <td style="background: #f3f4f6; border-bottom: 1px solid #e5e7eb;"><strong>Kişi Bilgileri</strong></td>
          <td style="border-bottom: 1px solid #e5e7eb;">
            Telefon: ${escapeHtml(phoneNumber || 'Bilinmiyor')}<br>
            Subscriber ID: ${escapeHtml(subscriberId)}
          </td>
        </tr>
        <tr>
          <td style="background: #f3f4f6; border-bottom: 1px solid #e5e7eb;"><strong>Kategori</strong></td>
          <td style="border-bottom: 1px solid #e5e7eb;">
            <span style="background: #fee2e2; color: #991b1b; padding: 2px 8px; border-radius: 9999px; font-size: 13px; font-weight: 500;">
              ${escapeHtml(type)}
            </span>
          </td>
        </tr>
        <tr>
          <td style="background: #f3f4f6; border-bottom: 1px solid #e5e7eb;"><strong>Sebep</strong></td>
          <td style="border-bottom: 1px solid #e5e7eb;">${escapeHtml(reason)}</td>
        </tr>
      </table>

      <h3 style="margin-top: 0; margin-bottom: 16px; font-size: 18px;">Son Konuşma Özeti</h3>
      <div style="background: #ffffff;">
        ${messagesHtml}
      </div>
    </div>
  `;

  try {
    const response = await fetch('https://api.resend.com/emails', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${config.resendApiKey}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        from: fromAddress,
        to: [toEmail],
        subject: subject,
        html: html
      })
    });

    if (!response.ok) {
      const errorText = await response.text();
      log.error(`[escalation] Resend API hatası: HTTP ${response.status} - ${errorText}`);
      await notifyAdminOfFailure(subscriberId, `HTTP ${response.status} - ${errorText}`);
      return false;
    }

    const data = await response.json();
    log.info(`[escalation] E-mail başarıyla gönderildi: ${type} (${data.id})`);
    _markEscalationSent(subscriberId);
    return true;

  } catch (error) {
    log.error(`[escalation] Beklenmeyen hata: ${error.message}`, error);
    await notifyAdminOfFailure(subscriberId, error.message);
    return false; // Ana akışı bozmamak için false dönüyoruz
  }
}

module.exports = {
  sendEscalationEmail
};
