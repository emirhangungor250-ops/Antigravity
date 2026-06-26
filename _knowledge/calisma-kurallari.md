# Çalışma Kuralları ve Tercihler

Bu dosya, Antigravity ile çalışırken birikmesi gereken kişisel tercihleri ve kuralları içerir.
Kendi tercihlerinizi buraya ekleyin; Antigravity her konuşmada buraya bakar.

---

## Genel Çalışma Tarzı

- **Dil:** Kendi dilinizi yazın (kod ve teknik dosyalar İngilizce olabilir)
- **İletişim tarzı:** Kısa mı uzun mu, teknik mi sade mi — tercihinizi buraya yazın

## Proje Yapısı

```
Antigravity/
├── _agents/              → Agent'lar ve Workflow'lar
│   ├── musteri-kazanim/  → Lead + Outreach orkestratörü
│   ├── icerik-uretim/    → İçerik pipeline orkestratörü
│   ├── yayinla-paylas/   → Deploy + Export orkestratörü
│   └── workflows/        → Slash command workflow'ları
├── _skills/              → Kalıcı yetkinlikler (skill'ler)
├── _knowledge/           → Bu klasör (manuel hafıza)
│   └── credentials/      → 🔐 Merkezi şifre/token deposu
└── Projeler/             → Tüm proje klasörleri
```

## Aktif Projeler

*(Bu tabloyu kendi projelerinizle doldurun)*

| Proje | Açıklama | Durum |
|---|---|---|
| | | |

## 🔐 Şifre/Token Yönetim Kuralları (OTOMATİK)

Bu kurallar her proje oluşturma/düzenleme sırasında **otomatik olarak** uygulanır:

### Otomatik Tetikleme
- ✅ Yeni proje oluşturulduğunda → `sifre-yonetici` skill'ini oku ve çalıştır
- ✅ Bir projeye API kullanan kod eklendiğinde → ihtiyaç analizi yap
- ✅ Yeni API/token verildiğinde → önce `master.env`'e ekle, sonra projelere dağıt
- ✅ Deploy öncesinde → `.env` ve Service Account bağlantılarını doğrula

### Merkezi Depo
- **Tokenlar:** `_knowledge/credentials/master.env`
- **Google Service Account:** `_knowledge/credentials/google-service-account.json`
- **OAuth Dosyaları:** `_knowledge/credentials/oauth/`
- **Skill:** `_skills/sifre-yonetici/SKILL.md`
- **Workflow:** `/sifre-bagla`

### Token Güncellemesi
Yeni bir token verildiğinde:
1. `master.env`'deki ilgili satırı güncelle
2. `_knowledge/api-anahtarlari.md`'yi senkronize et
3. Etkilenen projeleri bildir

## 📋 Notion Workspace Kuralı

Notion kullanıyorsanız:
- Integration token'ları `master.env`'de saklayın (`NOTION_TOKEN`)
- Database ID'lerini proje `.env`'lerinde saklayın, koda gömmeyin
- Notion MCP sadece entegrasyonunuzla **paylaşılmış** sayfalara erişir — 404 alırsanız önce paylaşımı kontrol edin

## 🚀 Deploy Güvenlik Kuralları (ZORUNLU)

### Push Öncesi:
1. `python3 -m py_compile *.py` — syntax kontrolü
2. Tüm .py dosyalarını `importlib.import_module()` ile import et
3. `tests/` veya `run_test.py` varsa çalıştır
4. **Caller ↔ Callee imza doğrulaması** — entry point'teki fonksiyon çağrı argümanları tanımlarıyla uyumlu mu (import testi bunu yakalamaz)
5. Hata varsa → ❌ PUSH YAPMA

### Deploy Sonrası:
1. SUCCESS olduktan sonra 60 saniye bekle
2. `deploymentLogs` ile logları çek
3. `AttributeError`, `ImportError`, `SyntaxError`, `Traceback` ara
4. Fatal error varsa → düzelt, tekrar push, tekrar deploy

## 🔧 Railway Sistem Bağımlılıkları Kuralı

> **Railway, Nixpacks builder kullanır. `Aptfile` ve `apt.txt` dosyaları YOKSAYILIR!**

| Durum | Doğru Çözüm |
|---|---|
| Sistem paketi gerekiyor (ffmpeg, chromium vb.) | `nixpacks.toml` → `[phases.setup] nixPkgs = ["ffmpeg"]` |
| `Aptfile` veya `apt.txt` bulunuyor | ❌ SİL — Nixpacks bunları yoksayar |
| Sistem binary'si kontrolü | `config.py` → `self._check_system_deps(["ffmpeg"])` (fail-fast) |

## 🔍 Hata Düzeltme Protokolü (ZORUNLU)

> **Hata raporlandığında HEMEN koda dalma. Önce analiz, sonra plan, sonra fix.**

1. **3-Soru Analizi (fix yazmadan ÖNCE):**
   - Bu hata TAM OLARAK nereden kaynaklanıyor? (kök neden, semptom değil)
   - Bu fix başka nereleri etkiler? (`grep` ile tüm referansları tara)
   - Bu hata tipi `hatalar-ve-cozumler.md`'de var mı?
2. **Çözüm planını sun** → Onay al → Fix uygula
3. **Fix sonrası → tüm etkilenen yerleri test et**
4. **Yeni pattern ise → `hatalar-ve-cozumler.md`'ye ekle**

## 🎯 Küçük Parça Prensibi (ZORUNLU)

> **Büyük değişiklik yapıp sonunda test etme. Her parçayı ayrı test et.**

- Her değişiklik maks 1 dosya veya 1 fonksiyon kapsamında olmalı
- Push öncesi her dosya değişikliğini ayrı ayrı test et
- 3'ten fazla dosya değişiyorsa → "Bu değişikliği X parçaya bölmemi öneriyorum" de
- Her parça bittikten sonra → syntax + import testi çalıştır

## 🛡️ Stabilize-Lite (her deploy'da ZORUNLU)

1. Deploy status → SUCCESS mi?
2. Son 100 log'da fatal error var mı?
3. Tüm env var'lar Railway'de tanımlı mı?
4. Cron ise → manuel tetikle, 90 sn bekle, log kontrol et
5. Platform checklist → `_knowledge/platform-checklists/railway.md` kontrol et

## 📊 Görev Raporu

> Her görev tamamlandığında anlaşılır, teknik olmayan bir rapor sunulur.

```
📋 GÖREV RAPORU — [Proje/Görev Adı]

🎯 Ne yapıldı: [1 cümleyle açıklama]

✅ Çalışıyor mu?
   - Yayına alındı mı? → Evet/Hayır
   - Gerçekten çalışıyor mu? → Evet (log'da hata yok) / Hayır (şu hata var)
   - Bekleyen risk var mı? → Yok / "48 saat izlemeye alındı"

⚡ Bir şey yapman gerekiyor mu? → Hayır / Evet: [basit talimat]

🔢 Kalite Skoru: X/5
   1. Kod hatasız mı?  2. Doğru çalışıyor mu?  3. Güvenli mi (şifre sızdırmaz)?
   4. Başka projeleri bozmuyor mu?  5. İzlemeye alındı mı?
```

## 📖 API Contract-First Development (ZORUNLU)

Herhangi bir 3. parti API entegrasyonu yazılmadan ÖNCE:
1. **Dökümantasyonu oku** — resmi API docs URL'sini not et
2. **1 adet curl/test isteği gönder** — gerçek başarılı response al
3. **Parametre isimlerini dökümantasyondan kopyala** — ASLA tahmin etme
4. Başarılı response gördükten SONRA kodu yaz

**Anti-pattern (YASAK):** Parametre ismini hafızadan/tahminle yazmak, dökümantasyon okumadan entegrasyon kodlamak.

## 🧪 Sıfır Varsayım & Canlı Kanıt Doktrini (ZORUNLU)

> **"Log'da hata yok" ≠ "Çalışıyor". "Teorik olarak yazdım" = YASAK.**

Bir otomasyon "gerçek dünyada bir değişiklik" yapıyorsa (post paylaşmak, mail göndermek, video render almak, DB güncellemek):
1. **Fiziksel kanıt üretilecek** — "HTTP 200 döndü" yetmez
2. **Doğrulama agent'a aittir** — sonucun gerçekten oluştuğunu (video boyutu, mailin gelen kutusu, postun URL'si) agent test script'iyle doğrular
3. Nihai hedefin canlı sistemde oluştuğu kanıtlanmadan "görev bitti" denmez

## 🏗️ Proof of Concept Before Pipeline (ZORUNLU)

Yeni proje kurulmadan ÖNCE:
1. Kritik dış bağımlılıklar listelenir (video API, scraping, ödeme vb.)
2. Her biri 1 script/curl ile test edilir — "çalışıyor" kanıtı üretilir
3. Tüm core entegrasyonlar çalıştıktan SONRA pipeline/bot mimarisi kurulur

## 🤖 Otonom Contract Test (ZORUNLU)

Her pipeline projesi bir `contract_test.py` içerir:
1. Her dış API entegrasyonunu gerçek istek ile test eder (task oluştur → poll → URL al)
2. Çıktının erişilebilirliğini doğrular (dönen URL → HTTP 200 mü?)
3. Deploy öncesi agent tarafından çalıştırılır

**Kontrol eder:** auth geçerli mi, parametre isimleri doğru mu, task oluşuyor mu, polling başarılı mı, URL'ler erişilebilir mi.
**Kontrol edemez:** video/görsel kalitesi, içerik estetiği — bunu insan değerlendirir.

## 🧱 Antigravity Node Architecture (ANA) & Simülasyon Testi

> **Sorun:** "Happy Path" ile yazılıp canlıya alınan projeler, beklenmedik edge-case'lerde çöküyor.

### 1. Payload Record & Replay
Sistemin dış dünyadan tetiklendiği her fonksiyon (webhook, API endpoint, mesaj listener), çökmeden HEMEN ÖNCE gelen raw payload'u bir log dosyasına kaydeder. Debug ederken hayali parametre yerine bu gerçek snapshot ile lokalde "replay" testi yapılır.

### 2. Standart Provider Modülleri
Harici servislere her projede sıfırdan raw request atılmaz. `_skills/providers/` altında hataya dayanıklı sarmalayıcı modüller kullanılır. Bir node'un taşıması gerekenler:
- **Exponential Retry:** 500/502 hatalarında en az 3 retry (`tenacity`)
- **Timeout & Fallback:** Her HTTP isteğinin timeout'u olmalı, API yanıt vermezse fallback (örn. "fotoğraf servisi yanıt vermiyorsa gönderiyi text-only at, akışı kitleme")
- **Gözlemlenebilir Catch:** Genel `Exception` değil, açık mesaj — "🚨 [LinkedIn Node] API 422, resim boyutu limiti aşıldı"

### 3. Simülasyon / "Kıyamet" Testi
Sistem kurgulandıktan sonra bilerek "bozuk" mock veriler (empty payload, eksik key, hatalı auth) gönderilip script'in graceful kapandığı simüle edilmeden onaylanmaz. `mock_data` / `scratch_mock_e2e.py` ile uçtan uca senaryo simülasyonu yapılır.

## 🛠️ MCP ve Araç Kullanım Standartları

> Detaylı rehber: `_knowledge/mcp-ve-tool-optimizasyon-rehberi.md`

1. **Cerrahi Müdahale:** Dosyaları baştan yazmak yerine sadece değişen satırlar güncellenir
2. **Akıllı Okuma:** Sadece ihtiyaç duyulan kod bloğu okunur; `grep` birincil arama aracı
3. **Lokal Simülasyon:** Her kritik logic değişikliği `scratch/` altında test edilmeden deploy edilmez
4. **Sessiz Terminal:** `--silent` ve `head/tail` ile log kalabalığı önlenir

## Kesinlikle Yapılmaması Gerekenler

- API anahtarlarını hardcode etme — her zaman `master.env` veya env variable kullan
- Skill dosyalarını gereksiz yere değiştirme — skill'ler atomik ve kararlıdır
- `_knowledge/credentials/` klasöründeki dosyaları GitHub'a push etme
- Google Service Account JSON dosyasını kod içine gömme
- Kod sağlık kontrolü yapmadan GitHub'a push etme — import testi + testler ZORUNLU
- Smoke test yapmadan deploy'u tamamlanmış sayma
- README güncellemeden değişiklik push etme

## Tekrarlayan Talepler

*(Burası zamanla dolacak — önemli kararlar ve tercihler buraya eklenir)*
