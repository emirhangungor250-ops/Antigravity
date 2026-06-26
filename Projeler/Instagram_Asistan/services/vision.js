// services/vision.js
// Görsel analizi — Claude Sonnet 4.6 vision (URL referansı).
const Anthropic = require('@anthropic-ai/sdk');
const { config } = require('../config/env');
const log = require('../utils/logger');

const client = new Anthropic({ apiKey: config.anthropicApiKey });

/**
 * Görseli analiz et, kısa bir özet döndür (kullanıcı mesajına ek context olarak ai_engine'e gider).
 * @param {string} imageUrl
 * @param {string} [userHint] - opsiyonel: kullanıcının görselle birlikte yazdığı kısa metin
 * @returns {Promise<string>} 2-4 cümle açıklama (TR)
 */
async function describeImage(imageUrl, userHint = '') {
  try {
    const userTextPart = userHint && userHint.length > 1
      ? `Kullanıcı şu metni de yazdı: "${userHint}". Bunu görseli yorumlarken dikkate al.`
      : 'Kullanıcı sadece görseli attı, başka metin yok.';

    const response = await client.messages.create({
      model: config.modelExpensive,
      max_tokens: 400,
      system: `Sen <KULLANICI_ADI>'in IG asistanısın. Kullanıcının attığı görseli kısa Türkçe açıklayacaksın. Amaç: asistanın bir sonraki cevabını üretirken konuyu bilmek. Spekülasyon yapma, görselde net ne varsa söyle. 2-4 cümle yeterli.`,
      messages: [{
        role: 'user',
        content: [
          { type: 'image', source: { type: 'url', url: imageUrl } },
          { type: 'text', text: userTextPart }
        ]
      }]
    });
    const text = (response.content || []).filter(b => b.type === 'text').map(b => b.text).join('\n').trim();
    log.info('[vision] OK', { chars: text.length });
    return text;
  } catch (err) {
    log.error(`[vision] describeImage hatası: ${err.message}`, err);
    return '';
  }
}

module.exports = { describeImage };
