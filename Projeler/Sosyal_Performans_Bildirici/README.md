# Sosyal Performans Bildirici

Sosyal medya hesaplarını periyodik olarak tarayıp, belirlenen izlenme barajını
aşan içerikleri tespit eden ve bir özet rapor maili gönderen otomasyon.

## Ne işe yarar?

Instagram, TikTok ve YouTube'daki videolarını Apify ile tarar, son N günde
yayınlanmış ve platform bazlı izlenme barajını aşan içerikleri bulur, isteğe
bağlı bir LLM ile kısa bir özet üretir ve HTML formatlı bir performans raporu
e-postası gönderir. Daha önce raporlanan içerikleri tekrar göndermez (state takibi).

## Desen — bu yapı şuna yarar

Bu proje "threshold-based content monitoring + digest" desenidir:

1. **Çek** — Apify Store actor'larıyla 3 platformdan veri topla.
2. **Filtrele** — Lookback penceresi + platform bazlı izlenme barajı uygula.
3. **Dedupe** — Notion DB (veya lokal JSON) ile daha önce bildirilenleri ele.
4. **Özetle** — Opsiyonel LLM ile kısa bir özet metin üret.
5. **Raporla** — HTML mail gönder; platform hataları için ayrı teknik rapor.

Aynı desen "rakip içerik takibi", "marka mention takibi", "viral içerik alarmı"
gibi senaryolara uyarlanabilir. Barajlar, hesaplar ve lookback tamamen env-driven.

## Teknik Altyapı

- **Runtime:** Python, Railway Cron Job
- **Veri:** Apify (Instagram/TikTok/YouTube actor'ları)
- **LLM:** Groq (`llama-3.3-70b-versatile`, opsiyonel)
- **State:** Notion DB veya lokal JSON fallback
- **Mail:** Gmail API (OAuth2)
- **Resilience:** `tenacity` ile retry, çoklu Apify key rotasyonu

## Kurulum

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # Değerleri doldur
ENV=development python main.py   # DRY_RUN — mail göndermez
```

## Proje Yapısı

```
├── main.py                      # Entry point
├── config.py                    # Fail-fast env validation
├── logger.py / ops_logger.py    # Logging (stdout + opsiyonel Notion)
├── core/
│   ├── apify_client.py          # 3 platform veri çekimi
│   └── llm_helper.py            # Opsiyonel LLM özet
├── infrastructure/
│   ├── email_sender.py          # Gmail HTML mail
│   └── state_manager.py         # Notion / lokal state
└── scripts/
    └── diagnose.py              # Pre-flight check (Apify + Notion + Gmail)
```

## Diagnose

Bir şey kırık görünüyorsa önce diagnose çalıştır:

```bash
ENV=development python -m scripts.diagnose
```

3 Apify actor + Notion DB schema + Gmail OAuth durumunu kontrol eder.

## Deploy

Railway Cron Job olarak çalışır (örn. `0 8 * * 1,3,5`). `.env.example`'daki
tüm değişkenleri Railway servis ayarlarında tanımla.
