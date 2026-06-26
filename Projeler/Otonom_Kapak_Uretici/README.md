# Otonom Kapak Üreticisi (V2)

> Reels (9:16) ve YouTube (16:9) kapak fotoğraflarını otonom üreten birleşik pipeline.
> Kie AI ile görsel üretim, Gemini Vision ile otomatik değerlendirme ve iterasyon.

Bu proje bir **şablondur**. Video kaynağı (Notion), depolama (Google Drive) ve
yüz referans fotoğrafları (anchor cutout'ları) size aittir — kendi içeriğinizle
doldurursunuz.

## Mimari

```
Otonom_Kapak_Uretici/
├── main.py                    # Orkestratör — COVER_TYPE env ile Reels/YouTube seçimi
├── trigger_example.py         # Tek video için manuel tetikleme örneği
├── run_manual.py              # Notion/Drive olmadan lokal üretim örneği
├── rourke_style_guide.md      # Görsel stil rehberi
├── agents/
│   ├── reels_agent.py         # 9:16 Reels kapak pipeline (3 tema × 2 varyasyon)
│   ├── youtube_agent.py       # 16:9 YouTube thumbnail pipeline (5 tema × 2 varyasyon)
│   ├── learnings.md           # Pipeline öğrenimleri / iyi pratikler
│   └── cutout_tags.json       # Anchor + cutout meta-veri tablosu (ŞABLON — siz doldurun)
├── core/
│   ├── config.py              # Fail-Fast env doğrulama (boot crash)
│   ├── notion_service.py      # Notion API (video listesi, revizyon paneli)
│   ├── drive_service.py       # Google Drive upload
│   ├── google_auth.py         # Merkezi Google OAuth token yönetimi
│   ├── ops_logger.py          # Notion Operations Logger
│   └── logger.py              # Standart Python logger
├── assets/
│   └── cutouts/               # Yüz referans fotoğrafları (BOŞ gelir — siz koyarsınız)
├── outputs/                   # Üretilen kapaklar (geçici, .gitignore)
├── requirements.txt
├── railway.json
└── nixpacks.toml
```

## Pipeline Akışı

1. **Notion Query** → "hazır" statüsündeki videoları getir
2. **Tema Üretimi** → Gemini ile 3 (Reels) / 5 (YouTube) konsept üret
3. **Identity Lock** → `cutout_tags.json`'dan sabit Master Anchor + Secondary Anchor'lar
4. **Görsel Üretim** → Kie AI'ya referans cutout'lar + sahne promptu gönderilir
5. **Self-Review** → Gemini Vision ile otomatik değerlendirme (metin, yüz kimliği, klişe kontrolü)
6. **Iterasyon** → Skor düşükse prompt iyileştirip yeniden üret
7. **Drive Upload** → Onaylanan kapağı Google Drive'a yükle
8. **Revizyon Paneli** → Notion sayfasına revizyon paneli ekle

## Identity Lock — Anchor Fotoğrafları

Pipeline, üretilen görsellerde tutarlı bir yüz çıkarması için "anchor" (yüz referansı)
fotoğraflarına ihtiyaç duyar. Bu şablonda `assets/cutouts/` klasörü **boş** gelir.

Kendi fotoğraflarınızı eklemek için: `assets/cutouts/README.md` dosyasındaki adımları
izleyin, sonra `agents/cutout_tags.json` içine dosya adlarınızı ve meta-verileri girin.

## Environment Setup

`.env.example` dosyasını `.env` olarak kopyalayın ve doldurun:

| Variable | Açıklama |
|----------|----------|
| `COVER_TYPE` | `reels` veya `youtube` |
| `ENV` | `production` veya `development` (development = dry-run) |
| `NOTION_SOCIAL_TOKEN` | Notion API token |
| `NOTION_DB_REELS_KAPAK` | Reels video veritabanı ID |
| `NOTION_DB_YOUTUBE_ISBIRLIKLERI` | YouTube video veritabanı ID |
| `NOTION_DB_OPS_LOG` | Operasyon log veritabanı ID |
| `KIE_API_KEY` | Kie AI görsel üretim anahtarı |
| `GEMINI_API_KEY` | Google Gemini (metin + vision) anahtarı |
| `IMGBB_API_KEY` | ImgBB görsel hosting anahtarı |
| `GOOGLE_OUTREACH_TOKEN_JSON` | Google Drive OAuth token (JSON string) |

## Lokal Çalıştırma

```bash
python main.py --type reels      # Reels pipeline
python main.py --type youtube    # YouTube pipeline
LOOP=1 python main.py --type reels   # Worker modu (sonsuz döngü)
python trigger_example.py        # Tek video için manuel tetikleme
```

## Deploy

Railway'de **2 ayrı CronJob servisi** olarak deploy edilir (biri `COVER_TYPE=reels`,
diğeri `COVER_TYPE=youtube`). `railway.json` ve `nixpacks.toml` hazır gelir.
Build: NIXPACKS, start: `python main.py`.
