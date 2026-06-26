// Canlı Demo — generic dashboard frontend
// SSE ile pipeline state'ini dinler, DOM'u günceller.
// Stabilizasyon: idempotent event tracking (id), reconnect status banner,
// proje-spesifik payload rendering window.PROJECT_PAYLOAD_RENDERERS plugin'i ile.

const $ = (id) => document.getElementById(id);
const els = {
  pipeline: $("pipeline"),
  productThumb: $("product-thumb"),
  productName: $("product-name"),
  productUrl: $("product-url"),
  runStatus: $("run-status"),
  runTimer: $("run-timer"),
  streamContent: $("stream-content"),
  brandTitle: $("brand-title"),
  brandSub: $("brand-sub"),
  banner: $("connection-banner"),
  qrBtn: $("qr-btn"),
  qrModal: $("qr-modal"),
  qrImg: $("qr-img"),
  qrUrl: $("qr-url"),
};

let stageDefs = [];
let snapshot = null;
let runStartedAt = null;
let stageTimers = {};
let runTimerInterval = null;
let lastEventId = 0;
let eventSource = null;
let projectMeta = null;

const fmtTime = (sec) => {
  if (!sec || sec < 0) return "00:00";
  const m = Math.floor(sec / 60);
  const s = Math.floor(sec % 60);
  return `${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
};

const fmtStageTime = (sec) => {
  if (!sec || sec < 0) return "";
  if (sec < 60) return `${sec.toFixed(1)}s`;
  return fmtTime(sec);
};

const subStageIcon = (status) =>
  status === "completed" ? "✓" : status === "error" ? "✕" : status === "active" ? "●" : "○";

const renderSubStages = (stage) => {
  const order = stage.sub_stage_order || [];
  const subs = stage.sub_stages || {};
  if (!order.length) return "";
  const cards = order
    .map((sid) => {
      const sub = subs[sid] || { id: sid, status: "pending" };
      const pct = sub.progress != null ? Math.round(sub.progress * 100) : null;
      return `<div class="substage" data-substage-id="${sid}" data-status="${sub.status}">
        <div class="substage-icon">${sub.icon || "·"}</div>
        <div class="substage-body">
          <div class="substage-label">${sub.label || sid}</div>
          <div class="substage-sub">${sub.sub_text || "—"}</div>
          <div class="substage-bar${pct == null ? " hidden" : ""}"><div class="substage-bar-fill" style="width:${pct ?? 0}%"></div></div>
        </div>
        <div class="substage-state">${subStageIcon(sub.status)}</div>
      </div>`;
    })
    .join("");
  return `<div class="substages" data-substage-for="${stage.id}">${cards}</div>`;
};

const applyMeta = (meta) => {
  if (!meta) return;
  projectMeta = meta;
  if (meta.title) {
    document.title = `${meta.title} — Canlı Demo`;
    els.brandTitle.textContent = meta.title;
  }
  if (meta.subtitle) {
    els.brandSub.textContent = meta.subtitle;
  }
  if (meta.input_label_default) {
    els.productName.textContent = meta.input_label_default;
  }
  if (meta.public_url) {
    els.qrBtn.hidden = false;
    els.qrUrl.textContent = meta.public_url;
    els.qrImg.src = "/qr.svg";
  }
};

const wireQrModal = () => {
  if (!els.qrBtn || !els.qrModal) return;
  els.qrBtn.addEventListener("click", () => {
    els.qrModal.hidden = false;
  });
  els.qrModal.addEventListener("click", (ev) => {
    if (ev.target && ev.target.dataset && ev.target.dataset.close) {
      els.qrModal.hidden = true;
    }
  });
  document.addEventListener("keydown", (ev) => {
    if (ev.key === "Escape" && !els.qrModal.hidden) {
      els.qrModal.hidden = true;
    }
  });
};

const renderPipeline = () => {
  els.pipeline.innerHTML = "";
  els.pipeline.style.setProperty("--stage-count", String(stageDefs.length || 1));
  stageDefs.forEach((def, idx) => {
    const stage = (snapshot && snapshot.stages && snapshot.stages[def.id]) || {
      id: def.id, label: def.label, icon: def.icon,
      status: "pending", sub_text: null, elapsed_sec: null,
    };
    const node = document.createElement("div");
    node.className = "node";
    node.dataset.status = stage.status;
    node.dataset.stageId = def.id;

    const badgeLabel = {
      pending: "Bekliyor",
      active: "Çalışıyor",
      completed: "Tamam",
      error: "Hata",
    }[stage.status] || stage.status;

    node.innerHTML = `
      <div class="node-head">
        <div class="node-icon">${def.icon || "•"}</div>
        <div>
          <div class="node-title">${def.label || def.id}</div>
          <div class="node-num">Adım ${idx + 1} / ${stageDefs.length}</div>
        </div>
      </div>
      <div class="node-badge">${badgeLabel}</div>
      <div class="node-sub">${stage.sub_text || "—"}</div>
      ${renderSubStages(stage)}
      <div class="node-output" data-output-for="${def.id}"></div>
      <div class="node-timer" data-timer-for="${def.id}">${
        stage.status === "completed" || stage.status === "error"
          ? `⏱ ${fmtStageTime(stage.elapsed_sec)}`
          : stage.status === "active" && stage.started_at
          ? "⏱ 00:00"
          : ""
      }</div>
      <div class="node-progress"></div>
    `;
    els.pipeline.appendChild(node);
  });
  if (snapshot) {
    Object.values(snapshot.stages || {}).forEach((stg) => {
      if (stg.payload) setNodeOutput(stg.id, stg.payload);
    });
  }
};

const updateSubStage = (stageId, subId, patch) => {
  const card = els.pipeline.querySelector(
    `[data-substage-for="${stageId}"] [data-substage-id="${subId}"]`
  );
  if (!card) return;
  if (patch.status) card.dataset.status = patch.status;
  if (patch.sub_text !== undefined) {
    const s = card.querySelector(".substage-sub");
    if (s) s.textContent = patch.sub_text || "—";
  }
  if (patch.progress != null) {
    const bar = card.querySelector(".substage-bar");
    const fill = card.querySelector(".substage-bar-fill");
    if (bar && fill) {
      bar.classList.remove("hidden");
      fill.style.width = Math.round(patch.progress * 100) + "%";
    }
  }
  const st = card.querySelector(".substage-state");
  if (st && patch.status) st.textContent = subStageIcon(patch.status);
};

const updateNode = (stageId, status, subText, elapsedSec) => {
  const node = els.pipeline.querySelector(`[data-stage-id="${stageId}"]`);
  if (!node) return;
  if (status) node.dataset.status = status;
  const badge = node.querySelector(".node-badge");
  if (badge && status) {
    badge.textContent = {
      pending: "Bekliyor",
      active: "Çalışıyor",
      completed: "Tamam",
      error: "Hata",
    }[status] || status;
  }
  if (subText !== undefined && subText !== null) {
    const sub = node.querySelector(".node-sub");
    if (sub) sub.textContent = subText || "—";
  }
  if (elapsedSec !== null && elapsedSec !== undefined) {
    const t = node.querySelector(`[data-timer-for="${stageId}"]`);
    if (t) t.textContent = `⏱ ${fmtStageTime(elapsedSec)}`;
  }
};

const startStageTimer = (stageId, startedAt) => {
  if (stageTimers[stageId]) clearInterval(stageTimers[stageId]);
  const node = els.pipeline.querySelector(`[data-stage-id="${stageId}"]`);
  if (!node) return;
  const t = node.querySelector(`[data-timer-for="${stageId}"]`);
  if (!t) return;
  const tick = () => {
    const elapsed = (Date.now() / 1000) - startedAt;
    t.textContent = `⏱ ${fmtStageTime(elapsed)}`;
  };
  tick();
  stageTimers[stageId] = setInterval(tick, 200);
};

const stopStageTimer = (stageId) => {
  if (stageTimers[stageId]) {
    clearInterval(stageTimers[stageId]);
    delete stageTimers[stageId];
  }
};

const updateRunStatus = (state, label) => {
  const dot = els.runStatus.querySelector(".status-dot");
  const lbl = els.runStatus.querySelector(".status-label");
  if (dot) dot.dataset.state = state;
  if (lbl) lbl.textContent = label;
};

const startRunTimer = (startedAt) => {
  runStartedAt = startedAt;
  if (runTimerInterval) clearInterval(runTimerInterval);
  const tick = () => {
    if (!runStartedAt) return;
    const elapsed = (Date.now() / 1000) - runStartedAt;
    els.runTimer.textContent = fmtTime(elapsed);
  };
  tick();
  runTimerInterval = setInterval(tick, 200);
};

const stopRunTimer = (finalElapsed) => {
  if (runTimerInterval) {
    clearInterval(runTimerInterval);
    runTimerInterval = null;
  }
  if (finalElapsed !== null && finalElapsed !== undefined) {
    els.runTimer.textContent = fmtTime(finalElapsed);
  }
};

const stageLabel = (stageId) => {
  const def = stageDefs.find((s) => s.id === stageId);
  return def ? (def.label || def.id) : stageId;
};

const pushStream = (event) => {
  const time = new Date((event.ts || Date.now() / 1000) * 1000).toLocaleTimeString("tr-TR", { hour12: false });
  let label = "";
  let tone = "info";
  switch (event.type) {
    case "run_start":
      label = `Yeni koşu başladı`;
      tone = "start";
      break;
    case "run_end":
      label = `Koşu tamamlandı · toplam ${fmtStageTime(event.elapsed_sec)}`;
      tone = "done";
      break;
    case "run_fail":
      label = `Koşu hata verdi`;
      tone = "fail";
      break;
    case "stage_start":
      label = `${stageLabel(event.stage_id)} başlatıldı`;
      tone = "start";
      break;
    case "stage_update":
      if (!event.sub_text) return;
      label = event.sub_text;
      tone = "info";
      break;
    case "stage_end":
      label = `${stageLabel(event.stage_id)} tamamlandı · ${fmtStageTime(event.elapsed_sec)}`;
      tone = "done";
      break;
    case "stage_fail":
      label = `${stageLabel(event.stage_id)} hata verdi`;
      tone = "fail";
      break;
    case "hydrate":
    case "idle":
      return;
    default:
      return;
  }
  const empty = els.streamContent.querySelector(".output-empty");
  if (empty) empty.remove();

  const line = document.createElement("div");
  line.className = "stream-line";
  line.dataset.tone = tone;
  line.innerHTML = `<span class="stream-time">${time}</span><span class="stream-msg">${label}</span>`;
  els.streamContent.prepend(line);
  while (els.streamContent.children.length > 30) {
    els.streamContent.removeChild(els.streamContent.lastChild);
  }
};

const escapeHtml = (str) =>
  String(str || "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");

const renderGenericPayload = (payload) => {
  if (!payload || typeof payload !== "object") {
    return `<div class="output-row"><span class="output-val">${escapeHtml(String(payload))}</span></div>`;
  }
  const rows = Object.entries(payload)
    .filter(([, v]) => v != null && v !== "")
    .slice(0, 6)
    .map(([k, v]) => {
      const val = typeof v === "object" ? JSON.stringify(v) : String(v);
      return `<div class="output-row"><span class="output-key">${escapeHtml(k)}</span><span class="output-val">${escapeHtml(val.slice(0, 200))}</span></div>`;
    })
    .join("");
  return rows;
};

const setNodeOutput = (stageId, payload) => {
  if (!payload) return;
  const target = els.pipeline.querySelector(`[data-output-for="${stageId}"]`);
  if (!target) return;

  let rendered = null;
  if (window.PROJECT_PAYLOAD_RENDERERS && typeof window.PROJECT_PAYLOAD_RENDERERS[stageId] === "function") {
    try {
      rendered = window.PROJECT_PAYLOAD_RENDERERS[stageId]({
        payload, els, escapeHtml, fmtStageTime,
      });
    } catch (e) {
      console.warn("Proje payload renderer hata:", e);
    }
  }
  target.innerHTML = rendered != null ? rendered : renderGenericPayload(payload);
  target.classList.add("has-content");
};

const flashCompleteNode = (stageId) => {
  const node = els.pipeline.querySelector(`[data-stage-id="${stageId}"]`);
  if (!node) return;
  node.classList.add("just-completed");
  setTimeout(() => node.classList.remove("just-completed"), 1300);
};

const trackEventId = (event) => {
  if (event && typeof event.id === "number") {
    if (event.id <= lastEventId) return false;
    lastEventId = event.id;
  }
  return true;
};

const handleEvent = (event) => {
  if (!trackEventId(event)) return;
  pushStream(event);

  switch (event.type) {
    case "hydrate": {
      if (event.snapshot) hydrateFromSnapshot(event.snapshot);
      break;
    }
    case "run_start": {
      Object.keys(stageTimers).forEach(stopStageTimer);
      stageTimers = {};
      els.productUrl.textContent = event.input_label || "";
      els.productName.textContent = (projectMeta && projectMeta.input_label_running) || "Pipeline çalışıyor…";
      els.productThumb.style.backgroundImage = "";
      els.productThumb.classList.remove("has-image");
      snapshot = event.snapshot || snapshot;
      renderPipeline();
      updateRunStatus("running", "Çalışıyor");
      startRunTimer(event.started_at);
      break;
    }
    case "stage_start": {
      updateNode(event.stage_id, "active", event.sub_text, null);
      if (event.started_at) startStageTimer(event.stage_id, event.started_at);
      break;
    }
    case "stage_update": {
      updateNode(event.stage_id, null, event.sub_text, null);
      break;
    }
    case "stage_end": {
      stopStageTimer(event.stage_id);
      updateNode(event.stage_id, "completed", null, event.elapsed_sec);
      if (event.payload) setNodeOutput(event.stage_id, event.payload);
      flashCompleteNode(event.stage_id);
      break;
    }
    case "stage_fail": {
      stopStageTimer(event.stage_id);
      updateNode(event.stage_id, "error", event.error || "Hata", event.elapsed_sec);
      break;
    }
    case "substage_start": {
      updateSubStage(event.stage_id, event.sub_id, {
        status: "active",
        sub_text: event.sub_text || "Başlıyor…",
      });
      break;
    }
    case "substage_update": {
      updateSubStage(event.stage_id, event.sub_id, {
        sub_text: event.sub_text,
        progress: event.progress,
      });
      break;
    }
    case "substage_end": {
      updateSubStage(event.stage_id, event.sub_id, {
        status: "completed",
        sub_text: "Tamam",
        progress: 1,
      });
      break;
    }
    case "substage_fail": {
      updateSubStage(event.stage_id, event.sub_id, {
        status: "error",
        sub_text: event.error || "Hata",
      });
      break;
    }
    case "run_end": {
      updateRunStatus("completed", "Tamamlandı");
      stopRunTimer(event.elapsed_sec);
      break;
    }
    case "run_fail": {
      updateRunStatus("error", "Hata");
      stopRunTimer(event.elapsed_sec);
      break;
    }
    case "idle": {
      updateRunStatus("idle", "Boşta");
      stopRunTimer(0);
      break;
    }
  }
};

const hydrateFromSnapshot = (snap) => {
  if (!snap) return;
  snapshot = snap;
  renderPipeline();

  if (snap.input_label) {
    els.productUrl.textContent = snap.input_label;
  }

  const orderedStages = (snap.stage_order || []).map((id) => snap.stages?.[id]).filter(Boolean);
  orderedStages.forEach((stg) => {
    if (stg.payload) setNodeOutput(stg.id, stg.payload);
  });

  if (snap.status === "running" && snap.started_at) {
    startRunTimer(snap.started_at);
    updateRunStatus("running", "Çalışıyor");
    orderedStages.forEach((stg) => {
      if (stg.status === "active" && stg.started_at) {
        startStageTimer(stg.id, stg.started_at);
      }
    });
  } else if (snap.status === "completed") {
    updateRunStatus("completed", "Son koşu tamamlandı");
    stopRunTimer(snap.elapsed_sec);
  } else if (snap.status === "error") {
    updateRunStatus("error", "Hata");
    stopRunTimer(snap.elapsed_sec);
  } else {
    updateRunStatus("idle", "Boşta");
    stopRunTimer(0);
  }
};

const showBanner = (message, tone = "warn") => {
  if (!els.banner) return;
  els.banner.textContent = message;
  els.banner.dataset.tone = tone;
  els.banner.hidden = false;
};

const hideBanner = () => {
  if (els.banner) els.banner.hidden = true;
};

const connectSSE = () => {
  if (eventSource) {
    try { eventSource.close(); } catch (_) {}
  }
  const url = lastEventId > 0 ? `/events?last_id=${lastEventId}` : "/events";
  eventSource = new EventSource(url);

  eventSource.onopen = () => hideBanner();
  eventSource.onmessage = (ev) => {
    try {
      const data = JSON.parse(ev.data);
      handleEvent(data);
    } catch (e) {
      console.error("Event parse hatası:", e, ev.data);
    }
  };
  eventSource.onerror = () => {
    showBanner("Bağlantı koptu, yeniden bağlanıyor…", "warn");
  };
};

const boot = async () => {
  try {
    const res = await fetch("/api/state");
    const data = await res.json();
    applyMeta(data.meta || {});
    stageDefs = data.stages || [];
    hydrateFromSnapshot(data.snapshot);
  } catch (e) {
    console.error("State boot hatası:", e);
  }
  wireQrModal();
  connectSSE();
};

boot();
