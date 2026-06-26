---
name: eposta-asistani
description: |
  Gmail'deki okunmamış mailleri AI ile analiz eder: promosyon/gereksiz olanları otomatik 
  okundu işaretler, yanıt gereken önemli maillere taslak yanıt hazırlar. "maillerimi oku",
  "mail asistanı çalıştır", "gelen kutusu temizle" gibi taleplerde tetiklenir.
---

# 📧 E-Posta Asistanı

Gmail'deki okunmamış mailleri okur, OpenAI GPT-4o-mini ile analiz eder ve otomatik aksiyonlar alır:

- **Promosyon / Bildirim / Gereksiz** → Okundu olarak işaretler
- **Önemli + Yanıt Gereken** → Profesyonel taslak yanıt hazırlayıp Gmail Taslaklar'a kaydeder
- **Önemli + Bilgi** → Dokunmaz, kullanıcı görsün

---

## 🔑 Gereksinimler

- **Gmail API:** Merkezi OAuth token (`_knowledge/credentials/oauth/`)
- **OpenAI API:** `master.env`'deki `OPENAI_API_KEY`
- **Python paketleri:** `scripts/requirements.txt`

---

## 📂 Dosya Yapısı

```
_skills/eposta-asistani/
├── SKILL.md                         ← Bu dosya
├── scripts/
│   ├── email_assistant.py           ← Ana script
│   └── requirements.txt             ← Python bağımlılıkları
└── logs/                            ← Çalışma raporları (otomatik oluşur)
    └── rapor_YYYYMMDD_HHMMSS.json
```

---

## 🚀 Nasıl Çalıştırılır

### Normal Çalışma
```bash
python _skills/eposta-asistani/scripts/email_assistant.py
```

### Test Modu (Değişiklik Yapmaz)
```bash
python _skills/eposta-asistani/scripts/email_assistant.py --dry-run
```

### Parametreler
```bash
python _skills/eposta-asistani/scripts/email_assistant.py \
  --account all \              # Gmail hesabı: all (tüm hesaplar), outreach (birincil) veya ikincil
  --max-emails 100 \           # Maks işlenecek mail sayısı (varsayılan: 100)
  --dry-run                    # Test modu — sadece analiz yapar, aksiyon almaz
```

---

## 📊 Kategori Sistemi

| Kategori | Açıklama | Aksiyon |
|----------|----------|---------|
| `PROMOSYON` | Reklam, newsletter, kampanya | ✅ Okundu işaretle |
| `BILDIRIM` | Otomatik bildirimler (GitHub, banka) | ✅ Okundu işaretle |
| `GEREKSIZ` | Spam benzeri, gereksiz listeler | ✅ Okundu işaretle |
| `ONEMLI_YANIT_GEREK` | İnsan yazmış, cevap bekleniyor | 📝 Taslak yanıt oluştur |
| `ONEMLI_BILGI` | Fatura, sözleşme, onay (cevap yok) | 🔕 Dokunma |

---

## 📝 Taslak Yanıt Kuralları

- Mailin dilinde yanıt (Türkçe ise Türkçe, İngilizce ise İngilizce)
- Kısa, profesyonel, doğal ton
- Gmail'de "Taslaklar" klasöründe görünür
- Kullanıcı beğenirse gönderir, beğenmezse düzenler

---

## 🔄 Railway Cron (7/24 Çalışma)

Hızlı yanıt verebilmesi için her 3 saatte bir otomatik çalışması önerilir (Railway deploy):

- **Cron:** `0 */3 * * *` (Her 3 saatte bir)
- **Start command:** `python email_assistant.py` (Varsayılan olarak "all" hesaplarını tarar)
- **Env'ler:** `OPENAI_API_KEY` + Google OAuth token bilgileri

---

## ❌ Hata Yönetimi

| Durum | Çözüm |
|-------|-------|
| Token hatası (`invalid_grant`) | `cd _knowledge/credentials/oauth && python auth_helper.py status` |
| OpenAI API hatası | Mail `ONEMLI_BILGI` kategorisine atanır (güvenli fallback) |
| Gmail kota aşımı | Günlük limit 250+ — genelde sorun olmaz |
| Body parse hatası | Snippet kullanılır |

---

## 📈 Maliyet

| Bileşen | Günlük Tahmini |
|---------|---------------|
| GPT-4o-mini (100 mail analiz) | ~$0.02-0.05 |
| Gmail API | Ücretsiz |
| Railway cron | Free tier |
