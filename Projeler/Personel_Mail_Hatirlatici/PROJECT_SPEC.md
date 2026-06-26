# Personel Mail Hatırlatıcı — Proje Spesifikasyonu

> Bu dosya projenin teknik ve iş spesifikasyonunu içerir.

---

## 1. Problem

Bir personel, iş ilişkilerini e-posta üzerinden yürütüyor.
Bazı thread'ler unutuluyor/kaçırılıyor → karşı tarafa dönüş yapılmıyor → iş gecikiyor.

## 2. Çözüm

Günlük çalışan bir CronJob:
1. Gmail API ile izlenen inbox'ı tarar (son N gün)
2. 48+ iş saati sessiz thread'leri bulur
3. LLM ile gerçek, aksiyon gerektiren iş thread'lerini tespit eder
4. Aksiyon gerektiren thread'ler için tek bir hatırlatma digest'i gönderir

## 3. Konfigürasyon

### E-posta Hesabı
Tek bir gelen kutusu izlenir. Hesap `STAFF_EMAIL` env var'ı ile belirlenir.
OAuth token Railway'de `GMAIL_TOKEN_JSON` env var'ında (JSON string),
lokal'de `data/gmail-token.json` dosyasında tutulur.

### LLM
- **Provider:** Groq
- **Model:** `openai/gpt-oss-120b`
- **API Key:** `GROQ_API_KEY` env var'ı

### Bildirimler
- **Digest:** E-posta → `ALERT_EMAIL` (opsiyonel `ALERT_CC`)

### Deploy
- **Platform:** Railway CronJob (örn. her gün 07:00 UTC)
- **Webhook servisi:** Opsiyonel ayrı Railway servisi (mute/snooze butonları)

## 4. İş Kuralları

### Tarama
- Son N gündeki thread'ler taranır (`main.py` → `SCAN_DAYS`)
- Sadece izlenen inbox taranır

### Stale Eşiği
- **48 iş saati** (2 iş günü) sessizlik → hatırlatma tetiklenir
- Hafta sonu iş günü sayılmaz

### LLM Analiz Çıktısı (örnek)
```json
{
  "category": "brand_collab_offer",
  "confidence": 0.95,
  "is_personalized": true,
  "brand_name": "Örnek Şirket",
  "last_sender": "brand",
  "action_needed_by_staff": true,
  "thread_status": "active",
  "reason": "Karşı taraf teklif gönderdi, personel henüz cevap vermedi"
}
```

### Karar Matrisi
| Son mesajı atan | 48+ saat sessiz | Aksiyon |
|-----------------|-----------------|---------|
| Karşı taraf | Evet | ⚠️ Personele hatırlatma |
| Personel | Evet | ℹ️ Karşı taraftan cevap bekleniyor — hatırlatma YOK |
| Thread kapanmış | - | ❌ Atla |

### Tekrar Hatırlatma
- Aynı thread için 2 iş günü arayla tekrar hatırlatma gönderilir
- Thread cevaplandığında otomatik durur

## 5. State Yönetimi (Notion)

Her Gmail thread için Notion DB'sinde bir satır tutulur. Status değerleri:
`open`, `responded_by_staff`, `closed_won`, `closed_lost`, `false_positive`.

Manuel olarak `closed_*` / `false_positive` yapılan satırlara sistem dokunmaz.
Beklenen property adları için `services/notion_threads.py` başındaki nota bak.

## 6. Akış Detayı (main.py)

1. Gmail tara → pre-filter
2. Her thread için Notion'daki mevcut durumu çek
3. Yeni veya değişmiş thread'leri LLM ile analiz et
4. LLM çıktısını `core/decision.py` ile Status'e dönüştür, Notion'a upsert et
5. Notion'dan tüm `open` thread'leri çek
6. İş saati hesabıyla stale (48+ saat) olanları filtrele
7. Digest mail gönder (yeni + devam eden bölümler)
8. Gönderilen thread'lerin Reminder Count'unu artır

## 7. Environment Variables

`.env.example` dosyasına bak. Zorunlu: `GROQ_API_KEY`, `NOTION_TOKEN`,
`NOTION_DB_THREADS`, `STAFF_EMAIL`, `GMAIL_TOKEN_JSON`.
