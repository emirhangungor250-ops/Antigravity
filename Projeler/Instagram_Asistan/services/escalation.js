// services/escalation.js
// IG eskalasyon mail — yöneticiye (<ADMIN_EMAIL>).
// 3 kategori: hassas_konu, bilinmeyen_soru, b2b_uygun.
const fetch = require('node-fetch');
const { config } = require('../config/env');
const log = require('../utils/logger');

const DEDUP_WINDOW_MS = 30 * 60 * 1000;
const _lastEscalationAt = new Map();

function _shouldDedup(subscriberId, type) {
  const key = `${subscriberId}::${type}`;
  const last = _lastEscalationAt.get(key);
  if (!last) return false;
  return (Date.now() - last) < DEDUP_WINDOW_MS;
}

function _markSent(subscriberId, type) {
  const key = `${subscriberId}::${type}`;
  _lastEscalationAt.set(key, Date.now());
  if (_lastEscalationAt.size > 2000) {
    const cutoff = Date.now() - DEDUP_WINDOW_MS;
    for (const [k, ts] of _lastEscalationAt) {
      if (ts < cutoff) _lastEscalationAt.delete(k);
    }
  }
}

function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

const TYPE_TO_PREFIX = {
  hassas_konu: 'IG-HASSAS',
  bilinmeyen_soru: 'IG-BILINMEYEN',
  b2b_uygun: 'IG-B2B-UYGUN'
};

const TYPE_TO_LABEL = {
  hassas_konu: 'Hassas Konu',
  bilinmeyen_soru: 'KB Boşluğu / Bilinmeyen Soru',
  b2b_uygun: 'B2B Uygun Görülen Lead'
};

/**
 * @param {object} params
 * @param {'hassas_konu'|'bilinmeyen_soru'|'b2b_uygun'} params.type
 * @param {string} params.subscriberId
 * @param {string} [params.igUsername]
 * @param {string} params.reason
 * @param {Array<{role,content}>} params.recentMessages
 * @returns {Promise<boolean>}
 */
async function sendEscalationEmail({ type, subscriberId, igUsername, reason, recentMessages }) {
  if (subscriberId && /^(test-runner|sim-)/.test(String(subscriberId))) {
    log.info(`[escalation] test_guard_skip — ${subscriberId} için mail atılmadı (${type})`);
    return false;
  }
  if (config.simulationMode) {
    log.info(`[escalation] SIMULATION_MODE — mail bypass: ${type} subscriber=${subscriberId}`);
    return false;
  }
  if (!config.resendApiKey) {
    log.warn(`[escalation] RESEND_API_KEY yok — mail atılmadı (${type})`);
    return false;
  }
  if (!TYPE_TO_PREFIX[type]) {
    log.warn(`[escalation] bilinmeyen type: ${type}`);
    return false;
  }
  if (_shouldDedup(subscriberId, type)) {
    log.info(`[escalation] dedup_skip — ${subscriberId} (${type}) son 30dk içinde zaten gönderildi`);
    return false;
  }

  const prefix = TYPE_TO_PREFIX[type];
  const shortReason = reason && reason.length > 60 ? reason.substring(0, 60) + '...' : (reason || '-');
  const subject = `[${prefix}] Instagram Eskalasyon — ${shortReason}`;
  const toEmail = config.escalationEmail;
  const fromAddress = `Instagram Asistan <${toEmail}>`;

  const dateStr = new Date().toLocaleString('tr-TR', { timeZone: 'Europe/Istanbul' });
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
    <div style="font-family: system-ui, sans-serif; color: #111827; max-width: 600px; margin: 0 auto; border: 1px solid #e5e7eb; border-radius: 8px; padding: 24px;">
      <h2 style="margin-top: 0; color: #dc2626; border-bottom: 2px solid #fee2e2; padding-bottom: 12px;">📸 Instagram Eskalasyon</h2>
      <table border="0" cellpadding="10" cellspacing="0" style="width: 100%; border-collapse: collapse; margin-bottom: 24px;">
        <tr><td style="background: #f3f4f6; width: 140px; border-bottom: 1px solid #e5e7eb;"><strong>Tarih (TSİ)</strong></td><td style="border-bottom: 1px solid #e5e7eb;">${dateStr}</td></tr>
        <tr><td style="background: #f3f4f6; border-bottom: 1px solid #e5e7eb;"><strong>Kullanıcı</strong></td><td style="border-bottom: 1px solid #e5e7eb;">
          IG: @${escapeHtml(igUsername || 'bilinmiyor')}<br>
          Subscriber ID: ${escapeHtml(subscriberId)}
        </td></tr>
        <tr><td style="background: #f3f4f6; border-bottom: 1px solid #e5e7eb;"><strong>Kategori</strong></td><td style="border-bottom: 1px solid #e5e7eb;">
          <span style="background: #fee2e2; color: #991b1b; padding: 2px 8px; border-radius: 9999px; font-size: 13px; font-weight: 500;">${escapeHtml(TYPE_TO_LABEL[type])}</span>
        </td></tr>
        <tr><td style="background: #f3f4f6; border-bottom: 1px solid #e5e7eb;"><strong>Sebep</strong></td><td style="border-bottom: 1px solid #e5e7eb;">${escapeHtml(reason || '-')}</td></tr>
      </table>
      <h3 style="margin-top: 0; margin-bottom: 16px; font-size: 18px;">Son Konuşma</h3>
      <div>${messagesHtml}</div>
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
        subject,
        html
      })
    });
    if (!response.ok) {
      const text = await response.text();
      log.error(`[escalation] Resend hatası: HTTP ${response.status} - ${text}`);
      return false;
    }
    const data = await response.json();
    log.info(`[escalation] mail gönderildi: ${type} (${data.id})`);
    _markSent(subscriberId, type);
    return true;
  } catch (error) {
    log.error(`[escalation] Beklenmeyen hata: ${error.message}`, error);
    return false;
  }
}

module.exports = { sendEscalationEmail };
