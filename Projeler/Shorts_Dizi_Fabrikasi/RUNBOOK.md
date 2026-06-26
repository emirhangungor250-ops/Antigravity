# RUNBOOK: Shorts Dizi Fabrikası (Tam Otomatik AI Mini Dizi Fabrikası)

## Ne yapar

Verilen senaryodan tam otomatik YouTube Shorts mini dizisi üretir. Önce kalıcı bir "dizi kitabı" kurulur (karakterler, sesler, ortamlar, stil). Sonra her bölüm sahne sahne Kie Gemini Omni ile üretilir, ffmpeg ile birleştirilir ve Google Drive'a yüklenir.

## Çalıştırma

Üç komut var, hepsi `python main.py` üzerinden:

```
python main.py kur   --senaryo senaryo.md --seri <slug>   # dizi kitabı kurulumu (1 kez)
python main.py bolum --seri <slug> [--konu "..."] [--devam] [--test]
python main.py durum --seri <slug>                        # seri durumu + Kie bakiyesi
```

- `--devam`: yarıda kesilen bölümü kaldığı yerden sürdürür. Aynı task'a yeniden poll yapılır, çifte ödeme olmaz.
- `--test`: ucuz duman testi (2 sahne, 4 sn, 720p). Sayaç ve hafıza güncellenmez.
- `durum` seri vermeden çağrılırsa mevcut serileri ve bakiyeyi listeler.

## Deploy

Proje lokalde komutla çalışır. `railway.json` ileride bir sunucuya taşımak için hazır: `builder: RAILPACK`, `startCommand: python main.py`, `restartPolicyType: ON_FAILURE`.

Railway'e taşınırsa:

- Monorepo'da servis ayarında **rootDirectory = projenin klasör yolu** dolu olmalı. Boşsa deploy sessizce FAILED olur.
- CLI arg verilmezse komut `MODE` ve `SERI_SLUG` env'lerinden okunur. Cron için `MODE=bolum` + `SERI_SLUG=<slug>` yeterli.
- Drive için `GOOGLE_OUTREACH_TOKEN_JSON` env'i zorunlu olur (lokalde oauth token dosyasından okunur).
- Dikkat: seri durumu `seriler/` altında diskte yaşar. Railway'de kalıcı volume yoksa state her deploy'da sıfırlanır. Taşımadan önce bu çözülmeli.

## Env Değişkenleri

Tam liste `.env.example`'da. Lokalde `.env` dosyasından yüklenir.

- `ENV`: `development` ise DRY_RUN otomatik açılır (tüm dış API'ler taklit, sıfır maliyet). Production'da `production` olmalı.
- `DRY_RUN`: `1` ise production'da bile taklit mod.
- `KIE_API_KEY`: zorunlu. Kie AI video + görsel + ses üretimi.
- `ANTHROPIC_API_KEY`: zorunlu. Senarist ve dizi kitabı beyni.
- `IMGBB_API_KEY`: zorunlu. Referans görsellerin public host'u.
- `KIE_BASE_URL`: varsayılan `https://api.kie.ai/api/v1/`.
- `BRAIN_MODEL`: senarist modeli. Varsayılan ucuz model (`claude-haiku-4-5`). Pahalı model gerekmedikçe değiştirme.
- `QC_MODEL`: varsayılan `claude-haiku-4-5` (kare kontrol, ucuz vision).
- `GOOGLE_OUTREACH_TOKEN_JSON`: Railway'de Drive için zorunlu. Lokalde boş kalır, oauth token dosyası kullanılır.
- `DRIVE_FOLDER_URL`: hedef Drive klasörü. Boşsa ilk çalıştırmada bir kök klasör otomatik açılır.
- `KIE_CREDITS_PER_USD`: varsayılan 200. Bakiye gösteriminde dolar çevirisi için.
- `MAX_EPISODE_CREDITS`: 0 = limitsiz. Pozitifse her sahne öncesi bütçe kontrolü yapılır.
- `MODE` / `SERI_SLUG`: Railway cron uyumu. Lokal kullanımda boş bırak.

## Sorun Giderme

| Belirti | İlk bak | Çöz |
|---------|---------|-----|
| Açılışta `BOOT ERROR: CRITICAL STARTUP FAILURE` | Hata mesajındaki env var adı | Zorunlu key eksik (KIE / ANTHROPIC / IMGBB). `.env`'i kendi anahtarlarınla doldur |
| Bölüm yarıda kaldı, "bekliyor" mesajı | `python main.py durum --seri <slug>` ile bekleyen sahneler | Aynı komutu `--devam` ile çalıştır, kaldığı sahneden sürer |
| Kie 401/403 veya sahne üretimi hep fail | `durum` çıktısındaki Kie bakiyesi | Bakiye bittiyse kredi yükle; bakiye varsa `KIE_API_KEY`'i yenile |
| "Bölüm bütçesi aşıldı" hatası | `seriler/<slug>/bolumler/<ep>/maliyet.json` | `MAX_EPISODE_CREDITS`'i yükselt veya 0 yap, `--devam` ile sürdür |
| Video üretildi ama Drive'da yok | DRY_RUN açık mı; OAuth token var mı | `ENV=production` yap; Drive token dosyanı veya `GOOGLE_OUTREACH_TOKEN_JSON` env'ini kontrol et |

QC notu: `qc_report.json`'daki tier2 bayrakları üretimi BLOKLAMAZ. Sadece şüpheli sahneleri işaretler, log'a uyarı düşer.

## Loglar Nerede

- Çalışma logu stdout'a akar (INFO seviyesi). Kalıcı log dosyası yok; Railway'e taşınırsa deploy log'unda görünür.
- Kalıcı durum `seriler/<slug>/` altında JSON olarak yaşar: `bible.json` (dizi kitabı), `bolumler/<ep>/episode.json` (sahne durumları), `qc_report.json` (kalite kontrol), `maliyet.json` (kredi + LLM maliyeti), `kimlik.html` (kimlik kartı).
- Her sahne geçişi diske atomic yazılır. Süreç kesilse bile state bozulmaz.
- Hızlı özet için: `python main.py durum --seri <slug>`.

## Yedekleme ve Geri Yükleme (ÖNEMLİ)

`seriler/` klasörünün tamamı `.gitignore`'da (maliyet.json kredi bakiyesi içerdiği için). Yani seri durumu **repoya girmez** — sadece bu makinede yaşar. Final videolar ve kimlik kartı Drive'a yüklenir ama `bible.json` Drive'a normalde gitmez.

**Neden kritik:** `bible.json` geri getirilemez. İçinde Kie karakter kimliği (`characterId`), ses kimlikleri (`kieAudioId`), referans görsel URL'leri ve `series_seed` var. Bunlar kaybolursa serinin sonraki bölümleri **aynı karakter/ses/stille devam edemez** — sıfırdan yeni kimlik kurmak gerekir. Makine değişir veya disk silinirse seri fiilen ölür.

**Yedek alma** (seri klasörünün `_state_yedek/` alt klasörüne, Drive'a):

```python
# proje kökünden: .venv/bin/python
import os
from dotenv import load_dotenv; load_dotenv()
from core import drive_service as ds

SLUG, TITLE = '<seri-slug>', '<Seri Başlığı>'   # kendi serin
folder_id, _ = ds.ensure_series_folder(TITLE)
svc = ds.get_drive_service()
state_id = ds.get_or_create_subfolder(svc, folder_id, '_state_yedek')
base = f'seriler/{SLUG}'
for path, name in [
    (f'{base}/bible.json', 'bible.json'),
    (f'{base}/series_state.json', 'series_state.json'),
]:
    if os.path.exists(path):
        ds.upload_file_to_folder(path, state_id, name, mimetype='application/json')
```

> Not: `upload_file_to_folder` aynı isim varsa **üzerine yazmaz** (resume mantığı). Güncel state'i yeniden yedeklemek için ya Drive'da eski dosyayı sil, ya da isme tarih ekle (`bible_2026-06-14.json`).

**Geri yükleme:** `_state_yedek/`'ten `bible.json` + `series_state.json`'ı indir, `seriler/<slug>/` altına koy. `bolumler/` klasörlerini elle yeniden oluşturmaya gerek yok — yeni bölüm `bolum` komutuyla sıfırdan üretilir; sadece dizi kitabı (bible) ve seri hafızası (series_state) yerinde olmalı.

**Açık iyileştirme:** Bu yedek şu an manuel. İdeali: `pipeline/produce_episode.py` her başarılı bölüm sonunda `bible.json` + `series_state.json`'ı `_state_yedek/`'e otomatik yüklesin (tarihli isimle). Henüz eklenmedi.
