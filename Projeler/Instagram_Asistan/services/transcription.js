// services/transcription.js
// Ses mesajı transkripsiyon (Groq Whisper-large-v3-turbo, Türkçe).
// IG/ManyChat audio URL pattern'leri detect edilir.
const { config } = require('../config/env');
const log = require('../utils/logger');
const fetch = require('node-fetch');
const FormData = require('form-data');
const fs = require('fs');
const os = require('os');
const path = require('path');
const { pipeline } = require('stream/promises');

const AUDIO_HOST_PATTERNS = [
  'lookaside.fbsbx.com',
  'lookaside.instagram.com',
  'scontent.cdninstagram.com',
  'manybot',
  'fbcdn.net',
  '.mp4',
  '.m4a',
  '.ogg',
  '.opus',
  '.wav'
];

function isAudioUrl(text) {
  if (!text || typeof text !== 'string') return false;
  const trimmed = text.trim();
  if (!/^https?:\/\//i.test(trimmed)) return false;
  const lower = trimmed.toLowerCase();
  return AUDIO_HOST_PATTERNS.some(p => lower.includes(p)) && !isImageUrl(trimmed);
}

function isImageUrl(text) {
  if (!text || typeof text !== 'string') return false;
  const trimmed = text.trim();
  if (!/^https?:\/\//i.test(trimmed)) return false;
  return /\.(jpg|jpeg|png|webp|gif|heic)(\?|$)/i.test(trimmed);
}

async function downloadFile(url, tempFilePath) {
  const response = await fetch(url);
  if (!response.ok) throw new Error(`Dosya indirilemedi: ${response.statusText}`);
  await pipeline(response.body, fs.createWriteStream(tempFilePath));
}

async function transcribeAudio(audioUrl) {
  const tempFilePath = path.join(os.tmpdir(), `ig_audio_${Date.now()}.mp4`);
  try {
    log.info('[transcription] indir...');
    await downloadFile(audioUrl, tempFilePath);

    const form = new FormData();
    form.append('file', fs.createReadStream(tempFilePath));
    form.append('model', 'whisper-large-v3-turbo');
    form.append('language', 'tr');

    const response = await fetch('https://api.groq.com/openai/v1/audio/transcriptions', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${config.groqApiKey}`,
        ...form.getHeaders()
      },
      body: form
    });
    const data = await response.json();
    if (data.error) throw new Error(data.error.message);
    log.info('[transcription] OK', { chars: (data.text || '').length });
    return data.text || '';
  } catch (err) {
    log.error(`[transcription] hata: ${err.message}`, err);
    throw err;
  } finally {
    if (fs.existsSync(tempFilePath)) fs.unlinkSync(tempFilePath);
  }
}

module.exports = { transcribeAudio, isAudioUrl, isImageUrl };
