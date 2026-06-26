---
description: Seçilen niş/pazar hakkında internette araştırma yap
---

# Araştırma Yap — Pazar/Niş Araştırması

> 🤖 **Agent:** Bu workflow `_agents/icerik-uretim/AGENT.md` agent'ının bir parçasıdır.
> Bağımsız olarak da çalışabilir (`/arastirma-yap`), ancak tam pipeline için agent yönergesini takip et.

Seçilen niş/pazar hakkında güncel araştırma yapma adımları.

## Bağlam
- **Agent:** `_agents/icerik-uretim/AGENT.md`
- **Config:** `_agents/icerik-uretim/config/ornek-musteri.yaml`
- **Müşteri:** `config/ornek-musteri.yaml` ile tanımlanır
- **Skill:** `_skills/kie-ai-video-production/SKILL.md`
- **Rakip Analiz Skill:** `_skills/rakip-analiz/SKILL.md`
- **Kaynak Script'ler:** `Projeler/<ICERIK_PROJESI>/reference-scripts/`

## Adımlar

1. **Araştırma konusunu belirle**
   - Bölge analizi mi? (Downtown, JVC, Business Bay, vb.)
   - Fiyat trendi mi?
   - Kira getirisi mi?
   - Yeni proje lansmanı mı?

2. **Güncel veri topla** (Perplexity veya web araması)
   - Resmi/açık kaynak piyasa verileri
   - Property Finder, Bayut gibi platformlar
   - Son 12 aydaki değer artışı
   - Kira ROI yüzdesi

3. **Rakip içerik analizi** (opsiyonel)
   - `_skills/rakip-analiz/SKILL.md` → Radar Engine ile rakip içerikleri analiz et
   - `_skills/lead-generation/SKILL.md` → Apify ile rakip videoları bul
   - Transcript'i analiz et
   - `Projeler/<ICERIK_PROJESI>/rakipler.md` dosyasını güncelle

4. **Veriyi doğrula**
   - Sayısal iddialar için kaynak linki ekle
   - Format: `Kaynak: [Link](url) — Veri: %X değer artışı`

5. **Çıktıyı hazırla**
   - Markdown formatında özet rapor
   - Kullanılabilir metrik tablosu
   - Script üretimi için hazır notlar

6. **Bir sonraki adım** (agent pipeline'da)
   - Araştırma çıktısını `workflows/script-yaz.md` veya `workflows/hesaplama-scripti.md` workflow'una aktar

## Çıktı Formatı

```markdown
## [Bölge/Konu] Araştırma Özeti — [Tarih]

### Temel Metrikler
| Metrik | Değer | Kaynak |
|--------|-------|--------|
| Ortalama fiyat | $X/m² | [Link] |
| Değer artışı | %X/yıl | [Link] |
| Kira ROI | %X | [Link] |

### Fırsat Analizi
...

### Riskler
...

### Kaynaklar
- [Link 1](url)
- [Link 2](url)
```
