# RUNBOOK — Teleprompter_Senkron

Notion script veritabanında **"hazır"** olan video script'lerini alır. Gövdeyi AI ile temiz prompter metnine çevirir. Sonucu Google Drive'daki teleprompter klasörüne `{gün} - {kart adı}.txt` olarak bırakır. Tabletteki teleprompter uygulaması bu klasörü kendisi senkronlar; script çekimde tablette belirir.

## Deploy

İki seçenek var:

- **GitHub Actions cron (önerilen):** `.github/workflows/sync.yml` dosyasını ekleyin (örnek README'de). 2 saatte bir + elle tetik (Actions sekmesi → "Run workflow"). Workflow her koşuda repo'nun güncel halini çeker; kodu main'e push etmek yeterli.
- **Railway cron:** `railway.json` pakette hazır (`python sync.py`). İsterseniz kendi Railway hesabınıza deploy edip cron olarak koşturabilirsiniz.
- **Lokal:** `python sync.py` (gerçek) veya `python sync.py --dry-run` (Drive'a dokunmaz, planı yazar).

Secret'lar (Actions repo secret olarak): `NOTION_REELS_TOKEN`, `PROMPTER_NOTION_DB_ID`, `PROMPTER_DRIVE_FOLDER_ID`, `GOOGLE_DRIVE_TOKEN_JSON`, `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`.

## Güvenlik kapısı

`EXPECTED_DRIVE_DOMAIN` ayarlıysa, kod yazmadan önce Drive token'ının o domain'e ait bir Google hesabına bağlı olduğunu doğrular. Hesap eşleşmezse hiçbir şey yazmadan durur ve log'a "DURDU: beklenen '<domain>' hesabı değil" düşer. Boş bırakırsanız kapı kapalıdır.

## Env değişkenleri

Tam liste `.env.example`'da. Özet:

- `NOTION_REELS_TOKEN` (zorunlu) — Notion DB erişimi. Alternatif ad: `PROMPTER_NOTION_TOKEN`.
- `PROMPTER_NOTION_DB_ID` (zorunlu) — script DB ID'niz.
- `PROMPTER_DRIVE_FOLDER_ID` (zorunlu) — teleprompter uygulamasının açtığı klasör ID'si.
- `GOOGLE_DRIVE_TOKEN_JSON` (sunucuda zorunlu) — TAM `drive` scope OAuth token, tek satır JSON. Lokal'de env yerine proje kökündeki `drive-full-token.json` dosyasından okunur.
- `OPENAI_API_KEY` — AI temizleme birincil modeli (OpenAI). Model `OPENAI_MODEL` ile değişir.
- `ANTHROPIC_API_KEY` — OpenAI yoksa veya patlarsa Claude fallback. Model `ANTHROPIC_MODEL` ile değişir.
- `NOTION_STATUS_PROPERTY` / `NOTION_STATUS_READY` (opsiyonel) — DB şemanız farklıysa.
- `EXPECTED_DRIVE_DOMAIN` (opsiyonel) — güvenlik kapısı.

## Sorun giderme

| Belirti | Bak | Çöz |
|---------|-----|-----|
| Run fail: "Drive token geçersiz ve yenilenemiyor" | Çalıştırma log'undaki Senkron adımı | `python core/reauth_drive_full.py` ile token'ı yeniden üret (tarayıcı açılır, doğru Google hesabıyla izin ver). Sonra `GOOGLE_DRIVE_TOKEN_JSON` secret'ını yeni `drive-full-token.json` içeriğiyle güncelle |
| "DURDU: beklenen ... hesabı değil" | Log'daki "Drive hesabı:" satırı | Token yanlış Google hesabıyla üretilmiş. reauth'u doğru hesapla tekrarla, ya da `EXPECTED_DRIVE_DOMAIN`'i düzelt |
| Run fail: "Notion token yok" veya Notion 401 | Secret'lar | `NOTION_REELS_TOKEN` eksik veya süresi dolmuş; yenisini koy. DB'yi integration ile paylaştığından emin ol |
| Script tablette görünmüyor ama run yeşil | Log'daki özet satırı (bırakılan / zaten-var / atlanan) | Kart adı veya gövdesi boşsa atlanır. Klasörde aynı adlı dosya zaten varsa dokunulmaz (tasarım gereği: bir kez bırak). Güncelleme gerekiyorsa eski dosyayı teleprompter UYGULAMASINDAN sil, Drive'dan silme (uygulama geri getirir) |
| AI temizleme patlıyor | Log'da "(OpenAI düştü, Claude'a geçildi...)" | Tek başına sorun değil, fallback çalışıyor. İkisi de patlarsa `ANTHROPIC_API_KEY` secret'ını kontrol et |
| Şema hatası: status property bulunamadı | Notion DB'nizdeki property adı | `NOTION_STATUS_PROPERTY` ve `NOTION_STATUS_READY`'i kendi DB'nizdeki ada göre ayarla |

## Loglar nerede

GitHub Actions kullanıyorsanız: repo → **Actions** sekmesi → ilgili workflow → çalıştırma → Senkron adımı. Her koşu sonunda tek satır özet basılır: `Özet — bırakılan:X zaten-var:Y atlanan:Z`. Lokal çalıştırmada aynı çıktı terminale düşer.
