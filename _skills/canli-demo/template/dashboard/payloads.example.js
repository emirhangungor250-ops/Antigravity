// Proje-spesifik payload renderer'ları — opsiyonel.
//
// Bu dosyayı projedeki `dashboard/payloads.js` olarak kopyalarsan
// stage'lerin emitter.end_stage(stage_id, payload) çağrısındaki payload'u
// projeye özgü şekilde render edebilirsin. Tanımlamazsan generic key/value
// render fallback'i devreye girer.
//
// Imza: (ctx) => HTMLString
// ctx = { payload, els, escapeHtml, fmtStageTime }

window.PROJECT_PAYLOAD_RENDERERS = {
  // Örnek 1: extract stage'inde marka + ürün adı + hero image gösterimi
  // extract: ({ payload, escapeHtml }) => {
  //   let rows = "";
  //   if (payload.hero_image_url) {
  //     rows += `<div class="output-hero" style="background-image:url(${JSON.stringify(payload.hero_image_url)})"></div>`;
  //   }
  //   if (payload.brand) {
  //     rows += `<div class="output-row"><span class="output-key">Marka</span><span class="output-val">${escapeHtml(payload.brand)}</span></div>`;
  //   }
  //   return rows;
  // },

  // Örnek 2: caption stage'inde hashtag chip'leri
  // caption: ({ payload, escapeHtml }) => {
  //   if (!payload.hashtags?.length) return null;
  //   const tags = payload.hashtags
  //     .map((h, i) => `<span class="output-hashtag" style="animation-delay:${i * 0.09}s">#${escapeHtml(h)}</span>`)
  //     .join("");
  //   return `<div class="output-hashtags">${tags}</div>`;
  // },
};
