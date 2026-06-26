---
description: Gmail'deki okunmamış mailleri AI ile analiz et — gereksizleri okundu yap, önemlilere taslak yanıt hazırla
---

# /eposta-asistani — E-Posta Asistanı

> 📧 Her gün sabah 09:00'da (veya manuel çağrıda) Gmail'i okur, AI ile analiz eder,
> gereksiz mailleri temizler ve önemli maillere taslak yanıt hazırlar.

## Çağırılacak Skill

Bu workflow tetiklendiğinde şu skill'i yükle:
- `eposta-asistani` — Gmail okuma + AI analiz + taslak oluşturma

## Ön Koşullar

1. **Google OAuth token mevcut olmalı:** `_knowledge/credentials/oauth/gmail-outreach-token.json`
   - Yoksa: `cd _knowledge/credentials/oauth && python auth_helper.py outreach`
2. **OpenAI API key:** `master.env`'de `OPENAI_API_KEY` dolu olmalı
3. **Python paketleri kurulu olmalı:** `pip install -r _skills/eposta-asistani/scripts/requirements.txt`

## Adım 1 — Bağımlılık Kontrolü

```bash
pip install -r _skills/eposta-asistani/scripts/requirements.txt
```

Python paketleri yoksa kur. Varsa atla.

## Adım 2 — İlk Çalıştırma (Dry-Run)

İlk seferde mutlaka `--dry-run` ile test et:

```bash
python _skills/eposta-asistani/scripts/email_assistant.py --dry-run --max-emails 5
```

Kontroller:
- Gmail bağlantısı başarılı mı?
- OpenAI API çalışıyor mu?
- Kategoriler mantıklı mı?

## Adım 3 — Canlı Çalıştırma

Dry-run başarılıysa:

```bash
python _skills/eposta-asistani/scripts/email_assistant.py
```

## Adım 4 — Rapor

Script çalışınca `_skills/eposta-asistani/logs/` altına JSON rapor yazar. Kullanıcıya şu bilgileri özetle:

- Toplam işlenen mail sayısı
- Kaç tanesi okundu işaretlendi (promosyon/bildirim/gereksiz)
- Kaç tane taslak yanıt oluşturuldu
- Varsa hatalar

## Adım 5 — Railway'e Deploy (Opsiyonel)

Kullanıcı "her gün otomatik çalışsın" derse:

1. `/canli-yayina-al` workflow'unu tetikle
2. Railway cron expression: `0 6 * * *` (UTC 06:00 = TR 09:00)
3. Start command: `python email_assistant.py`
4. Gerekli env'ler:
   - `OPENAI_API_KEY`
   - Google OAuth token (dosya olarak veya env var olarak)

## ⚠️ Dikkat Edilecekler

- **Taslak yanıtlar gönderilmez** — sadece Gmail Taslaklar'a kaydedilir
- **ONEMLI_BILGI kategorisi** için hiçbir aksiyon alınmaz — mail okunmamış kalır
- **AI hata verirse** mail güvenli kategoriye (ONEMLI_BILGI) düşer — veri kaybı olmaz
- Günlük maks maliyet: ~$0.03 (GPT-4o-mini)
