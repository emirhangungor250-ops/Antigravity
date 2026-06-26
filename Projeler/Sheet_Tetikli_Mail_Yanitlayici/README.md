# Sheet Tetikli Mail Yanıtlayıcı

Bir Google Sheet'te bir satır işaretlendiğinde (checkbox), o satırdaki kişiye
otomatik, kişiselleştirilmiş bir Türkçe mail gönderen bot.

## Ne işe yarar?

Bir Sheet'i periyodik olarak tarar. "Tetikleyici" sütunundaki checkbox TRUE olan
ve "durum" sütunu henüz boş olan satırları bulur. Her satır için satırdaki
bağlam bilgisiyle (isim, marka, ihtiyaç vb.) bir mail üretir, gönderir ve durum
sütununa "✅ Gönderildi" yazar. Durum sütunu sayesinde idempotenttir — aynı
satıra ikinci kez mail gitmez.

## Desen — bu yapı şuna yarar

Bu proje "spreadsheet-triggered action" desenidir:

1. **Tara** — Sheet'i çek, tetikleyici checkbox + boş durum satırlarını bul.
2. **Üret** — Satır bağlamından LLM ile (veya şablonla) mail içeriği üret.
3. **Gönder** — Gmail API ile mail at.
4. **İşaretle** — Durum sütununa sonucu yaz (idempotency).

Aynı desen "form yanıtına otomatik teşekkür", "randevu onayı", "eksik bilgi
talebi", "takip maili" gibi her senaryoya uyar. Sheet yapısı, tetikleyici/durum
sütunları ve mailin amacı tamamen env-driven.

## Sütun haritası

Hangi sütunun ne işe yaradığı `.env` ile belirlenir:
- `TRIGGER_COL` — işaretlendiğinde mail tetikleyen checkbox sütunu
- `STATUS_COL` — bot'un "gönderildi" durumunu yazdığı sütun
- `EMAIL_COL` — alıcının e-posta adresi
- `NAME_COL`, `BRAND_COL`, `NEED_COL` vb. — mail kişiselleştirme bağlamı

## Auth

İki Google OAuth token kullanılır (`google_auth.py`):
- `GMAIL_TOKEN_JSON` — mail gönderecek hesap (`gmail.send` scope)
- `SHEETS_TOKEN_JSON` — Sheet'i okuyup yazacak hesap (`spreadsheets` scope)

Aynı hesabı ikisi için de kullanabilirsin — o zaman iki değişkene aynı token'ı koy.

## Komutlar

```bash
python3 main.py --dry-run   # Mail gönderme, sadece taslakları göster
python3 main.py             # Tek tur (cron modu)
python3 main.py --loop      # Sürekli polling (worker modu)
```

## Deploy

Railway'de Cron Job olarak çalışır (`*/5 * * * *` gibi). `.env.example`'daki
tüm değişkenleri Railway servis ayarlarında tanımla.
