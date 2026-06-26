# 💰 Tahsilat Takip Otomasyonu

Notion tabanlı bir kayıt listesinde **geciken ödemeleri** tarayıp tek bir
toplu HTML e-posta özeti gönderen cron botu.

**Bu desen şuna yarar:** Notion'da iş/proje/fatura kaydı tutan herkes için.
Her gün manuel "kimden ne zaman para gelecekti" kontrolü yapmak yerine,
bot yayın/teslim tarihinden bu yana geçen süreyi hesaplar, ödeme alınmamış
kayıtları gecikme bandına göre gruplar ve sana tek mail atar. Bekleyen yoksa
mail bile atmaz.

---

## 🎯 Ne Yapar?

1. **Notion'dan veri çeker** — `COLLAB_DB_ID` veritabanından "Yayınlandı" durumundaki kayıtları alır.
2. **Tutar bilgisini join'ler** — Ayrı bir tutar/ödeme DB'sini (`TAHSILAT_TAKIP_DB_ID`) **sadece okur**, bir relation property üzerinden kayıt → tutar eşlemesi yapar.
3. **Gecikme hesaplar** — Yayın/teslim tarihinden bugüne kaç gün geçtiğini bulur.
4. **Tek toplu e-posta atar** — Bekleyen kayıtlar üç banda ayrılır:
   - 🟡 **14-29 gün** → Sarı bandı
   - 🔴 **30-59 gün** → Kırmızı bandı
   - ⚫ **60+ gün** → Siyah bandı
5. **Bekleyen yoksa mail atılmaz.** Notion'a hiçbir şey yazılmaz (tamamen read-only).

---

## 🏗️ Mimari

```
Notion (ana kayıt DB)            Notion (tutar/ödeme DB)
        │                                │ (READ-ONLY)
        ▼                                ▼
                  notion_client.py
                        │
                        ▼
                   database.py — gecikme + bant filtresi
                        │
                        ▼
                      main.py — tek HTML özet hazırlar
                        │
                        ▼
                  email_client.py — Gmail API
```

State takibi minimaldir — günde 1 mail atıldığı için `/tmp` sentinel dosyası
ile aynı gün ikinci mail engellenir (Railway retry koruması).

---

## 📁 Dosya Yapısı

| Dosya | Açıklama |
|-------|----------|
| `main.py` | Toplu HTML özet + Gmail gönderim + idempotency guard |
| `config.py` | Ortam değişkenleri, DB ID'leri, Notion property adları |
| `notion_client.py` | Ana DB sorgusu + tutar DB read-only join |
| `database.py` | Gecikme + bant filtresi (state-less) |
| `email_client.py` | Gmail API (OAuth2) ile gönderim |
| `ops_logger.py` | Notion operational log (opsiyonel) |
| `railway.json` | Railway native cron config |
| `requirements.txt` | Python bağımlılıkları |

---

## ⚙️ Kurulum

1. `.env.example`'ı `.env` olarak kopyala, değerleri doldur.
2. Notion entegrasyonunu her iki DB'ye de bağla (paylaş).
3. `config.py` içindeki property adlarını (`PAYMENT_TYPE_PROP`,
   `CONTENT_RELATION_PROP`, ...) kendi Notion şemandaki gerçek adlarla
   eşleştir — ya doğrudan `.env`'den ver ya da config'teki default'ları düzenle.
4. Gmail API OAuth2 token'ını `GOOGLE_OUTREACH_TOKEN_JSON`'a base64'lü yerleştir.

### Beklenen Notion property'leri (ana DB)
- `Name` (title), `Status` (select — "Yayınlandı" değeri filtrelenir)
- `Check` (checkbox — işaretliyse ödeme alınmış sayılır, atlanır)
- `Paylaşım Tarihi` (date — gecikme bu tarihten hesaplanır)
- `PAYMENT_TYPE_PROP` (select — `PAYMENT_TYPE_SKIP_VALUE`'ya eşitse kayıt elenir)

### Beklenen Notion property'leri (tutar DB)
- `Tutar` (number), `CONTENT_RELATION_PROP` (ana DB'ye relation)

---

## 🚀 Çalıştırma

```bash
# Lokal
python main.py

# Railway: native cron (railway.json'daki cronSchedule)
```

---

## 🚂 Deploy

- **Platform:** Railway (Native Cron)
- **Start:** `python main.py` · **Restart:** `ON_FAILURE` (max 5) · **Cron:** `railway.json`'da

---

## 📝 Versiyon Geçmişi

| Tarih | Değişiklik |
|-------|-----------|
| — | Toplu özet mail, eşikler 14/30/60, tutar DB read-only join, stateless çalışma |
