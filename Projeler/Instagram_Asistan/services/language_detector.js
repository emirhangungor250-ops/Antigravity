// services/language_detector.js
// Instagram'da Türkçe varsayılan; sadece açık İngilizce/Almanca/Arapça sezgisinde değiştir.
// WhatsApp Asistan Groq llama-3.3-70b kullanıyordu; IG'de daha hafif heuristik yeterli.

const TURKISH_HINTS = /[çğıİöşüÇĞÖŞÜ]|^(merhaba|selam|naber|nasılsın|teşekkür|ben|bir|şu|bu|var|yok)\b/i;
const ENGLISH_HINTS = /^(hi|hello|hey|how|what|when|where|why|i|the|a|is|are)\b/i;

function detectLanguage(text) {
  if (!text || typeof text !== 'string' || text.trim() === '') return 'tr';
  if (TURKISH_HINTS.test(text)) return 'tr';
  if (ENGLISH_HINTS.test(text)) return 'en';
  return 'tr';
}

module.exports = { detectLanguage };
