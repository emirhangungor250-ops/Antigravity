# Sesli Asistan (JARVIS)

**Just A Rather Very Intelligent System.** Mac'te çalışan, sesle konuşulan bir
yapay zeka asistanı. Konuşursunuz, size sesle yanıt verir; ekranda sesinize tepki
veren bir parçacık küresi (Three.js) döner.

Asistan Apple Takvim, Mail ve Notlar'a bağlanır; web'de arama yapar, gününüzü
planlamanıza yardım eder, ekranınızdaki açık pencereleri görüp bağlam kurar ve
Claude Code oturumu açarak gerçek geliştirme işleri yapabilir. Tüm yanıtlar
Türkçe verilir; karakter MCU'daki JARVIS gibi sakin, kuru espirili bir asistandır.

> Orijinal proje: **Ethan Rogers** (ethanplus.ai), açık kaynak JARVIS sesli
> asistanı. Bu kopya, AI Factory starter kit'i için **jenerikleştirildi**: kişisel
> isim/e-posta çıkarıldı, env ile parametrelendirildi, sahibe özel canlı-yayın
> reklam akışı (Higgsfield) kaldırıldı. Lisans ve atıf `LICENSE` dosyasında aynen
> korunmuştur (telifi orijinal yazara aittir).

---

## Ne yapar

- **Sesli sohbet** — doğal konuşursunuz, sesli yanıt alırsınız.
- **Yazılım kurar** — "bana bir açılış sayfası yap" deyin, Claude Code işi yapsın.
- **Takvimi okur** — "bugün programımda ne var?"
- **Maili okur** — "okunmamış mesaj var mı?" (güvenlik için sadece okuma).
- **Web'de arar** — "en iyi restoranları bul."
- **Görev ve not yönetir** — hatırlatma oluşturur, not kaydeder.
- **Bilgi hatırlar** — tercihlerinizi sonraki oturumlarda anımsar.
- **Ekranı görür** — açık uygulamaları bilir, bağlama göre yanıt verir.

## Gereksinimler

- **macOS** (Takvim/Mail/Notlar için AppleScript kullanır)
- **Python 3.11+**
- **Node.js 18+**
- **Google Chrome** (Web Speech API için)
- **OpenRouter API anahtarı** — beyni (LLM) çalıştırır
- **ElevenLabs (veya Fish Audio) API anahtarı** — sesi üretir
- **Claude Code CLI** (opsiyonel) — geliştirme görevlerini açmak için

## Kurulum

```bash
# 1. Ortam dosyasını hazırla
cp .env.example .env
# .env içindeki <...> alanlarını kendi anahtarlarınla doldur (aşağıya bak)

# 2. Python bağımlılıkları
pip install -r requirements.txt

# 3. Frontend bağımlılıkları
cd frontend && npm install && cd ..

# 4. SSL sertifikası (güvenli WebSocket için, opsiyonel)
openssl req -x509 -newkey rsa:2048 -keyout key.pem -out cert.pem -days 365 -nodes -subj '/CN=localhost'

# 5. Backend'i başlat (Terminal 1)
python server.py

# 6. Frontend'i başlat (Terminal 2)
cd frontend && npm run dev
```

Tek komutla kurulum + başlatma için `./baslat.sh` da kullanabilirsiniz (idempotent:
ilk çalıştırma her şeyi kurar, sonrakiler sadece başlatır). Tarayıcıda sayfayı bir
kez tıklayıp sesi açın, sonra konuşun.

## Ortam değişkenleri

`.env.example` dosyasını `.env` olarak kopyalayıp doldurun:

| Değişken | Zorunlu | Açıklama |
|---|---|---|
| `OPENROUTER_API_KEY` | evet | LLM beyni (openrouter.ai) |
| `ELEVENLABS_API_KEY` | ses için | Türkçe TTS (elevenlabs.io). Alternatif: `FISH_API_KEY` |
| `ELEVENLABS_VOICE_ID` | ses için | Kullanmak istediğiniz sesin kimliği |
| `JARVIS_MODEL` / `JARVIS_SMALL_MODEL` | hayır | Model seçimi (ucuz varsayılan: `openai/gpt-4o-mini`) |
| `USER_NAME` | hayır | Asistanın size hitabı. Boşsa isimsiz "efendim" kullanılır |
| `CALENDAR_ACCOUNTS` | hayır | Virgülle ayrılmış takvim e-postaları (`auto` = otomatik) |

Varsayılan modeller bilerek ucuz tutulmuştur. Daha güçlü bir model isterseniz
`JARVIS_MODEL`'i OpenRouter anahtarınızın eriştiği herhangi bir modele çevirin.

## Mimari

| Katman | Teknoloji |
|---|---|
| Backend | FastAPI + Python (`server.py`) |
| Frontend | Vite + TypeScript + Three.js |
| İletişim | WebSocket (JSON mesaj + ikili ses) |
| LLM | OpenRouter (OpenAI-uyumlu istemci) |
| TTS | ElevenLabs veya Fish Audio |
| Sistem | macOS entegrasyonları için AppleScript |

## Lisans

Kişisel, ticari olmayan kullanım için ücretsizdir. Ticari kullanım lisans
gerektirir — ayrıntı `LICENSE` dosyasında. Telif orijinal yazara (Ethan Rogers)
aittir.

> **Uyarı:** Bu bağımsız bir hayran projesidir; Marvel/Disney veya ilgili
> kuruluşlarla bağlantısı yoktur. JARVIS adı ve karakteri Marvel'a aittir.
