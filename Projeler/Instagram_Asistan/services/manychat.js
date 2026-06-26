// services/manychat.js
const { config } = require('../config/env');
const log = require('../utils/logger');
const fetch = require('node-fetch');

const API_URL = 'https://api.manychat.com/fb';
const headers = {
  'Authorization': `Bearer ${config.manychatApiToken}`,
  'Content-Type': 'application/json'
};

function _isTestSubscriber(subscriberId) {
  if (config.simulationMode) return true;
  return subscriberId && /^(test-runner|sim-)/.test(String(subscriberId));
}

async function setCustomField(subscriberId, fieldId, value) {
  if (_isTestSubscriber(subscriberId)) {
    log.info(`[manychat] test/simulation — setCustomField bypass.`, { subscriberId });
    return true;
  }

  const payload = {
    subscriber_id: subscriberId,
    field_id: parseInt(fieldId),
    field_value: String(value)
  };

  try {
    const response = await fetch(`${API_URL}/subscriber/setCustomField`, {
      method: 'POST',
      headers,
      body: JSON.stringify(payload)
    });
    const data = await response.json();
    if (data.status !== 'success') {
      log.warn(`[manychat] setCustomField başarısız/uyarı`, { data });
      return false;
    }
    return true;
  } catch (error) {
    log.error(`[manychat] setCustomField hatası: ${error.message}`, error);
    return false;
  }
}

async function sendFlow(subscriberId, flowId) {
  if (_isTestSubscriber(subscriberId)) {
    log.info(`[manychat] test/simulation — sendFlow bypass.`, { subscriberId });
    return { status: 'success', bypass: true };
  }

  const payload = { subscriber_id: subscriberId, flow_ns: flowId };

  try {
    const response = await fetch(`${API_URL}/sending/sendFlow`, {
      method: 'POST',
      headers,
      body: JSON.stringify(payload)
    });
    const data = await response.json();
    if (data.status !== 'success') {
      log.error(`[manychat] sendFlow başarısız.`, { data });
      throw new Error(`sendFlow hatası: ${JSON.stringify(data)}`);
    }
    return data;
  } catch (error) {
    log.error(`[manychat] sendFlow hatası: ${error.message}`, error);
    throw error;
  }
}

// 4 Product Card variant'ı. Variant adı → flow ID eşleme.
const PRODUCT_CARD_FLOWS = {
  'otomasyonlar': () => config.manychatProductCardsFlowId,        // 5 ana otomasyon
  'basari_izlenme': () => config.manychatBasariIzlenmeFlowId,      // YouTube/AI influencer izlenme başarıları
  'basari_gelir': () => config.manychatBasariGelirFlowId,          // Bireysel gelir/satış başarıları
  'basari_isletme': () => config.manychatBasariIsletmeFlowId       // İşletme otomasyon başarıları
};

async function sendProductCards(subscriberId, variant = 'otomasyonlar') {
  const resolver = PRODUCT_CARD_FLOWS[variant];
  if (!resolver) {
    log.warn(`[manychat] geçersiz product card variant: ${variant}`);
    return { status: 'skipped', reason: 'unknown_variant' };
  }
  const flowId = resolver();
  if (!flowId) {
    log.warn(`[manychat] variant ${variant} için flow ID env'de tanımlı değil`);
    return { status: 'skipped', reason: 'no_flow_id' };
  }
  log.info(`[manychat] product_cards tetikleniyor`, { subscriberId, variant, flowId });
  return await sendFlow(subscriberId, flowId);
}

module.exports = { setCustomField, sendFlow, sendProductCards, PRODUCT_CARD_FLOWS };
