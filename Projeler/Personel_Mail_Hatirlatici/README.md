# Personel Mail Hatırlatıcı

Bir personelin gelen kutusunu tarayıp, cevapsız kalmış önemli iş thread'lerini
tespit eden ve düzenli bir hatırlatma digest'i gönderen otomasyon.

## Ne işe yarar?

Yoğun bir gelen kutusunda bazı iş mailleri cevapsız kalır ve unutulur.
Bu bot her gün çalışır, son N gündeki thread'leri tarar, gürültüyü (bültenler,
sistem bildirimleri, faturalar) eler, kalan thread'leri bir LLM ile sınıflandırır
ve 48+ iş saati boyunca cevapsız kalanları tek bir özet mail halinde gönderir.

## Desen — bu yapı şuna yarar

Bu proje "stale thread detection" desenidir. Çekirdek mantık şu adımlardan oluşur:

1. **Tara** — Gmail API ile gelen kutusunu çek.
2. **Pre-filter** — Kesinlikle ilgisiz mailleri LLM'e göndermeden ele (token tasarrufu).
3. **Sınıflandır** — Kalan thread'leri LLM ile kategorilere ayır.
4. **State tut** — Her thread'in durumunu Notion DB'sinde takip et (carry-forward).
5. **Stale filtrele** — İş günü hesabıyla "kaç saat sessiz?" sorusunu cevapla.
6. **Digest gönder** — Yeni + hala bekleyen thread'leri tek mailde özetle.
7. **Geri bildirim** — Mute/snooze butonlarıyla kullanıcı listeyi yönetir.

Aynı desen satış lead takibi, müşteri talep takibi, başvuru takibi gibi
"gelen kutusunda iş kaybolmasın" senaryolarına uyarlanabilir. Sınıflandırma
mantığını kendi senaryona göre `core/thread_analyzer.py` içindeki prompt'tan
değiştir.

## Teknik Altyapı

- **Runtime:** Python 3.11, Railway CronJob
- **Gmail:** OAuth2
- **LLM:** Groq (`openai/gpt-oss-120b`)
- **State:** Notion DB
- **Buton webhook'u:** FastAPI (opsiyonel, ayrı Railway servisi)

## Kurulum

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # Değerleri doldur
python main.py --dry-run   # Test modu — mail/Notion'a yazmaz
```

## Klasör Yapısı

```
├── main.py                  # CronJob giriş noktası
├── webhook_server.py        # Mute/snooze buton servisi (opsiyonel)
├── core/
│   ├── gmail_scanner.py     # Gmail tarama + pre-filter
│   ├── thread_analyzer.py   # LLM sınıflandırma (prompt buradadır)
│   ├── decision.py          # LLM çıktısı → Status kararı
│   └── notifier.py          # Digest mail HTML + gönderim
├── services/
│   ├── gmail_service.py     # Gmail API auth
│   ├── groq_client.py       # Groq LLM client
│   ├── notion_threads.py    # Thread state DB
│   └── notion_pipeline.py   # Opsiyonel pipeline DB entegrasyonu
├── utils/
│   ├── business_hours.py    # İş günü/saati hesaplama
│   └── logger.py
└── tests/
    └── test_decision.py
```

## Deploy

Railway CronJob olarak çalışır. `.env.example`'daki tüm değişkenleri Railway
servis ayarlarında tanımla. Cron için ayrı, webhook için ayrı servis kullan.
