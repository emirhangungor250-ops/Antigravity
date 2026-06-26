/**
 * Voice input (Web Speech API) and audio output (AudioContext) for JARVIS.
 */

// ---------------------------------------------------------------------------
// Speech Recognition
// ---------------------------------------------------------------------------

export interface VoiceInput {
  start(): void;
  stop(): void;
  pause(): void;
  resume(): void;
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
declare const webkitSpeechRecognition: any;

export function createVoiceInput(
  onTranscript: (text: string) => void,
  onError: (msg: string) => void
): VoiceInput {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const SR = (window as any).SpeechRecognition || (typeof webkitSpeechRecognition !== "undefined" ? webkitSpeechRecognition : null);
  if (!SR) {
    onError("Speech recognition not supported in this browser");
    return { start() {}, stop() {}, pause() {}, resume() {} };
  }

  const recognition = new SR();
  recognition.continuous = true;
  recognition.interimResults = true;
  recognition.lang = (import.meta as any).env?.VITE_STT_LANG || "tr-TR";

  let shouldListen = false;
  let paused = false;

  recognition.onresult = (event: any) => {
    for (let i = event.resultIndex; i < event.results.length; i++) {
      if (event.results[i].isFinal) {
        const text = event.results[i][0].transcript.trim();
        if (text) onTranscript(text);
      }
    }
  };

  recognition.onend = () => {
    if (shouldListen && !paused) {
      try {
        recognition.start();
      } catch {
        // Already started
      }
    }
  };

  recognition.onerror = (event: any) => {
    if (event.error === "not-allowed") {
      // Çoğu zaman izin gerçekten verilmiştir; Chrome sadece kullanıcı hareketi (tıklama)
      // ister. Otomatik yeniden başlatmayı durdur (gesture'sız restart sonsuz not-allowed
      // döngüsü yapar); kullanıcının sonraki tıklaması start() ile tanımayı toparlar.
      onError("Mikrofonu başlatmak için ekrana bir kez tıkla. Sürerse Chrome'da mikrofon iznini ver.");
      shouldListen = false;
    } else if (event.error === "no-speech") {
      // Normal, just restart
    } else if (event.error === "aborted") {
      // Expected during pause
    } else {
      console.warn("[voice] recognition error:", event.error);
    }
  };

  return {
    start() {
      shouldListen = true;
      paused = false;
      try {
        recognition.start();
      } catch {
        // Already started
      }
    },
    stop() {
      shouldListen = false;
      paused = false;
      recognition.stop();
    },
    pause() {
      paused = true;
      recognition.stop();
    },
    resume() {
      paused = false;
      if (shouldListen) {
        try {
          recognition.start();
        } catch {
          // Already started
        }
      }
    },
  };
}

// ---------------------------------------------------------------------------
// Audio Player
// ---------------------------------------------------------------------------

export interface AudioPlayer {
  enqueue(base64: string): Promise<void>;
  playUrl(url: string): Promise<void>;
  stop(): void;
  getAnalyser(): AnalyserNode;
  onFinished(cb: () => void): void;
}

export function createAudioPlayer(): AudioPlayer {
  const audioCtx = new AudioContext();
  const analyser = audioCtx.createAnalyser();
  analyser.fftSize = 256;
  analyser.smoothingTimeConstant = 0.8;
  analyser.connect(audioCtx.destination);

  const queue: AudioBuffer[] = [];
  let isPlaying = false;
  let currentSource: AudioBufferSourceNode | null = null;
  let finishedCallback: (() => void) | null = null;

  function playNext() {
    if (queue.length === 0) {
      isPlaying = false;
      currentSource = null;
      finishedCallback?.();
      return;
    }

    isPlaying = true;
    const buffer = queue.shift()!;
    const source = audioCtx.createBufferSource();
    source.buffer = buffer;
    source.connect(analyser);
    currentSource = source;

    source.onended = () => {
      if (currentSource === source) {
        playNext();
      }
    };

    source.start();
  }

  return {
    async enqueue(base64: string) {
      // Resume audio context (browser autoplay policy)
      if (audioCtx.state === "suspended") {
        await audioCtx.resume();
      }

      try {
        const binary = atob(base64);
        const bytes = new Uint8Array(binary.length);
        for (let i = 0; i < binary.length; i++) {
          bytes[i] = binary.charCodeAt(i);
        }
        const audioBuffer = await audioCtx.decodeAudioData(bytes.buffer.slice(0));
        queue.push(audioBuffer);
        if (!isPlaying) playNext();
      } catch (err) {
        console.error("[audio] decode error:", err);
        // Skip bad audio, continue
        if (!isPlaying && queue.length > 0) playNext();
      }
    },

    // Statik bir ses dosyasını (ör. önceden üretilmiş karşılama) aynı analyser üzerinden çalar
    // — böylece orb sese tepki verir ve bittiğinde onFinished tetiklenir (TTS ile aynı yol).
    async playUrl(url: string) {
      if (audioCtx.state === "suspended") {
        await audioCtx.resume();
      }
      const resp = await fetch(url);
      const arr = await resp.arrayBuffer();
      const audioBuffer = await audioCtx.decodeAudioData(arr);
      queue.push(audioBuffer);
      if (!isPlaying) playNext();
    },

    stop() {
      queue.length = 0;
      if (currentSource) {
        try {
          currentSource.stop();
        } catch {
          // Already stopped
        }
        currentSource = null;
      }
      isPlaying = false;
    },

    getAnalyser() {
      return analyser;
    },

    onFinished(cb: () => void) {
      finishedCallback = cb;
    },
  };
}

// ---------------------------------------------------------------------------
// Clap Detector — mikrofon enerjisinde ani sıçrama (alkış) yakalar
// ---------------------------------------------------------------------------

export interface ClapDetector {
  start(): Promise<void>;
  stop(): void;
}

/**
 * Mikrofon girişini dinler, ani yüksek enerji sıçraması (alkış) olunca onClap çağırır.
 * Uyandırma için kullanılır. Sürekli konuşmayı tetiklemesin diye yüksek eşik + debounce var.
 */
export function createClapDetector(onClap: () => void): ClapDetector {
  let audioCtx: AudioContext | null = null;
  let analyser: AnalyserNode | null = null;
  let stream: MediaStream | null = null;
  let raf = 0;
  let running = false;
  let lastClap = 0;

  // Hareketli ortalama (gürültü tabanı) — alkış bunun çok üstünde bir sıçrama
  let baseline = 0.02;
  let buf = new Uint8Array(0);

  function loop() {
    if (!running || !analyser) return;
    raf = requestAnimationFrame(loop);
    analyser.getByteTimeDomainData(buf);

    // RMS enerji (0..1 civarı)
    let sum = 0;
    for (let i = 0; i < buf.length; i++) {
      const v = (buf[i] - 128) / 128;
      sum += v * v;
    }
    const rms = Math.sqrt(sum / buf.length);

    const now = performance.now();
    // Alkış: gürültü tabanının çok üstünde keskin sıçrama + mutlak eşik
    const isSpike = rms > baseline * 6 && rms > 0.18;
    if (isSpike && now - lastClap > 800) {
      lastClap = now;
      onClap();
    }

    // Tabanı yavaşça güncelle (sadece sıçrama değilken), düşük tut
    if (!isSpike) baseline += (Math.min(rms, 0.1) - baseline) * 0.02;
  }

  return {
    async start() {
      if (running) return;
      try {
        stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        audioCtx = new AudioContext();
        if (audioCtx.state === "suspended") await audioCtx.resume();
        const src = audioCtx.createMediaStreamSource(stream);
        analyser = audioCtx.createAnalyser();
        analyser.fftSize = 1024;
        buf = new Uint8Array(analyser.fftSize);
        src.connect(analyser);
        running = true;
        loop();
      } catch (err) {
        console.warn("[clap] mic access failed:", err);
      }
    },
    stop() {
      running = false;
      if (raf) cancelAnimationFrame(raf);
      stream?.getTracks().forEach((t) => t.stop());
      stream = null;
      audioCtx?.close();
      audioCtx = null;
      analyser = null;
    },
  };
}
