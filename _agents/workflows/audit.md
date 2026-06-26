---
description: Audit — tüm projelerin kod kalitesi + güvenlik + mimari sağlığını denetle (statik kod + mimari analiz)
---

# /audit — Proje Sağlık Denetimi

> Antigravity ekosistemindeki projelerin "sağlıklı yazılıp yazılmadığını" denetler.
> Watchdog "ayakta mı" sorar; bu komut "doğru mu yazılmış" sorar.

## Modlar

| Çağrı | Kapsam |
|---|---|
| `/audit` | Statik kod denetimi — tüm projeler |
| `/audit <proje>` | Statik kod denetimi — tek proje |
| `/audit mimari <proje>` | Tek projede derin mimari analiz (state, log, fault tolerance, modülerlik) |

---

## Mod 1: Statik Kod Denetimi (default)

1. Audit script'ini çalıştır:
   ```bash
   python3 _agents/proje_audit.py             # tüm projeler
   python3 _agents/proje_audit.py --project <ProjeAdı>
   ```
2. Detaylı rapor `_knowledge/son-audit-raporu.md`'ye yazılır. Sadece **özet** sun:
   - Toplam kritik / uyarı sayısı.
   - En acil 3 proje (örn. hardcoded API key, syntax hatası).
3. Sorun azsa → bu chat'te düzelt. Çoksa → kullanıcıya `[Proje]` için yeni chat öner (context koruması).

**Yaygın fix patternleri:**
- Hardcoded key → `os.environ.get("KEY")`, `master.env`'ye ekle.
- Unpinned dependency → `paket==X.Y.Z` ile sabitle.
- `print(e) / except: pass` → `logging.error(..., exc_info=True)`.
- Syntax error → dosyayı oku ve düzelt.

---

## Mod 2: Mimari Analiz

Tek proje için derin analiz. Hedef: 4 kategoride kalite puanı + düzeltme planı çıkar.

### Adım 1 — Keşif
- Proje klasörünü tara, `main.py` / `app.js` / `services/` gibi kritik dosyaları oku.
- Veri depolama, kullanıcı işleme, dış API çağrı noktalarını hedef al.

### Adım 2 — 4 Kategoride Analiz

| Kategori | Soru | Beklenen |
|---|---|---|
| **State Persistence** | State `dict()` ile RAM'de mi? Restart'ta uçar mı? | Notion / Sheets / SQLite / disk JSON |
| **Event Logging** | Sadece `print()` mi? Geçmiş konuşmalar dışarıdan okunabiliyor mu? | Persistent log kaynağı (NotionLogger vb.) |
| **Fault Tolerance** | 500'de patlıyor mu? Failed işler kayboluyor mu? | try/except, backoff, dead letter |
| **Modülerlik** | Business logic + API entegrasyonu iç içe mi? | Servis katmanı ayrımı |

### Adım 3 — Rapor (KODA DOKUNMA)
Mimar puanı (X/10) + mevcut durum + anti-pattern listesi + madde madde düzeltme planı.

### Adım 4 — Onay
Kullanıcı planı onaylarsa → uygula. Sonrasında `/degisiklik-kontrol` + `/self-review` zorunlu.
