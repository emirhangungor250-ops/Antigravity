/**
 * JARVIS — Main entry point.
 *
 * Wires together the orb visualization, WebSocket communication,
 * speech recognition, and audio playback into a single experience.
 */

import { createOrb, type OrbState } from "./orb";
import { createVoiceInput, createAudioPlayer, createClapDetector } from "./voice";
import { createSocket } from "./ws";
import { openSettings, checkFirstTimeSetup } from "./settings";
import "./style.css";
import startupSoundUrl from "./jarvis-startup.mp3";
import greetingSoundUrl from "./greeting.mp3";

// JARVIS her açılışta (uyandığında) bu repliği söyler — sabit, önceden üretilmiş kendi sesi.
const GREETING_TEXT = "Emrinizdeyim, efendim.";

// ---------------------------------------------------------------------------
// State machine
// ---------------------------------------------------------------------------

// "asleep" = başlangıç uyku durumu; uyandırılana dek konuşma backend'e gitmez
type State = "asleep" | "idle" | "listening" | "thinking" | "speaking";
let currentState: State = "asleep";
let isMuted = false;
let isAwake = false;
// Echo savunması: JARVIS kendi sesini mikrofonda duyabiliyor (hoparlör → mikrofon).
let lastSpokenText = "";
let suppressTranscriptsUntil = 0;

// Mikrofonda duyulan metin, JARVIS'in az önce söylediğiyle büyük oranda örtüşüyorsa
// bu kullanıcı değil, kendi echo'sudur — yok say.
function isEchoOfJarvis(text: string): boolean {
  if (!lastSpokenText) return false;
  const norm = (s: string) =>
    s.toLocaleLowerCase("tr").replace(/[^\p{L}\p{N}\s]/gu, " ").split(/\s+/).filter(Boolean);
  const said = new Set(norm(lastSpokenText));
  const heard = norm(text);
  if (heard.length === 0) return false;
  let overlap = 0;
  for (const w of heard) if (said.has(w)) overlap++;
  return overlap / heard.length > 0.5;
}

const statusEl = document.getElementById("status-text")!;
const errorEl = document.getElementById("error-text")!;
const subtitleEl = document.getElementById("subtitle")!;

function showError(msg: string) {
  errorEl.textContent = msg;
  errorEl.style.opacity = "1";
  setTimeout(() => {
    errorEl.style.opacity = "0";
  }, 5000);
}

function updateStatus(state: State) {
  const labels: Record<State, string> = {
    asleep: "uyuyor — uyandırmak için alkışla veya 'Jarvis uyan' de",
    idle: "",
    listening: "listening...",
    thinking: "thinking...",
    speaking: "",
  };
  statusEl.textContent = labels[state];
}

// ---------------------------------------------------------------------------
// Altyazı (subtitle) — JARVIS konuşurken söylediği metin
// ---------------------------------------------------------------------------

let subtitleHideTimer: number | undefined;

function showSubtitle(text: string) {
  if (!text) return;
  if (subtitleHideTimer) {
    clearTimeout(subtitleHideTimer);
    subtitleHideTimer = undefined;
  }
  subtitleEl.textContent = text;
  subtitleEl.classList.add("visible");
}

function hideSubtitle() {
  // Konuşma bitince kısa bir süre ekranda kalsın, sonra yumuşakça gizlen
  subtitleHideTimer = window.setTimeout(() => {
    subtitleEl.classList.remove("visible");
  }, 1200);
}

// ---------------------------------------------------------------------------
// Init components
// ---------------------------------------------------------------------------

const canvas = document.getElementById("orb-canvas") as HTMLCanvasElement;
const orb = createOrb(canvas);

const wsProto = window.location.protocol === "https:" ? "wss:" : "ws:";
const WS_URL = `${wsProto}//${window.location.host}/ws/voice`;
const socket = createSocket(WS_URL);

const audioPlayer = createAudioPlayer();
orb.setAnalyser(audioPlayer.getAnalyser());

function transition(newState: State) {
  if (newState === currentState) return;
  currentState = newState;
  orb.setState(newState as OrbState);
  updateStatus(newState);

  switch (newState) {
    case "asleep":
      // Uykuda da dinle — ama transcript backend'e gitmez, sadece "uyan" yakalanır
      if (!isMuted) voiceInput.resume();
      break;
    case "idle":
      if (!isMuted) voiceInput.resume();
      break;
    case "listening":
      if (!isMuted) voiceInput.resume();
      break;
    case "thinking":
      voiceInput.pause();
      break;
    case "speaking":
      voiceInput.pause();
      break;
  }
}

// ---------------------------------------------------------------------------
// Uyandırma — alkış veya "uyan" kelimesi
// ---------------------------------------------------------------------------

function wakeUp() {
  if (isAwake) return;
  isAwake = true;
  playStartupMusic(); // gerçek JARVIS açılış müziği (yüklenemezse sentez chime'a düşer)
  orb.wake(); // sinematik doğuş animasyonu (hızlandırıldı)
  clapDetector.stop(); // uyandık, artık alkış dinlemeye gerek yok
  transition("idle");
  // Kısa "çevrimiçi" parıltısı — şov dokunuşu
  statusEl.textContent = "JARVIS çevrimiçi";
  statusEl.classList.add("flash");
  // Orb doğarken JARVIS selam verir: "Emrinizdeyim, efendim." (her açılışta sabit replik).
  // Karşılamayı TTS yolundan (audioPlayer) çalıyoruz → orb sese tepki verir, bitince idle'a döner.
  lastSpokenText = GREETING_TEXT; // echo savunması: mikrofon kendi selamını kullanıcı sanmasın
  setTimeout(() => {
    statusEl.classList.remove("flash");
    transition("speaking");
    showSubtitle(GREETING_TEXT);
    audioPlayer.playUrl(greetingSoundUrl).catch((e) => {
      console.warn("[wake] greeting failed", e);
      hideSubtitle();
      transition(isMuted ? "idle" : "listening");
    });
  }, 600);
}

// Uyanma sesi — sinematik power-up: bas vuruş + yükselen sweep + tepe parıltısı
// (asset yok, tamamı Web Audio ile sentezlenir)
function playWakeChime() {
  try {
    const ctx = audioPlayer.getAnalyser().context as AudioContext;
    if (ctx.state === "suspended") ctx.resume();
    const now = ctx.currentTime;

    const master = ctx.createGain();
    master.gain.setValueAtTime(0.0001, now);
    master.gain.exponentialRampToValueAtTime(0.45, now + 0.05);
    master.gain.exponentialRampToValueAtTime(0.0001, now + 1.5);
    master.connect(ctx.destination);

    // 1) Derin bas vuruş — uyanışın "ağırlığı"
    const thump = ctx.createOscillator();
    thump.type = "sine";
    thump.frequency.setValueAtTime(120, now);
    thump.frequency.exponentialRampToValueAtTime(38, now + 0.5);
    const tg = ctx.createGain();
    tg.gain.setValueAtTime(0.9, now);
    tg.gain.exponentialRampToValueAtTime(0.0001, now + 0.6);
    thump.connect(tg); tg.connect(master);
    thump.start(now); thump.stop(now + 0.6);

    // 2) Yükselen güç-veriliş sweep'i — iki katman (sine + sawtooth) zengin doku
    [
      { type: "sine" as OscillatorType, f0: 180, mul: 4.5, g: 0.5 },
      { type: "sawtooth" as OscillatorType, f0: 90, mul: 5, g: 0.18 },
    ].forEach(({ type, f0, mul, g }) => {
      const osc = ctx.createOscillator();
      osc.type = type;
      osc.frequency.setValueAtTime(f0, now);
      osc.frequency.exponentialRampToValueAtTime(f0 * mul, now + 0.9);
      const gain = ctx.createGain();
      gain.gain.setValueAtTime(0.0001, now);
      gain.gain.exponentialRampToValueAtTime(g, now + 0.12);
      gain.gain.exponentialRampToValueAtTime(0.0001, now + 1.2);
      osc.connect(gain); gain.connect(master);
      osc.start(now); osc.stop(now + 1.2);
    });

    // 3) Tepe parıltısı — zirvede kısa, parlak shimmer
    const sparkle = ctx.createOscillator();
    sparkle.type = "triangle";
    sparkle.frequency.setValueAtTime(1400, now + 0.5);
    sparkle.frequency.exponentialRampToValueAtTime(2600, now + 1.0);
    const sg = ctx.createGain();
    sg.gain.setValueAtTime(0.0001, now + 0.5);
    sg.gain.exponentialRampToValueAtTime(0.22, now + 0.62);
    sg.gain.exponentialRampToValueAtTime(0.0001, now + 1.25);
    sparkle.connect(sg); sg.connect(master);
    sparkle.start(now + 0.5); sparkle.stop(now + 1.3);
  } catch (e) {
    console.warn("[wake] chime failed", e);
  }
}

// Gerçek JARVIS açılış müziği — Iron Man arayüz sesi (konuşma AI ile çıkarıldı, sadece müzik).
// Uyanışta arka planda çalar; kullanıcı konuşmaya başlayınca durur. Yüklenemezse chime'a düşer.
let startupAudio: HTMLAudioElement | null = null;
function playStartupMusic() {
  try {
    startupAudio = new Audio(startupSoundUrl);
    startupAudio.volume = 0.5;
    const p = startupAudio.play();
    if (p && typeof p.catch === "function") {
      p.catch((err) => {
        console.warn("[music] blocked, fallback chime:", err?.name);
        playWakeChime();
      });
    }
  } catch (e) {
    console.warn("[music] error, fallback chime", e);
    playWakeChime();
  }
}

// Açılış müziğini yumuşakça kıs. targetVolume=0 ise tamamen durdurur (kullanıcı konuşunca),
// >0 ise sadece o seviyeye indirir (karşılama biterken müziği susturmadan geri plana alır).
// Aksi halde hoparlör müziği mikrofona sızıp ses tanımayı bozuyor — ama müzik 17 sn,
// karşılama ~2 sn; karşılama bitince müziği ÖLDÜRMEK 15 sn'yi çöpe atıyordu. Çözüm: karşılama
// bitince kısık devam et, tam susturmayı yalnızca kullanıcı konuşunca yap.
function fadeStartupMusic(targetVolume = 0, durationMs = 1200) {
  const audio = startupAudio;
  if (!audio) return;
  const steps = 24;
  const v0 = audio.volume;
  if (targetVolume >= v0) return; // zaten hedefin altında/eşit
  let i = 0;
  const timer = window.setInterval(() => {
    i++;
    audio.volume = Math.max(targetVolume, v0 - (v0 - targetVolume) * (i / steps));
    if (i >= steps) {
      window.clearInterval(timer);
      if (targetVolume <= 0) {
        try { audio.pause(); } catch { /* noop */ }
        if (startupAudio === audio) startupAudio = null;
      }
    }
  }, durationMs / steps);
}

// ---------------------------------------------------------------------------
// Voice input
// ---------------------------------------------------------------------------

const voiceInput = createVoiceInput(
  (text: string) => {
    // Uykudayken konuşmayı işleme — sadece uyandırma kelimesini dinle
    if (!isAwake) {
      if (text.toLocaleLowerCase("tr").includes("uyan")) {
        wakeUp();
      }
      return;
    }
    // JARVIS konuşurken/düşünürken gelen ses = kendi echo'su; yok say (şov tutarlılığı)
    if (currentState === "speaking" || currentState === "thinking") return;
    // Konuşma bittikten hemen sonraki kuyruk/yankıyı da yut
    if (performance.now() < suppressTranscriptsUntil) return;
    // Son söylediğiyle büyük oranda örtüşüyorsa echo'dur
    if (isEchoOfJarvis(text)) return;
    // Cancel any current JARVIS response before sending new input
    audioPlayer.stop();
    fadeStartupMusic(0, 400); // kullanıcı konuşmaya başladı — açılış müziğini hızlıca tamamen sustur
    // User spoke — send transcript
    socket.send({ type: "transcript", text, isFinal: true });
    transition("thinking");
  },
  (msg: string) => {
    showError(msg);
  }
);

// Alkış algılayıcı — uyandırmanın ikinci yolu
const clapDetector = createClapDetector(() => {
  if (!isAwake) wakeUp();
});

// ---------------------------------------------------------------------------
// Audio playback finished
// ---------------------------------------------------------------------------

audioPlayer.onFinished(() => {
  hideSubtitle();
  // Karşılama bitti → müziği SUSTURMA, sadece bir tık kıs ki net duyulmaya devam etsin
  // (müzik 17 sn, karşılama ~2 sn). 0.18 çok kısıktı, "ses kesildi" gibi algılanıyordu;
  // 0.38 belirgin. Mikrofon sızıntısı: müzik sözsüz (STT kelime üretmez) + kullanıcı
  // konuşmaya başlayınca zaten anında tamamen susturuluyor.
  fadeStartupMusic(0.38, 1500);
  // Konuşma bitti — kısa süre transcript'leri bastır (hoparlör yankısı/kuyruğu yutulsun)
  suppressTranscriptsUntil = performance.now() + 1200;
  transition("idle");
});

// ---------------------------------------------------------------------------
// WebSocket messages
// ---------------------------------------------------------------------------

socket.onMessage((msg) => {
  const type = msg.type as string;

  if (type === "audio") {
    // Uykudayken gelen sesi çalma — uyandırılana dek sessiz kal
    if (!isAwake) return;
    const audioData = msg.data as string;
    console.log("[audio] received", audioData ? `${audioData.length} chars` : "EMPTY", "state:", currentState);
    // Altyazı: JARVIS'in söylediği metni ekranda göster
    if (msg.text) {
      showSubtitle(msg.text as string);
      lastSpokenText = msg.text as string; // echo karşılaştırması için
      console.log("[JARVIS]", msg.text);
    }
    if (audioData) {
      if (currentState !== "speaking") {
        transition("speaking");
      }
      audioPlayer.enqueue(audioData);
    } else {
      // TTS failed — no audio but still need to return to idle
      console.warn("[audio] no data received, returning to idle");
      hideSubtitle();
      transition("idle");
    }
  } else if (type === "status") {
    // Uykudayken durum değişimlerini yok say — uyanmayı bozmasın
    if (!isAwake) return;
    const state = msg.state as string;
    if (state === "thinking" && currentState !== "thinking") {
      transition("thinking");
    } else if (state === "working") {
      // Task spawned — show thinking with a different label
      transition("thinking");
      statusEl.textContent = "working...";
    } else if (state === "idle") {
      transition("idle");
    }
  } else if (type === "text") {
    // Text fallback when TTS fails
    console.log("[JARVIS]", msg.text);
  } else if (type === "task_spawned") {
    console.log("[task]", "spawned:", msg.task_id, msg.prompt);
  } else if (type === "task_complete") {
    console.log("[task]", "complete:", msg.task_id, msg.status, msg.summary);
  }
});

// ---------------------------------------------------------------------------
// Kick off — JARVIS uykuda başlar; uyandırma kelimesi/alkış bekler
// ---------------------------------------------------------------------------

// Orb render olduktan sonra uyku durumunu kur.
// NOT: Web Speech API'yi BURADA (gesture'sız) başlatmıyoruz — Chrome kullanıcı hareketi
// olmadan recognition.start()'a "not-allowed" veriyor ("Microphone access denied" görünür).
// Tanıma, ilk gerçek tıklamada (ensureAudioContext) başlar.
setTimeout(() => {
  transition("asleep");
}, 1000);

// Resume AudioContext on ANY user interaction (browser autoplay policy)
// Aynı gesture'da alkış algılayıcı mikrofonunu da başlat (getUserMedia gesture ister)
let clapStarted = false;
function ensureAudioContext(evt?: Event) {
  const ctx = audioPlayer.getAnalyser().context as AudioContext;
  if (ctx.state === "suspended") {
    ctx.resume().then(() => console.log("[audio] context resumed"));
  }
  // İlk kullanıcı etkileşiminde alkış dinleyicisini ayağa kaldır (uykudaysak)
  if (!clapStarted && !isAwake) {
    clapStarted = true;
    clapDetector.start();
  }
  // Uyandırma kelimesi tanımasını gerçek kullanıcı hareketinde başlat (gesture).
  // Gesture'sız başlatınca Chrome "not-allowed" veriyordu. start() idempotent: zaten
  // çalışıyorsa yutulur, önceki denemede "not-allowed" olduysa bu tıklama toparlar.
  if (evt) {
    voiceInput.start();
  }
}
document.addEventListener("click", ensureAudioContext);
document.addEventListener("touchstart", ensureAudioContext);
document.addEventListener("keydown", ensureAudioContext, { once: true });

// Try to resume audio context on load
ensureAudioContext();

// ---------------------------------------------------------------------------
// UI Controls
// ---------------------------------------------------------------------------

const btnMute = document.getElementById("btn-mute")!;
const btnMenu = document.getElementById("btn-menu")!;
const menuDropdown = document.getElementById("menu-dropdown")!;
const btnRestart = document.getElementById("btn-restart")!;
const btnFixSelf = document.getElementById("btn-fix-self")!;

btnMute.addEventListener("click", (e) => {
  e.stopPropagation();
  isMuted = !isMuted;
  btnMute.classList.toggle("muted", isMuted);
  if (isMuted) {
    voiceInput.pause();
    if (isAwake) transition("idle");
  } else {
    voiceInput.resume();
    // Uykudaysak uyku durumunda kal, uyanıksak dinlemeye dön
    transition(isAwake ? "listening" : "asleep");
  }
});

btnMenu.addEventListener("click", (e) => {
  e.stopPropagation();
  menuDropdown.style.display = menuDropdown.style.display === "none" ? "block" : "none";
});

document.addEventListener("click", () => {
  menuDropdown.style.display = "none";
});

btnRestart.addEventListener("click", async (e) => {
  e.stopPropagation();
  menuDropdown.style.display = "none";
  statusEl.textContent = "restarting...";
  try {
    await fetch("/api/restart", { method: "POST" });
    // Wait a few seconds then reload
    setTimeout(() => window.location.reload(), 4000);
  } catch {
    statusEl.textContent = "restart failed";
  }
});

btnFixSelf.addEventListener("click", (e) => {
  e.stopPropagation();
  menuDropdown.style.display = "none";
  // Activate work mode on the WebSocket session (JARVIS becomes Claude Code's voice)
  socket.send({ type: "fix_self" });
  statusEl.textContent = "entering work mode...";
});

// Settings button
const btnSettings = document.getElementById("btn-settings")!;
btnSettings.addEventListener("click", (e) => {
  e.stopPropagation();
  menuDropdown.style.display = "none";
  openSettings();
});

// First-time setup detection — check after a short delay for server readiness
setTimeout(() => {
  checkFirstTimeSetup();
}, 2000);
