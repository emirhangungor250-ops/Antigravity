# Lead Notifier Bot v3

Google Sheets'te belirtilen tab'da yeni bir lead tespit edildiğinde **Telegram** ve **Email** ile anlık bildirim gönderen otomasyon botu.

## ✨ v3 Değişiklikleri (Stabilite Reformu)

- **ID Tabanlı State:** Eski satır-sayısı tabanlı sistem kaldırıldı. Her lead'in benzersiz ID'si takip edilir — tekrar bildirim imkansız
- **lead_status Filtresi:** Sadece `lead_status == "CREATED"` olan lead'ler bildirilir. Test lead'ler (`TRUE`) otomatik atlanır
- **Batch Size Limiti:** Tek döngüde max 10 bildirim (state bozulması veya ilk kurulumda toplu spam engellenir)
- **Temiz Konfigürasyon:** Hardcoded token SIFIR — tüm değerler environment variable'dan
- **Fail-Fast Validation:** Eksik env variable varsa başlangıçta `EnvironmentError` fırlatır

## 📁 Dosya Yapısı

```
Lead_Notifier_Bot/
├── main.py              # Ana polling döngüsü, signal handler
├── config.py            # Env-only konfigürasyon
├── sheets_reader.py     # Google Sheets — ID tabanlı state, lead_status filtresi
├── notifier.py          # Telegram + Gmail API bildirim
├── share_sheet.py       # Sheet'i servis hesabıyla paylaşan yardımcı betik
├── requirements.txt     # Kilitli versiyonlar
├── railway.json         # Railway deployment config
├── .env.example         # Gerekli environment variable şablonu
├── .gitignore           # Güvenlik kuralları
└── README.md            # Bu dosya
```

## ⚙️ Environment Variables

| Değişken | Açıklama | Zorunlu |
|----------|----------|---------|
| `SPREADSHEET_ID` | Google Sheets dosya ID'si | ✅ |
| `SHEET_TAB` | İzlenecek tab adı | Hayır (default: `Sheet1`) |
| `POLL_INTERVAL_SECONDS` | Kontrol sıklığı (saniye) | Hayır (default: `300`) |
| `TELEGRAM_BOT_TOKEN` | Telegram bot tokeni | ✅ |
| `TELEGRAM_CHAT_ID` | Mesaj gönderilecek chat ID | ✅ |
| `NOTIFY_EMAIL` | Bildirim alacak e-posta | ✅ |
| `SENDER_EMAIL` | Gönderici e-posta | ✅ |
| `GOOGLE_SERVICE_ACCOUNT_JSON` | Google SA JSON (Railway) | ✅ (Production) |
| `GOOGLE_OUTREACH_TOKEN_JSON` | Gmail/Sheets OAuth token | Email ve Sheets için |
| `MAX_BATCH_SIZE` | Tek döngüde max bildirim | Hayır (default: `10`) |

## 🚀 Kullanım

```bash
# Sürekli polling (5 dk aralık)
python main.py

# Tek döngü (test)
python main.py --once
```

## 🏗️ Deployment

- **Platform:** Railway (7/24 Worker)
- **GitHub Repo:** `<GITHUB_REPO>`
- **Hedef:** İlgili kişiye Telegram + Email ile yeni lead bildirimi
