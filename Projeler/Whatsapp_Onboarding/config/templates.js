// ============================================================
// config/templates.js — ManyChat Flow ID Eşleştirmeleri
// ============================================================
// 7 günlük drip akışının her günü için bir ManyChat flow ID.
// Flow'lar ManyChat Builder'da oluşturulmuş olmalı; her flow'un ilk adımı
// ilgili WhatsApp template mesajıdır.
//
// SABLON: Flow ID'leri ve custom field ID'leri kendi ManyChat hesabınızdan
// alıp .env dosyanıza yazın (bkz. .env.example). Bu dosya değerleri env'den
// okur; env yoksa placeholder string döner (gönderim sırasında hata verir,
// böylece eksik konfig erken fark edilir).
// ============================================================

function flowId(day) {
  return process.env[`MANYCHAT_FLOW_DAY_${day}`] || `<MANYCHAT_FLOW_DAY_${day}>`;
}

const ONBOARDING_FLOWS = {
  0: { flow_id: flowId(0), template_name: 'onboarding_day_0', description: 'Hoş geldin + ilk yönlendirme' },
  1: { flow_id: flowId(1), template_name: 'onboarding_day_1', description: 'Gün 1 içeriği' },
  2: { flow_id: flowId(2), template_name: 'onboarding_day_2', description: 'Gün 2 içeriği' },
  3: { flow_id: flowId(3), template_name: 'onboarding_day_3', description: 'Gün 3 içeriği' },
  4: { flow_id: flowId(4), template_name: 'onboarding_day_4', description: 'Gün 4 içeriği' },
  5: { flow_id: flowId(5), template_name: 'onboarding_day_5', description: 'Gün 5 içeriği' },
  6: { flow_id: flowId(6), template_name: 'onboarding_day_6', description: 'Gün 6 içeriği + veda' },
};

// Field ID'leri — ManyChat custom fields. Kendi hesabınızdaki ID'lerle .env'e yazın.
const CUSTOM_FIELDS = {
  onboarding_name: process.env.MANYCHAT_FIELD_ONBOARDING_NAME || '<MANYCHAT_FIELD_ONBOARDING_NAME>',
  whatsapp_phone_text: process.env.MANYCHAT_FIELD_WHATSAPP_PHONE || '<MANYCHAT_FIELD_WHATSAPP_PHONE>',
};

module.exports = { ONBOARDING_FLOWS, CUSTOM_FIELDS };
