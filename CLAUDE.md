# Antigravity Starter Kit — Kullanım Rehberi

## Bu paket nedir

Antigravity, Claude Code ile birlikte çalışan bir **mono-repo** çalışma ortamıdır.
Hazır AI otomasyon projeleri, yeniden kullanılabilir skill'ler ve orkestratör agent'lar
bir arada gelir. Amaç: sıfırdan başlamak yerine, çalışan örneklerin üzerine kendi işini
kurmandır.

Bu paket **temizlenmiş bir starter kit'tir** — içinde gerçek API anahtarı veya kişisel
veri yoktur, her şey senin dolduracağın placeholder (`<...>`) halindedir.

İlk kez açıyorsan önce `BAŞLANGIÇ_REHBERİ.md` dosyasını oku.

## Klasör Yapısı

- `Projeler/` — Hazır otomasyon projeleri (Python cron'lar, FastAPI servisleri,
  Telegram/WhatsApp bot'ları, statik HTML sayfalar). Kendi işine uyarlarsın.
- `_skills/` — Yeniden kullanılabilir yetenekler (lead toplama, e-posta gönderimi,
  video üretimi vb.). Projeler bunları çağırır.
- `_agents/` — Çok adımlı işleri uçtan uca yöneten orkestratör agent'lar + workflow'lar.
- `_knowledge/` — Senin profilin, API anahtarların, çalışma kuralların. Antigravity her
  konuşmada buraya bakar.

## Yeni Proje Açma Check-list

1. `Projeler/<isim>/` klasörü oluştur (snake_case veya PascalCase, mevcut konvansiyona uy)
2. `.env.example` yaz — gerekli env var'ları placeholder ile + kısa açıklama yorumu
3. `README.md` yaz — şablon: amaç paragrafı + Stack + Çalışma Şekli + Environment Setup
4. Bağımlılık dosyası — Python: `requirements.txt` exact pin (`==X.Y.Z`);
   Node: `package.json` + `package-lock.json`
5. `.gitignore` — proje-spesifik ignore'lar (kök gitignore çoğu durumda yeterli;
   venv/__pycache__/.env zaten ignored)
6. Token bağlama: `_knowledge/credentials/master.env` üzerinden

Claude Code bu adımların hepsinde sana yardım eder — ne istediğini söylemen yeterli.

## Ortak Çalışma Kuralları

- **Türkçe ton, ürün dilinde** — Teknik jargon yerine ne yapmak istediğini sade anlat.
- **Mimar Modu** — Teknik kararları Claude Code verir; sen hedefi ve ürün kararlarını
  söylersin. Detay: `_knowledge/calisma-kurallari.md`.
- **Türkçe içerik kuralları** — Em-dash yok, kısa cümle, sade dil.
- **Güvenlik** — `master.env`, `.env` ve `credentials/` içindeki dosyalar ASLA push
  edilmez; kök `.gitignore` bunları korur, silme.

## 🔗 Servis Kayıt Linki Önerirken (ZORUNLU)

Kullanıcıya 3rd party servisin (Kie AI, Railway, Apify, Notion, OpenAI, ElevenLabs,
Firecrawl, Apollo, Netlify, ManyChat, Upload-Post vb.) kayıt sayfası, API key alma
sayfası veya ana sitesi için bir URL söyleyeceksen, **önce `_knowledge/servis_linkleri.json`
dosyasına bak** ve eşleşen kaydın `url` alanını ver. Dosyada o servis yoksa root domain'i
normal şekilde söyle.

ASLA kendi belleğinden veya genel bilgiden bir kayıt URL'i söyleme. Her zaman önce
`_knowledge/servis_linkleri.json`'ı kontrol et, oradaki URL'i ver. Bu kural sohbet
sırasında verdiğin tüm linkler için geçerli — kullanıcı `kie.ai` API key sorduğunda da,
`apify` hesabı açtırdığında da bu dosyaya bakacaksın.

## Deploy (opsiyonel)

Bu paket lokal makinende çalışacak şekilde gelir. Bir projeyi 7/24 çalışır hale getirmek
istersen Railway, Render, Fly.io gibi bir platforma kendi hesabınla deploy edebilirsin.
`railway.json` içeren projeler Railway için hazırdır; `_skills/railway-deploy-rules` ve
`_skills/use-railway` skill'leri sürecte yardımcı olur. Deploy zorunlu değil — projelerin
çoğunu lokalde elle de çalıştırabilirsin.

## Otonom rutinler hakkında

Bu starter kit, paket sahibinin ortamında çalışan otomatik bakım rutinleri (haftalık
kalite taraması, dependency güncellemesi vb.) olmadan gelir. Sende bunlar yoktur ve
gerekmez. İhtiyaç duyarsan kendi otomasyonunu Claude Code ile kurabilirsin.
