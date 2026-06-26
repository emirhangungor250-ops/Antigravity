---
description: Hata düzeltme — kök neden analizi + etki analizi + doğrulamalı fix
---

# /hata-duzeltme — Kök Neden Protokolü

> Hata raporlandığında koda dalmadan ÖNCE 3 soruyu cevapla.

## Adım 1 — 3 Soru

1. **Kök neden ne?** Mesaj = semptom. `grep -rn` ile arama yap, Railway loglarını (son 24 sa) oku.
2. **Bu fix nereyi etkiler?** Değişecek fonksiyon/değişkenin tüm çağrı yerleri, import zinciri, env var'lar.
3. **Daha önce görüldü mü?** `_knowledge/hatalar-ve-cozumler.md` aç; entegrasyon ile ilgiliyse `_skills/<servis>/SKILL.md` aç (kural ihlali olabilir).

## Adım 2 — Plan Sun

```
🔍 Kök neden: [1 cümle]
🎯 Çözüm: [1-2 cümle]
📁 Değişecek dosyalar: [liste]
⚠️ Riskler: [varsa]
```

## Adım 3 — Uygula

Teknik fix senin işin; kullanıcıdan onay isteme. Sadece şu durumlarda dur:
- Kullanıcıya görünür davranış değişiyor (ton, dil, akış).
- Geri-dönüşü zor + dışa görünür (deploy, mesaj, silme).
- Ürünsel tercih gerekiyor (hangi model, hangi servis).

**Minimal müdahale:** Sadece kırılan yeri düzelt. 5 satırlık fix için 200 satır değiştirme.

## Adım 4 — Doğrula

1. `python3 -m py_compile <dosya>.py`
2. Import testi: `python3 -c "import <modül>"`
3. Deploy gerekiyorsa push + 60 sn bekle + Railway log kontrolü.

## Adım 5 — Kaydet (Yeni Pattern İse)

`_knowledge/hatalar-ve-cozumler.md`'ye entry ekle:
```
### [Hata Başlığı] — [Tarih]
Semptom · Kök neden · Çözüm · Etkilenen projeler · Önlem
```
