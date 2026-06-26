---
description: Video scripti üret — bölge analizi, gayrimenkul yatırımı veya hesaplama konseptlerinde
---

# Script Yaz — Video Scripti

> 🤖 **Agent:** Bu workflow `_agents/icerik-uretim/AGENT.md` agent'ının bir parçasıdır.
> Bağımsız olarak da çalışabilir (`/script-yaz`), ancak tam pipeline için agent yönergesini takip et.

Seçilen marka/müşteri için sosyal medya video scripti üretme adımları.

## Bağlam
- **Agent:** `_agents/icerik-uretim/AGENT.md`
- **Config:** `_agents/icerik-uretim/config/ornek-musteri.yaml`
- **Skill:** `Projeler/<ICERIK_PROJESI>/skills/icerik-yazari/SKILL.md` → ÖNCE OKU
- **Referans Scriptler:** `Projeler/<ICERIK_PROJESI>/reference-scripts/`
- **Hesaplama:** `Projeler/<ICERIK_PROJESI>/tools/calculator.py`

## Adımlar

1. **SKILL.md dosyasını oku**
   - `Projeler/<ICERIK_PROJESI>/skills/icerik-yazari/SKILL.md`
   - Üslup kurallarını, format şablonlarını ve yasak ifadeleri öğren

2. **Config'den marka ayarlarını çek**
   - `_agents/icerik-uretim/config/ornek-musteri.yaml`
   - Ton, hedef kitle, yasak ifadeler ve format yapısını doğrula

3. **Script türünü belirle**
   - `bölge_analizi` → Hook + Tablo formatı
   - `gayrimenkul_yatirimi` → Soru-cevap formatı  
   - `hesaplama` → Hook + Tablo + Net rakam formatı
   - `ilham` → Rakip scriptten uyarlama

4. **Referans scriptleri oku** (en az 3 tane)
   - İlgili klasördeki referans dosyasını aç
   - Ton, ritim ve format tutarlılığını yakala

5. **Gerekirse hesaplama yap**
   - `tools/calculator.py` ile gerçek rakamları doğrula
   - Hesaplama scriptlerinde tablo ZORUNLU

6. **Scripti yaz**
   - SKILL.md kurallarına uy
   - Hook → Script → Tablo → CTA yapısını koru
   - TL karşılığı ekle (hedef kitle Türkiye'den)

7. **Kontrol listesi**
   - [ ] Format doğru mu?
   - [ ] Üslup tutarlı mı?
   - [ ] Abartılı ifade yok mu?
   - [ ] CTA var mı?
   - [ ] Kaynak linki var mı? (rakam içeriyorsa)

8. **Bir sonraki adım** (agent pipeline'da)
   - Script hazırsa video üretimi için `_agents/workflows/icerik-uretimi.md` workflow'una geç

## Script Formatları

### Bölge Analizi
```
### Hook
(1-2 cümle — bölgenin riski veya fırsatını vurgular)

### Script
(Dengeli artı/eksi analizi)

### Tablo
| ✅ Avantaj | ❌ Dezavantaj |
|---|---|
```

### Hesaplama
```
#### Hook
(Hedef kitleye doğrudan soru)

#### Script
(Adım adım hesap + tablo)

| Yıl | Ödeme | Kira | Değer |
|-----|-------|------|-------|
```
