# Reels Script Pipeline

Yabancı dildeki Instagram Reels'ları izleyip, ilgi alanına uygun olanları seçip, kendi dilinde scripte çeviren ve editör için brief hazırlayan pipeline şablonu.

Çıktı: Notion'da kart (script + caption + ManyChat DM şablonu) + Drive'da brief Doc (3-5 gerçek kaynak linki).

> **Bu çeviri değil — yeniden anlatım.** Pipeline kaynak içeriği bire bir kopyalamaz; konuyu kendi tonuna uyarlar. Telif ve marka sahipliği konusunda kendi etik politikanı tanımlamanı tavsiye ederiz.

## Stack

- **Runtime:** Python 3.11
- **State DB:** Supabase Postgres + pgvector (style corpus retrieval, run state)
- **Storage:** Supabase Storage bucket (`reels-source`)
- **Reels indirme:** Apify `apify/instagram-reel-scraper`
- **Transkript:** HappyScribe v1 REST
- **LLM:** Anthropic Claude (Opus + Sonnet)
- **Web search:** Anthropic native `web_search` tool
- **Embedding:** Voyage `voyage-3` (1024d)
- **Çıktı:**
  - Notion REST → kendi içerik DB'n
  - Google Drive (OAuth `drive.file` scope)

## Pipeline (8 stage)

1. **Download** → Apify + Supabase Storage public URL
2. **Transcribe** → HappyScribe transcript
3. **Correct + Analyze** → Sonnet ile düzeltme + yapısal analiz
4. **Topic Proposal** → Opus ile yeni başlık + hook
5a. **Style Retrieval** → Voyage embedding + pgvector top-5
5b. **Script Generation** → Opus + self-edit pass (jargon temizliği, hedef okur kontrolü)
6. **Asset Research** → Opus + web_search → 3-5 gerçek kaynak
7. **Drive Brief** → klasör + HTML başlıklı brief Doc
8. **Notion Card** → script paragrafları + ManyChat bloku

Stage 5b ve 6 çıktıları `core/sanitize.py`'den geçer. Sanitize kuralları kendi etik politikana göre düzenlenebilir.

## Setup

```bash
python3.11 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # değerleri doldur
python -m tests.test_smoke   # 8/8 yeşil bekleriz
```

Tek run:
```bash
python -m scripts.run_single "https://www.instagram.com/p/<shortcode>/" --source-channel "@kanal"
```

## Konfigürasyon

`.env.example` içinde doldurman gereken anahtarlar:
- `ANTHROPIC_API_KEY` — Claude
- `APIFY_TOKEN` — reels scraper
- `HAPPYSCRIBE_API_KEY` + `HAPPYSCRIBE_ORG_ID` — transkript
- `SUPABASE_URL` + `SUPABASE_SERVICE_KEY` — pgvector DB
- `NOTION_TOKEN` + `NOTION_DB_ID` — hedef DB
- `GOOGLE_OAUTH_CLIENT_ID/SECRET` + `GOOGLE_REFRESH_TOKEN` — Drive
- `VOYAGE_API_KEY` — embedding

## Stil Corpus (kendi tonunu öğret)

`scripts/build_style_corpus.py` ile kendi kaynak metinlerini okur, Voyage embedding üretir ve Supabase'e yazar. Pipeline her yeni reel için bu corpus'tan en alakalı pasajları retrieval edip Opus'a stil kılavuzu olarak verir.

```bash
python -m scripts.build_style_corpus --input <kendi_metin_kaynagin>
```

## Notion DB Şeması

Pipeline aşağıdaki property'leri bekler:
- `Title` (title)
- `Status` (select)
- `Caption` (rich_text)
- `ManyChat DM` (rich_text)
- `Brief` (url)

Property adları `core/notion_writer.py` içinde tanımlı. Kendi DB şemana göre uyarla.

## Klasör Yapısı

```
Reels_Script_Pipeline/
├── README.md
├── _PAYLASIM_NOTU.md
├── .env.example
├── requirements.txt
├── core/
│   ├── config.py
│   ├── pipeline.py
│   ├── storage.py
│   ├── transcribe.py
│   ├── retrieval.py
│   ├── llm.py
│   ├── sanitize.py
│   ├── notion_writer.py
│   ├── drive.py
│   └── state.py
├── scripts/
│   ├── run_single.py
│   └── build_style_corpus.py
└── tests/
    └── test_smoke.py
```

## Test

```bash
pytest tests/
```
