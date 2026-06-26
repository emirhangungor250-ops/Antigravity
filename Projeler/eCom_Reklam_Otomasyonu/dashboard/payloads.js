// eCom Reklam Otomasyonu — proje-spesifik payload renderer'ları.
// Generic dashboard app.js bu fonksiyonları stage_end event'inde çağırır.

(function () {
  const setTopbarFromExtract = (payload, els, escapeHtml) => {
    if (payload.hero_image_url) {
      els.productThumb.style.backgroundImage = `url(${JSON.stringify(payload.hero_image_url)})`;
      els.productThumb.classList.add("has-image");
    }
    if (payload.brand || payload.product) {
      els.productName.textContent = `${payload.brand || ""} — ${payload.product || ""}`
        .replace(/^ — | — $/g, "");
    }
  };

  const triggerHeroSpotlight = () => {
    setTimeout(() => {
      const hero = document.querySelector('[data-output-for="extract"] .output-hero');
      if (!hero) return;
      hero.classList.add("spotlight");
      setTimeout(() => hero.classList.remove("spotlight"), 2500);
    }, 80);
  };

  window.PROJECT_PAYLOAD_RENDERERS = {
    extract: ({ payload, els, escapeHtml }) => {
      let rows = "";
      if (payload.hero_image_url) {
        rows += `<div class="output-hero" style="background-image:url(${JSON.stringify(payload.hero_image_url)})"></div>`;
      }
      if (payload.brand) {
        rows += `<div class="output-row"><span class="output-key">Marka</span><span class="output-val">${escapeHtml(payload.brand)}</span></div>`;
      }
      if (payload.product) {
        rows += `<div class="output-row"><span class="output-key">Ürün</span><span class="output-val">${escapeHtml(payload.product)}</span></div>`;
      }
      if (payload.concept) {
        rows += `<div class="output-row"><span class="output-key">Konsept</span><span class="output-val">${escapeHtml(payload.concept)}</span></div>`;
      }
      setTopbarFromExtract(payload, els, escapeHtml);
      triggerHeroSpotlight();
      return rows;
    },

    scenario: ({ payload, escapeHtml }) => {
      let rows = "";
      if (payload.scene_count != null) {
        rows += `<div class="output-row"><span class="output-key">Sahne</span><span class="output-val">${payload.scene_count}</span></div>`;
      }
      if (payload.duration_sec) {
        rows += `<div class="output-row"><span class="output-key">Süre</span><span class="output-val">${payload.duration_sec} sn</span></div>`;
      }
      if (payload.voiceover_text) {
        rows += `<div class="output-blockquote">"${escapeHtml(payload.voiceover_text)}"</div>`;
      }
      return rows;
    },

    produce: ({ payload, escapeHtml }) => {
      let rows = "";
      if (payload.duration_sec) {
        rows += `<div class="output-row"><span class="output-key">Süre</span><span class="output-val">${payload.duration_sec} sn</span></div>`;
      }
      rows += `<div class="output-row"><span class="output-key">Dış ses</span><span class="output-val">${payload.voiceover_ok ? "✓ üretildi" : "⚠️ ambient"}</span></div>`;
      if (payload.video_url) {
        rows += `<div class="output-video"><video src="${escapeHtml(payload.video_url)}" muted playsinline preload="metadata"></video></div>`;
        rows += `<div class="output-row"><a class="output-link" href="${escapeHtml(payload.video_url)}" target="_blank">📥 Yeni sekmede aç</a></div>`;
      }
      return rows;
    },

    caption: ({ payload, escapeHtml }) => {
      let rows = "";
      if (payload.platforms?.length) {
        rows += `<div class="output-row"><span class="output-key">Platform</span><span class="output-val">${payload.platforms.join(", ")}</span></div>`;
      }
      if (payload.sample_text) {
        rows += `<div class="output-blockquote">${escapeHtml(payload.sample_text)}</div>`;
      }
      if (payload.hashtags?.length) {
        const tags = payload.hashtags
          .map((h, i) => `<span class="output-hashtag" style="animation-delay:${i * 0.09}s">#${escapeHtml(h)}</span>`)
          .join("");
        rows += `<div class="output-hashtags">${tags}</div>`;
      }
      return rows;
    },

    upload: ({ payload, escapeHtml }) => {
      let rows = "";
      if (payload.post_urls && Object.keys(payload.post_urls).length) {
        Object.entries(payload.post_urls).forEach(([pl, url]) => {
          const plLabel = pl.charAt(0).toUpperCase() + pl.slice(1);
          rows += `<div class="output-row inline"><span class="output-key">${escapeHtml(plLabel)}</span><a class="output-link" href="${escapeHtml(url)}" target="_blank">Aç ↗</a></div>`;
        });
      }
      if (payload.errors?.length) {
        rows += `<div class="output-row"><span class="output-key">Hata</span><span class="output-val">${payload.errors.join(", ")}</span></div>`;
      }
      return rows;
    },
  };
})();
