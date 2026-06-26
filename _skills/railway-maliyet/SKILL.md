---
name: railway-maliyet
description: Railway servislerinin maliyetini doğru hesaplamak için kullan. Railway %100 saniye-başı kaynak ölçümlü (vCPU·sn + GB·sn) — "cron $7/ay, worker $7/ay" gibi düz servis ücreti YOKTUR. Bu skill'i şu durumlarda çağır: (1) bir projeyi cron mu worker mı yapacağına karar vermek, (2) "şu servis ayda kaça patlar" sorusu, (3) toplam Railway faturasını tahmin etmek, (4) Hobby→Pro geçiş kararı, (5) "neden bu kadar fazla geldi" analizi, (6) canli-yayina-al/use-railway/railway-deploy-rules workflow'larında maliyet bahsi geçtiğinde.
license: MIT
metadata:
  author: antigravity
  version: "2.0.0"
  last_verified: 2026-05-05
  source: railway.com/pricing + docs.railway.com/reference/pricing
---

# Railway Maliyet Hesaplama — Doğru Model

## 0. Önce Aklında Tut: "Servis Başı $7" YALAN

Railway'de **servis başına sabit ücret yoktur**. Cron, Worker, Web, Postgres — hepsi aynı şekilde **fiilen kullanılan vCPU-saniye + RAM-GB-saniye + ağ + disk** ile faturalandırılır. Bir cron 5 dakika çalışıp duruyorsa, geri kalan 29 gün 23 saat 55 dakika **$0** maliyetlidir. Bir worker 7/24 ayaktaysa, 720 saat boyunca CPU ve RAM tüketimi metreye yazılır.

Bu yüzden "16 servisim var, hepsi $7 = $112" hesabı yanlıştır. Doğru hesap: **her servisin gerçek CPU+RAM kullanımını saniyeye vurmak.**

---

## 1. Plan Yapısı (2026-05 itibarıyla doğrulanmış)

| Plan | Aylık taban | Dahil kullanım kredisi | Limitler |
|------|-------------|------------------------|----------|
| Free | $0 (30 günlük trial) → $1/ay | $5 trial | Çok kısıtlı |
| **Hobby** | **$5/ay** | **$5 dahil kullanım** | 6 replica, 48 vCPU, 48 GB RAM, 5 GB volume |
| **Pro** | **$20/ay** | **$20 dahil kullanım** | 42 replica, 1000 vCPU, 1 TB RAM, 1 TB volume |
| Enterprise | Custom | — | — |

**Net ödenecek tutar = max(plan tabanı, plan tabanı + (gerçek kullanım − dahil kredi))**

Hobby'de $5 krediyi aşmadıysan da $5 ödüyorsun. Aştığın her $1 doğrudan eklenir.

---

## 2. Birim Fiyatlar (saniye başı)

```
RAM     : $0.00000386 / GB·saniye
vCPU    : $0.00000772 / vCPU·saniye
Volume  : $0.00000006 / GB·saniye
Egress  : $0.05       / GB (dış ağa giden trafik)
Object  : $0.015      / GB·ay  (object storage, egress bedava)
```

### Bir ay = 2,628,000 saniye (≈ 730 saat)

Bu sabiti aklında tut. Aylık maliyet için:

```
Aylık $ = (vCPU_ortalama × 0.00000772 + GB_RAM_ortalama × 0.00000386) × 2,628,000
       + Volume_GB × 0.00000006 × 2,628,000
       + Egress_GB × 0.05
```

### Hızlı kafadan dönüşüm tablosu (24/7 çalışan servis)

| Kaynak | Aylık maliyet |
|--------|---------------|
| 1 vCPU 7/24 | **$20.29** |
| 0.5 vCPU 7/24 | $10.14 |
| 0.1 vCPU 7/24 | $2.03 |
| 0.05 vCPU 7/24 | $1.01 |
| 1 GB RAM 7/24 | **$10.15** |
| 0.5 GB RAM 7/24 | $5.07 |
| 0.25 GB RAM 7/24 | $2.54 |
| 0.1 GB RAM 7/24 | $1.01 |

Cron için aynı kaynak × (çalışma süresi / 2,628,000).

---

## 3. Tipik Servis Maliyetleri (Antigravity gerçek profillerine göre)

Bunlar gözleme dayalı kaba tahminler — kesin sayı için Railway metrics ekranından oku.

### Worker (7/24 polling Telegram bot, hafif Python)
- Profil: ~0.05 vCPU + 0.15 GB RAM
- **Maliyet: ~$2.50–4/ay**

### Worker (orta seviye, Notion+OpenAI çağrıları)
- Profil: ~0.1 vCPU + 0.3 GB RAM
- **Maliyet: ~$5–7/ay**

### Worker (ağır, ffmpeg/medya işleyen)
- Profil: ~0.3 vCPU + 0.6 GB RAM (peak'te daha yüksek)
- **Maliyet: ~$10–15/ay**

### Cron (10 dakikada bir, 30 sn çalışan hafif iş)
- Aylık çalışma: ~144 koşu × 30sn = 72 dakika = 4320 sn
- 0.2 vCPU + 0.3 GB RAM × 4320 = $0.007 + $0.005
- **Maliyet: ~$0.02/ay** (pratikte yuvarlanır, ihmal edilebilir)

### Cron (saatlik, 2 dakika çalışan orta iş)
- Aylık: 720 × 120 sn = 86,400 sn
- 0.3 vCPU + 0.4 GB RAM × 86,400 = $0.20 + $0.13
- **Maliyet: ~$0.35/ay**

### Cron (günde 1×, 5 dakika çalışan ağır iş — örn. video üretim)
- Aylık: 30 × 300 sn = 9000 sn
- 0.5 vCPU + 0.5 GB RAM × 9000 = $0.035 + $0.017
- **Maliyet: ~$0.05/ay**

### Express/Web (FastAPI webhook listener, 7/24)
- Profil: ~0.1 vCPU + 0.4 GB RAM
- **Maliyet: ~$6–8/ay**

### Postgres (managed)
- Idle: ~0.1 vCPU + 0.5 GB RAM + 1 GB volume
- **Maliyet: ~$7–8/ay**

---

## 4. Cron mu Worker mı? — Karar Kuralı

Tek soru: **"Bir şeyin olur olmaz tepki vermesi gerekiyor mu?"**

| Senaryo | Doğru tip | Sebep |
|---------|-----------|-------|
| Telegram bot user mesajına cevap | Worker | Anında cevap lazım |
| Webhook listener (WhatsApp, Stripe) | Worker/Web | Hep dinlemeli |
| 10 dakikada bir Sheets→Notion | Cron | Gecikme tolere edilir |
| Günlük scraper / içerik üretici | Cron | Periyodik |
| Lead bildirimi (anında ulaşmalı) | Worker | Geç bildirim = lead kaybı |

**Maliyet motivasyonu:** Aynı kaynak profilinde cron, worker'a göre **çoğu durumda 50–500× daha ucuzdur** çünkü çalışmadığı sürede sıfır metreye yazar. "Polling worker'ı 10dk'da bir cron'a çevir" tek tek $5–7/ay tasarruf demektir.

⚠️ Ama hızlı tepki ürün gereği ise (Lead_Notifier_Bot gibi) cron'a çevirme — ürün kararı maliyet kararına ezdirilmez.

---

## 5. Tahmin Akışı (yeni proje ya da soru geldiğinde)

1. **Servis tipi belirle:** worker mı, cron mu, web mi.
2. **Kaynak profili tahmin et:** Python idle bot ≈ 0.05 vCPU + 0.15 GB; orta yük ≈ 0.1 + 0.3; ağır ≈ 0.3 + 0.6.
3. **Worker ise** Bölüm 3'teki tablodan al.
   **Cron ise** koşu sayısı × ortalama süre × kaynak × birim fiyat hesapla.
4. **Volume varsa** GB × $0.16/ay ekle (5 GB Hobby'de dahil).
5. **Egress önemliyse** (medya servisleri) GB × $0.05 ekle.
6. **Plan tabanını ekle** ($5 Hobby / $20 Pro) — dahil kredi düşülerek.

---

## 6. Gerçek Faturayı Okuma (tahmin yerine)

Tahmin yerine **Railway metrics**'ten oku. GraphQL endpoint:
`https://backboard.railway.com/graphql/v2` (memory'deki `feedback_railway_graphql_domain.md` kuralı geçerli — `.app` değil `.com`).

Servis bazlı CPU/RAM ortalamasını çekmek için `metrics` query'si kullan; yoksa dashboard'tan **Usage** sekmesi her servisin son 30 günlük gerçek $ tüketimini gösterir.

**Kural:** "Bu servis aylık X dolar" derken kaynak Railway dashboard'u **veya** bu skill'deki saniye-bazlı hesap olsun. `deploy-registry.md` maliyet kaynağı **değildir** (bkz. memory `feedback_registry_vs_railway_cron.md`).

---

## 7. Hobby → Pro Geçişi — Ne Zaman Mantıklı?

Hobby tabanı $5, Pro tabanı $20. Pro $15 daha pahalı ama $15 daha fazla dahil kredi getirmiyor — $20 dahil kredi getiriyor (Hobby'de $5). Yani **Pro net ek $15 tabana karşılık $15 ek kredi** sunar — break-even.

Pro'ya geçmenin gerçek sebebi:
- **Replica/RAM/vCPU limitleri** (Hobby 48 vCPU sınırı; ağır iş yükü vurur)
- **Workspace collaboration** (takım üyeleri)
- **Yüksek SLA**

Sadece $25–35/ay harcıyorsan Hobby'de kal — Pro'ya geçmek tasarruf değil, hatta küçük kayıp.

---

## 8. Antigravity Mevcut Durumu (2026-05-05 snapshot)

`_knowledge/deploy-registry.md` üzerinden 16 aktif servis:
- 12× Cron (toplam ~$1–3/ay — çoğu ihmal edilebilir)
- 4× Worker (toplam ~$15–25/ay — gerçek tüketime göre)
- Tahmini toplam fatura: **$25–35/ay** (Hobby tabanı $5 + ~$20–30 kullanım)

⚠️ Bu rakamlar dashboard'taki "Usage" sekmesi ile doğrulanmalı. Eski memory'deki "$125/ay" rakamı yanlış metodolojiyle (servis başı $7) çıkarılmıştı.

---

## 9. Maliyet Tasarrufu — Sıralı Müdahale Listesi

1. **Ölü servisleri sil** (Railway'de — lokal arşivle yetinme; Railway'de durdukça metre işler)
2. **Polling worker → cron** (sadece tepki süresi tolere edilebilir olanlar)
3. **Idle kaynaklar:** Servisin gerçekten 0.5 GB RAM'e ihtiyacı var mı? Çoğu Python bot 150–250 MB ile çalışır.
4. **Egress optimizasyonu:** Medya'yı Railway'den değil Drive/CDN'den serve et.
5. **Volume kullanmayan servislerden volume kaldır.**

---

## 10. ÖNEMLİ Anti-Pattern'lar

- ❌ "Cron $7, Worker $7, Express $20" — **TAMAMEN YANLIŞ**, böyle bir tarife yok.
- ❌ Toplam maliyeti servis sayısı × sabit ile hesaplamak.
- ❌ `deploy-registry.md`'ye bakıp "şu kadar tutar" demek.
- ❌ Kullanıcıya "cron'a çevirelim, ayda $7 tasarruf" demek — gerçek sayı $0.50–5 arası, abartmaktan kaçın.
- ✅ Her zaman **vCPU·saniye + GB·saniye** zihinsel modeline geri dön.
