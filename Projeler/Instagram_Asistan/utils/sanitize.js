// utils/sanitize.js
// Cevap post-process sanitizer. WhatsApp Asistan ai_engine.js'ten port.
// LLM-agnostic: regenerate callback parametrik.

const BANNED_AMOUNTS = [59, 97, 177, 197, 236, 297, 312, 497, 516, 997, 1997];

const BANNED_PHRASES = [
  { id: 'name_ece', re: /\bEce\b/, label: 'isim "Ece"' },
  { id: 'team_call', re: /\bekibimiz\s+(arayacak|d[öo]necek|seni)/i, label: '"ekibimiz arayacak/dönecek"' },
  { id: 'call_user', re: /\bseni\s+arayal[ıi]m\b/i, label: '"seni arayalım"' },
  { id: 'randevu', re: /\brandevu\s*(ayarlayal[ıi]m|alal[ıi]m|verel[ıi]m|talep|olu[şs]tural[ıi]m|verme)/i, label: '"randevu ayarlayalım"' },
  { id: 'gun_belirle', re: /g[üu]n\s+belirleyel[ıi]m/i, label: '"gün belirleyelim"' },
  { id: 'phone_meeting', re: /telefon\s+g[öo]r[üu][şs]mesi\s+(ayarlayal[ıi]m|alal[ıi]m)/i, label: '"telefon görüşmesi ayarlayalım"' },
  { id: 'randevu_sagla', re: /\brandevu\s*(ile|sa[ğg]lan|ayarlan|veril)/i, label: 'sahte "randevu ile sağlanıyor"' },
  { id: 'premium_only_automation', re: /(Premium\s*(ve\s*VIP)?'?[ae]?\s*(özel|özgü)|sadece\s+Premium|yaln[ıi]zca\s+Premium).{0,40}(otomasyon|kurulum|özellik|gelişmiş|tam otomatik|içerik|destek)/i, label: '"Premium\'a özel otomasyon"' },
  { id: 'standard_limited', re: /Standard.{0,30}(temel\s+seviyede|s[ıi]n[ıi]rl[ıi]|k[ıi]s[ıi]tl[ıi]|az[ai]lt[ıi]lm[ıi][şs]).{0,80}(Premium|geli[şs]mi[şs]|tam\s+otomatik)/i, label: 'Standard\'ın kısıtlı sunulması' },
  { id: 'cloud_phone_lie', re: /bulut\s+tabanl[ıi].{0,40}(telefon|tablet|mobil|her\s+cihaz)/i, label: '"bulut tabanlı, telefondan"' },
  { id: 'yearly_8_4', re: /(8\s+ay\s+öde|8\s+öde\s+4|8\s+ödeyip\s+4)/i, label: '"8 öde 4 bedava" (ters)' },
  { id: 'six_million', re: /(\$?6\s*milyon|6\s*milyonluk|alt[ıi]\s+milyonluk)/i, label: '"$6 milyonluk paket"' },
  { id: 'no_pkg_per_business', re: /(her\s+i[şs]letme\s+için\s+ayr[ıi]\s+üye|her\s+kanal\s+için\s+ayr[ıi]\s+üye|i?ki\s+farkl[ıi]\s+i[şs]letme\s+için\s+ayr[ıi]\s+üye)/i, label: '"her işletme için ayrı üyelik"' },
  { id: 'fake_product_sesli', re: /Sesli\s+Cevap\s+Otomasyonu/i, label: 'olmayan ürün "Sesli Cevap Otomasyonu"' },
  { id: 'fake_pkg_akil', re: /Ak[ıi]l\s+üyelik/i, label: 'olmayan paket "Akıl üyelik"' },
  { id: 'no_n8n_lie', re: /(n8n\s+(veya|ya da)?\s*(Make\.com)?\s*(gibi)?\s*[üu][çc][üu]nc[üu]\s+taraf|n8n\s+kullan[ıi]lm[ıi]yor)/i, label: '"n8n kullanılmıyor" (yanlış)' },
  { id: 'no_claude_code_lie', re: /(Claude\s*Code\s+(eğitimi\s+)?(yok|yer\s+almıyor|öğretmiyoruz))/i, label: '"Claude Code yok" (yanlış)' }
];

const ILETIM_PATTERNS = [
  /\bileti(yor|r)um\b/i,
  /\biletece[ğg]im\b/i,
  /\bilettim\b/i,
  /\bsana\s+d[öo]n[üu][şs]\s+yap[ıi]l(acak|aca[ğg][ıi]z)\b/i,
  /\b[A-ZĞÜŞİÖÇ][a-zığüşöç]+\s+sana\s+(ula[şs]acak|d[öo]necek)\b/
];

const APP_LINK_RE = /(apps\.apple\.com|play\.google\.com)/i;
const APP_INTENT_RE = /(\bapp\b|uygulama|iphone|android|mobil\b|playstore|app\s*store)/i;
// Türkçe ı/ş/ğ vb. ASCII-dışı harfler JS `\b` için non-word olduğundan
// `\bTL\b` "kısıtlı" gibi kelimelerde false positive üretiyordu. Bu yüzden
// boundary'leri Unicode-aware (Türkçe harf seti) negatif lookaround ile yapıyoruz.
const TR_W = 'A-Za-zĞÜŞİÖÇğüşıöçÂâÎî';
const TL_RE = new RegExp(
  `(?:T[üu]rk\\s+lira|(?<![${TR_W}])TL(?![${TR_W}])|(?<![${TR_W}])liras[ıi](?![${TR_W}])|(?<![${TR_W}])lira\\s+olarak|(?<![${TR_W}])liraya\\s+karş)`,
  'i'
);
const FAKE_DISCOUNT_RE = /(indirim\s+paketi\s+açıl|kampanya\s+(başl|açıl|devrede)|özel\s+fırsat|promosyon\s+devrede|milyonluk\s+(yapay zeka|paket)|\$?\s*\d+\s*milyonluk)/i;

function checkViolations(text, toolCalled, userContext = '') {
  const violations = [];

  for (const amount of BANNED_AMOUNTS) {
    const reDollarBefore = new RegExp(`\\$\\s*${amount}(?!\\d)`);
    const reDollarAfter = new RegExp(`(?<!\\d)${amount}\\s*\\$`);
    const reSpelled = new RegExp(`(?<!\\d)${amount}\\s+(dolar|usd|dolara)\\b`, 'i');
    if (reDollarBefore.test(text) || reDollarAfter.test(text) || reSpelled.test(text)) {
      violations.push({ id: `price_$${amount}`, label: `yasak fiyat $${amount}` });
    }
  }

  for (const p of BANNED_PHRASES) {
    if (p.re.test(text)) violations.push({ id: p.id, label: p.label });
  }

  if (/ — /.test(text) || /(\n|^)—\s/.test(text) || /:\s*—/.test(text)) {
    violations.push({ id: 'em_dash', label: 'em-dash karakteri' });
  }

  const hasIletim = ILETIM_PATTERNS.some(re => re.test(text));
  if (hasIletim && !toolCalled) {
    violations.push({ id: 'iletim_without_tool', label: '"iletirim" cümlesi tool çağrısı olmadan' });
  }

  const aiFactoryMention = /(<TOPLULUK_ADI>|topluluk|sağ\s+üstteki\s+mesajlar|eğitim)/i.test(text);
  const hasUrl = /topluluk\.com\/yapay-zeka-factory/i.test(text);
  if (aiFactoryMention && !hasUrl) {
    violations.push({ id: 'mention_without_url', label: '<TOPLULUK_ADI>/topluluk/eğitim URL eksik' });
  }

  if (APP_LINK_RE.test(text) && !APP_INTENT_RE.test(userContext)) {
    violations.push({ id: 'app_link_unprompted', label: 'app linki kullanıcı sormadan' });
  }

  if (TL_RE.test(text)) {
    violations.push({ id: 'tl_currency', label: 'TL/lira bahsi (USD sabit)' });
  }

  if (FAKE_DISCOUNT_RE.test(text)) {
    violations.push({ id: 'fake_discount', label: 'uydurma indirim/kampanya' });
  }

  return violations;
}

function detectPriorIletim(history) {
  return history
    .filter(m => m.role === 'assistant')
    .some(m => /<KULLANICI_ADI>'?a\s+(ileti|ilettim)/i.test(m.content || ''));
}

function hasIletimSentence(text) {
  return ILETIM_PATTERNS.some(re => re.test(text));
}

function applyHardFallback(violations, currentResponse, userContext) {
  const criticalIds = new Set(violations.map(v => v.id));

  if (criticalIds.has('tl_currency') && /(TL|lira|t[üu]rk\s+para|kur|d[öo]viz)/i.test(userContext)) {
    return {
      response: 'Fiyatlarımız USD olarak sabit: Standard $39/ay, Premium $129/ay, VIP $1.499/ay. Ödeme USD olarak alınır, banka kurun üzerinden hesaplanır.',
      kind: 'tl_currency'
    };
  }
  if (criticalIds.has('fake_discount')) {
    return {
      response: 'Sabit kampanya veya indirim uygulamıyoruz. Yıllık ödemede 4 öde 8 bedava avantajı var ve JoinSecret üzerinden ekstra indirimli yıllık paket sunuyoruz: https://main.joinsecret.com/',
      kind: 'fake_discount'
    };
  }
  if (criticalIds.has('name_ece')) {
    return {
      response: '<TOPLULUK_ADI> ekibinden <KULLANICI_ADI> seninle ilgilenir. Premium veya VIP üyelikle ilgileniyorsan iletişim formunu doldur: <JOTFORM_URL>',
      kind: 'name_ece'
    };
  }
  if (criticalIds.has('mention_without_url')) {
    const ctxLower = (userContext + ' ' + currentResponse).toLowerCase();
    let appendUrl = 'https://www.topluluk.com/yapay-zeka-factory';
    if (/(kayıt|paket|fiyat|üye ol|join|register|nereden|abone)/i.test(ctxLower)) {
      appendUrl = 'https://www.topluluk.com/yapay-zeka-factory/plans';
    } else if (/(buradan başla|eğitim|eğitim|video|n8n|antigravity|nereden başla)/i.test(ctxLower)) {
      appendUrl = 'https://www.topluluk.com/yapay-zeka-factory/eğitim';
    }
    return {
      response: currentResponse.trimEnd() + ` ${appendUrl}`,
      kind: 'mention_without_url'
    };
  }
  return null;
}

/**
 * Tam sanitize pipeline: violation check + retry + hard fallback.
 * @param {object} opts
 * @param {string} opts.response - LLM cevabı
 * @param {boolean} opts.toolCalled - eskalasyon tool çağrıldı mı
 * @param {string} opts.userContext - son user mesajları birleşik
 * @param {Array} opts.history - konuşma geçmişi
 * @param {Function} opts.regenerateFn - async (violations) => string; retry için
 * @param {Function} opts.logger - log obj (info/warn/error)
 * @returns {Promise<{ response: string, sanitized: boolean, fallback: ?string }>}
 */
async function run({ response, toolCalled, userContext, history = [], regenerateFn, logger }) {
  const log = logger || console;
  let aiResponse = response;
  let sanitized = false;
  let fallback = null;

  if (detectPriorIletim(history) && hasIletimSentence(aiResponse)) {
    log.warn?.('[sanitize] re_escalation_guard — sabit cevap');
    return {
      response: "Bu konuyu daha önce <KULLANICI_ADI>'a ilettim. Henüz dönüş olmadıysa topluluk DM üzerinden de yazabilirsin, 24 saat içinde cevap geliyor: https://www.topluluk.com/yapay-zeka-factory",
      sanitized: true,
      fallback: 're_escalation_guard',
      toolBypassed: true
    };
  }

  const violations = checkViolations(aiResponse, toolCalled, userContext);
  if (violations.length === 0) {
    return { response: aiResponse, sanitized: false, fallback: null };
  }

  log.warn?.(`[sanitize] first_pass_violations: ${violations.map(v => v.id).join(',')}`);

  if (typeof regenerateFn === 'function') {
    try {
      const retried = await regenerateFn(violations);
      const retryViolations = checkViolations(retried, toolCalled, userContext);
      if (retryViolations.length === 0) {
        log.info?.('[sanitize] retry_clean');
        return { response: retried, sanitized: true, fallback: 'retry' };
      }
      log.error?.(`[sanitize] retry_persist: ${retryViolations.map(v => v.id).join(',')}`);
      aiResponse = retryViolations.length < violations.length ? retried : aiResponse;

      const hard = applyHardFallback(retryViolations, aiResponse, userContext);
      if (hard) {
        log.warn?.(`[sanitize] hard_fallback_applied: ${hard.kind}`);
        return { response: hard.response, sanitized: true, fallback: hard.kind };
      }
      return { response: aiResponse, sanitized: true, fallback: 'retry_persist' };
    } catch (err) {
      log.error?.(`[sanitize] retry_exception: ${err.message}`);
    }
  }

  const hard = applyHardFallback(violations, aiResponse, userContext);
  if (hard) {
    return { response: hard.response, sanitized: true, fallback: hard.kind };
  }
  return { response: aiResponse, sanitized: true, fallback: 'no_retry' };
}

module.exports = {
  run,
  checkViolations,
  detectPriorIletim,
  hasIletimSentence,
  applyHardFallback,
  BANNED_AMOUNTS,
  BANNED_PHRASES,
  ILETIM_PATTERNS
};
