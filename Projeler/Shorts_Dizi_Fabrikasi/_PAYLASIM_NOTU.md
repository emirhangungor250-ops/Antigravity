# Paylaşım Notu — Shorts Dizi Fabrikası

**Mod:** C (şablona çevrildi)

## Ne yapıldı

### Temizlenen sırlar
- Kaynaktaki `.env` CANLI anahtarlar içeriyordu (Kie API key, ImgBB API key, gerçek bir
  `sk-ant-...` Anthropic anahtarı). **`.env` pakete hiç kopyalanmadı** (allowlist `.env`'i
  eler); hedefte `.env` olmadığı bizzat doğrulandı.
- Kodda gömülü API anahtarı yok — tüm anahtarlar `os.environ` üzerinden okunuyor (config.py).
- `.env.example`'daki gerçekçi görünen placeholder'lar (`your_kie_api_key_here` vb.) açık
  `<KIE_API_KEY>` / `<ANTHROPIC_API_KEY>` / `<IMGBB_API_KEY>` formatına çevrildi.

### Scrub edilen kişisel veriler
- **`core/google_auth.py`** — sahibin 3 kişisel Google hesabı (kişisel Gmail, bir kurumsal
  hesap, bir özel domain hesabı), bu hesaplara ait e-posta adresleri ve token dosya adları
  vardı. Modül **tek jenerik Drive hesabına** indirildi: tüm e-postalar, kurumsal hesap
  referansları ve kullanılmayan Gmail/Sheets kısa yolları kaldırıldı. Sadece projenin
  gerçekten kullandığı `get_drive_service()` korundu (drive.file scope).
- **`brain/client.py`** — senaryo prompt'undaki "(sahibin adından)" ibaresi kaldırıldı.
- **`core/drive_service.py`** — docstring'deki sahibe özel başka bir proje yolu kaldırıldı;
  Drive kök klasör adı sabit sahip-proje adından `DRIVE_ROOT_FOLDER_NAME` env'ine taşındı
  (varsayılan jenerik "Shorts Dizi Fabrikasi").
- **`core/config.py`** — maliyet politikası yorumundaki kişisel onay ifadesi jenerik
  "pahalı modeli varsayılan yapma" notuna dönüştürüldü.
- **`README.md`** — baştan yazıldı (aşağıya bak).
- **`RUNBOOK.md`** — sahibin adı/proje adı, `_knowledge/credentials/master.env` referansları,
  yanlış pahalı model varsayılanı (`claude-opus-4-8`), sahibe özel örnek seri (`gece-bekcisi`),
  monorepo'ya özel `rootDirectory` yolu ve "outreach Drive hesabı" jenerikleştirildi.
- **`.env.example`** — maliyet uyarısı ve kayıt servisleri jenerik dile çevrildi.

### Silinen ağır/state dosyaları
- `seriler/` (tüm dizi state'i + üretilmiş `.mp4` sahne videoları + QC `.png`'leri +
  `maliyet.json` kredi bakiyesi + sahibin örnek dizisi "gece-bekcisi") **kopyalanmadı.**
- DRY_RUN doğrulama testinde geçici oluşan `seriler/` ve `outputs/fake/` test artefaktları
  silindi. Pakette hiçbir koşu çıktısı yok.

## Öğrenci ne yapmalı

1. `.env.example`'ı `.env` olarak kopyala; şu anahtarları kendi hesaplarınla doldur:
   - `KIE_API_KEY` (kie.ai) — video + görsel + ses üretimi (asıl maliyet kalemi)
   - `ANTHROPIC_API_KEY` (console.anthropic.com) — senarist beyni. İstersen başka bir LLM
     sağlayıcına geçip `brain/client.py`'i ona göre uyarlayabilirsin.
   - `IMGBB_API_KEY` (api.imgbb.com) — referans görsel host'u
2. **Google Drive token'ı** — bölümlerin Drive'a yüklenmesi için kendi Google Cloud
   projende OAuth credential üret (drive.file scope), dönen token JSON'ını
   `_knowledge/credentials/oauth/gmail-outreach-token.json`'a koy ya da
   `GOOGLE_OUTREACH_TOKEN_JSON` env'ine yapıştır.
3. **`senaryo_mini_test.md`** — örnek bir senaryodur; kendi dizi fikrinle değiştir veya
   yeni bir senaryo dosyası yaz, `--senaryo` ile ver.
4. Model maliyeti: `BRAIN_MODEL` varsayılanı bilinçli ucuz seçildi (`claude-haiku-4-5`).
   Pahalı bir model (Opus/Sonnet) varsayılan yapma; gerçekten gerekmedikçe ucuz modelde kal.
5. İlk denemeyi `ENV=development` ile yap — tüm dış API'ler taklit edilir, sıfır maliyet.
   Çalıştığını gördükten sonra `ENV=production`'a geç.

## Orijinal amaç → yeni jenerik çerçeve

- **Orijinal:** Sahibin kendi YouTube Shorts kanalı için, kendi senaryolarından, kendi
  Google/Drive hesaplarına bağlı, sahibe özel örnek dizilerle (gece bekçisi, kahve falı)
  çalışan kişisel mini dizi üretim hattı.
- **Yeni:** Aynı karakterlerle düzenli kısa video serisi üretmek isteyen herkes için jenerik
  bir fabrika. "Dizi kitabını bir kez kur, her bölümde aynen kullan" tutarlılık deseni;
  senaryo → dizi kitabı (karakter/ses/ortam/stil kilidi) → sahne sahne video → ffmpeg
  birleştirme → Drive yükleme akışı korundu. Senaryo, anahtarlar ve Drive hesabı tamamen
  öğrencinin; kod hiçbir kişisel veriye bağlı değil.
