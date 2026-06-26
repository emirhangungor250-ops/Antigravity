---
name: icerik-uretim
description: |
  içerik üretim sürecini (araştırma → script yazma → video üretimi) uçtan uca
  orkestre eden agent. Seçilen marka/müşteri için sosyal medya video içerikleri üretir.
---

# 🎬 İçerik Üretim Agenti

> **Agent:** `_agents/icerik-uretim/`
> **Amaç:** seçtiğin niş için araştırmadan video üretimine kadar tüm içerik pipeline'ını tek çatı altında yönetmek.
> **Ana Müşteri:** `config/ornek-musteri.yaml` ile tanımlanır (kendi markanı/müşterini gir)

---

## 📋 Bu Agent Ne Yapar?

5 ayrı adımlı workflow'u tek bir orkestrasyon çatısı altında birleştirir:

```
                    ┌─────────────────┐
                    │  İÇERİK ÜRETİM  │
                    │     AGENT'I      │
                    └────────┬────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
   ┌────▼─────┐       ┌─────▼──────┐       ┌─────▼──────┐
   │ ARAŞTIRMA │       │  SCRİPT    │       │   VİDEO    │
   │  KATMANI  │       │  KATMANI   │       │  KATMANI   │
   └────┬──────┘       └─────┬──────┘       └─────┬──────┘
        │                    │                    │
   ┌────▼─────┐       ┌─────▼──────┐       ┌─────▼──────┐
   │araştırma  │       │ script-yaz │       │ icerik-    │
   │   yap     │       │ ilham-al   │       │ uretimi    │
   │           │       │ hesaplama  │       │ (Kie AI)   │
   └───────────┘       └────────────┘       └────────────┘
```

---

## 🛠️ Kullandığı Skill'ler

| Skill | Konum | Ne İçin Kullanılır |
|-------|-------|--------------------|
| **Kie AI Video Production** | `_skills/kie-ai-video-production/SKILL.md` | Video/görsel üretimi (Kling 3.0, Veo 3.1, Sora 2, Nano Banana) |
| **Competitor Radar** | `_skills/rakip-analiz/SKILL.md` | Rakiplerin içerik analizi (Instagram, TikTok, Meta Ads) |
| **İçerik Yazarı** | `Projeler/<ICERIK_PROJESI>/skills/icerik-yazari/SKILL.md` | Marka üslup kuralları, format şablonları, hesaplama metrikleri |

---

## 🔧 Kullandığı Tool'lar

| Tool | Konum | Ne İçin |
|------|-------|---------| 
| **Calculator** | `Projeler/<ICERIK_PROJESI>/tools/calculator.py` | Yatırım hesaplamaları (mortgage, ROI, değer artışı) |
| **Transcript** | `Projeler/<ICERIK_PROJESI>/tools/transcript.py` | Rakip videolardan transkript çıkarma (Supadata API) |
| **Currency** | `Projeler/<ICERIK_PROJESI>/tools/currency.py` | USD → TL döviz çevirisi |
| **Radar Engine** | `_skills/rakip-analiz/scripts/radar_engine.py` | Rakip profil analizi + içerik boşluğu tespiti |

---

## 📁 Agent Yapısı

```
_agents/icerik-uretim/
├── AGENT.md                          ← Bu dosya (ana yönerge)
├── config/
│   └── ornek-musteri.yaml              ← Marka profili + varsayılan ayarlar
└── workflows/
    ├── arastirma-yap.md              ← Pazar araştırma workflow'u
    ├── script-yaz.md                 ← Script yazma workflow'u
    ├── ilham-al.md                   ← Rakipten ilham alma workflow'u
    └── hesaplama-scripti.md          ← Hesaplama içerikli script workflow'u
```

> **Not:** `_agents/workflows/icerik-uretimi.md` (slash command: `/icerik-uretimi`) bu agent'ın video üretim adımını tetikler.

---

## 🔄 Uçtan Uca Orkestrasyon Akışı

Bir içerik üretim talebi geldiğinde agent şu akışı izler:

### Adım 1: Talebi Analiz Et
Kullanıcının isteğinden **içerik türünü** belirle:

| Kullanıcı Ne Diyor? | Tetiklenen Workflow |
|---------------------|---------------------|
| "X bölgesini/konusunu analiz et" | `workflows/arastirma-yap.md` → `workflows/script-yaz.md` |
| "200K$ daireyle yatırım hesabı yap" | `workflows/hesaplama-scripti.md` |
| "Şu rakibin videosundan ilham al" | `workflows/ilham-al.md` |
| "Genel bir script yaz" | `workflows/script-yaz.md` |
| "Bu script için video üret" | `/icerik-uretimi` workflow'u |
| "Sıfırdan içerik üret (araştırma → video)" | **Tam Pipeline** (aşağıda) |

### Adım 2: Config'i Yükle
```yaml
# config/ornek-musteri.yaml'dan varsayılan ayarları çek
marka: <MARKA_ADI>
dil: Türkçe
ton: samimi-profesyonel
hedef_kitle: <HEDEF_KITLE_TANIMI>
```

### Adım 3: Pipeline Çalıştır
İçerik türüne göre ilgili workflow'ları **sırayla** çalıştır:

---

## 🚀 5 Workflow'un Büyük Resmi

### A. Araştırma Workflow'u (`workflows/arastirma-yap.md`)
**Tetikleyici:** Bölge analizi, fiyat trendi veya pazar araştırması gerektiğinde
**Girdi:** Konu (bölge adı, trend türü)
**Çıktı:** Metrikler tablosu + fırsat analizi + kaynaklar
**Bağlandığı Bir Sonraki Adım:** Script yazma

### B. Script Yazma Workflow'u (`workflows/script-yaz.md`)
**Tetikleyici:** Araştırma tamamlandığında veya doğrudan script istenmesi
**Girdi:** Araştırma notları veya konu
**Çıktı:** Hook → Script → Tablo → CTA formatında video scripti
**Bağlandığı Bir Sonraki Adım:** Video üretimi

### C. İlham Alma Workflow'u (`workflows/ilham-al.md`)
**Tetikleyici:** Rakip videosundan ilham istenmesi
**Girdi:** Video URL'i veya rakip kanal adı
**Çıktı:** Uyarlanmış orijinal script + ilham kaynağı notu
**Bağlandığı Bir Sonraki Adım:** Video üretimi

### D. Hesaplama Workflow'u (`workflows/hesaplama-scripti.md`)
**Tetikleyici:** Yatırım/mortgage/kira hesabı gerektiren script
**Girdi:** Daire fiyatı, vade, parametreler
**Çıktı:** Hesaplamalı script + tablo + TL karşılıkları
**Bağlandığı Bir Sonraki Adım:** Video üretimi

### E. Video Üretim Workflow'u (`_agents/workflows/icerik-uretimi.md`)
**Tetikleyici:** Script hazır olduğunda video gerektiğinde
**Girdi:** Script veya video prompt'u
**Çıktı:** Kie AI ile üretilmiş video/görsel URL'leri
**Kullandığı Skill:** `_skills/kie-ai-video-production/SKILL.md`

---

## 🎯 Tam Pipeline Örneği (Araştırma → Video)

```
1. [Araştırma]     → konuyu araştır (web + açık kaynak veriler)
2. [Config]        → ornek-musteri.yaml'dan marka kurallarını al
3. [SKILL.md]      → İçerik yazarı kurallarını oku
4. [Script Yaz]    → Araştırma verilerinden bölge analizi scripti üret
5. [Video Prompt]  → Script'e uygun görsel prompt hazırla  
6. [Kie AI]        → Kling 3.0 / Veo 3.1 ile video üret
7. [Seslendirme]   → (opsiyonel) ElevenLabs ile Türkçe dış ses
8. [Teslim]        → Video URL'ini kullanıcıya sun
```

---

## ⚙️ Varsayılan Config

Agent her çalıştığında `config/ornek-musteri.yaml` dosyasından şu değerleri çeker:

- **Marka kimliği:** İsim, platformlar, logo kullanım kuralları
- **Üslup:** Samimi-profesyonel, abartısız, Türkçe + teknik İngilizce terimler
- **Hesaplama metrikleri:** Değer artışı %8/%7, Kira ROI %7, Mortgage %4.5
- **Format kuralları:** Hook → Script → Tablo → CTA yapısı
- **Yasak ifadeler:** "Kesin kazanırsınız", "garantili getiri" gibi abartılı vaatler

Farklı bir marka için çalışılacaksa `config/` altına yeni YAML dosyası oluşturulabilir.

---

## ❌ Hata Senaryoları

| Hata | Çözüm |
|------|-------|
| Araştırma verisi bulunamadı | Web aramasını genişlet, İngilizce anahtar kelimeler dene |
| Hesaplama metrikleri güncel değil | `config/ornek-musteri.yaml` dosyasını güncelle |
| Kie AI 402 (kredi yok) | `_knowledge/api-anahtarlari.md` → yedek anahtar kontrol et |
| Kie AI 500 (sunucu hatası) | 30 saniye bekle, tekrar dene |
| Rakip video bulunamadı | `Projeler/<ICERIK_PROJESI>/rakipler.md` listesini güncelle |
| Transcript alınamadı | Supadata API anahtarını kontrol et |

---

## 📌 İlişkili Kaynaklar

- **Proje:** `Projeler/<ICERIK_PROJESI>/` — Bağımsız proje ekosistemi (dokunulmaz)
- **Referans Scriptler:** `Projeler/<ICERIK_PROJESI>/reference-scripts/`
- **Rakipler:** `Projeler/<ICERIK_PROJESI>/rakipler.md`
- **API Anahtarları:** `_knowledge/api-anahtarlari.md`
- **Ana Workflow:** `_agents/workflows/icerik-uretimi.md` (slash command)
