---
description: Deploy sonrası kapsamlı stabilizasyon — tek seferde tüm potansiyel bugları tespit, düzelt, doğrula
---

# /stabilize — Production Stabilizasyon

> Deploy edildikten **sonra** çalıştır. Amacı: 3-4 iterasyon yerine TEK SEFERDE tüm bugları yakalamak.
> Platform bağımsız (Railway / Netlify / GitHub Pages / vs).

## Kullanım

```
/stabilize <ProjeAdı>
```

## Adım 0 — Bağlam Yükle

1. Proje klasörünü oku: `Projeler/<ProjeAdı>/` — `README.md`, ana entry point, `requirements.txt`/`package.json`, `railway.json`/`netlify.toml`.
2. `_knowledge/deploy-registry.md`'den platform + servis ID'lerini al.
3. Hangi entegrasyonlar var? (Supabase, Notion, Apify, Telegram) → ilgili `_skills/<entegrasyon>/SKILL.md` aç (kural ihlali kontrolü için).

## Adım 1 — Statik Analiz (Kodu okumadan)

```bash
# 1.1 Syntax
python3 -m py_compile *.py

# 1.2 Import zinciri
python3 -c "import importlib,os; [importlib.import_module(f[:-3]) for f in os.listdir('.') if f.endswith('.py')]"

# 1.3 Hardcoded secret
grep -rnE "(sk-|AIza|ghp_|ghs_|xoxb-|Bearer )" --include="*.py" --include="*.js"

# 1.4 Unpinned dependency
grep -v "==" requirements.txt | grep -v "^#" | grep -v "^$"

# 1.5 Legacy nixpacks tuzağı
ls Aptfile apt.txt 2>/dev/null && echo "SİL — Nixpacks yoksayar"

# 1.6 Dependency name mismatch
# google.genai → google-genai · PIL → Pillow · telegram → python-telegram-bot
```

## Adım 2 — Semantik Analiz (Kodu okuyarak)

Entry point'ten başlayarak şunları kontrol et:
- **Caller ↔ Callee imza:** `func(x=...)` çağrılarındaki kwarg'lar, fonksiyon tanımında gerçekten var mı? (`TypeError: unexpected keyword argument` hatasını deploy ÖNCESİ yakalar.)
- **State persistence:** RAM'de `dict()` ile tutulan kritik state var mı? Restart'ta uçar mı?
- **Logging:** `print(e)` veya `except: pass` patternleri → `logging.error(..., exc_info=True)`'a çevir.
- **Fault tolerance:** Dış API çağrısı try/except + backoff içinde mi? Rate limit yedekleri var mı?
- **Env var bütünlüğü:** `.env.example` veya kod'da geçen tüm env key'leri platformda tanımlı mı?

## Adım 3 — Runtime Doğrulaması (Gerçek ortamda)

### 3.1 Deployment Status
- Railway → son `deployment.status` `SUCCESS` mi?
- Netlify → son deploy `published` mı?

### 3.2 Log Taraması (60 sn bekle, sonra son 100 satır)
Fatal pattern listesi:
```
Traceback · ImportError · ModuleNotFoundError · AttributeError ·
NameError · KeyError · TypeError · Process exited with code 1
```

### 3.3 Gerçek Çıktı Doğrulaması
Proje veri üretiyorsa → çıktıyı **hedef sistemden** oku (`/self-review` mantığı):
- Sheets/Notion'a yazıyorsa → kayıt sayısı + örnek içerik.
- Mail atıyorsa → `in:sent` sorgusu.
- Dosya üretiyorsa → dosya var mı + boyut > 0 mı?

### 3.4 Cron Tetiklemesi (Sadece cron projeler)
- Manuel `cronSchedule` override (min 5 dk) ile tetikle.
- 90 sn bekle → log + çıktı re-check.

## Adım 4 — Fix + Doğrulama Döngüsü

Her bulgu için:
1. Kök nedeni netle (`/hata-duzeltme` mantığı — 3 soru).
2. Minimal fix uygula.
3. Push + yeni deploy.
4. Adım 3.2 + 3.3'ü tekrar koştur.
5. Temiz değilse → tekrar fix.

## Adım 5 — Knowledge + README Senkron

- Yeni bir hata pattern'i bulundu mu → `_knowledge/hatalar-ve-cozumler.md`'ye entry.
- Davranış değişti mi → `Projeler/<ProjeAdı>/README.md` güncelle.
- `_knowledge/deploy-registry.md` (env, watchPatterns, schedule) tutarlı mı?

## Çıktı Raporu

```
🛡️ /stabilize — <ProjeAdı>
Statik: X bulgu / Y düzeltildi
Semantik: X bulgu / Y düzeltildi
Runtime: SUCCESS · log temiz · çıktı doğrulandı
Cron (varsa): tetiklendi · 90sn sonra log temiz
Süre: ~X dk
```

## Yaygın Bulgular (Hızlı Referans)

| Bulgu | Fix |
|---|---|
| `AttributeError: 'NoneType' has no attribute X` | Env var eksik veya None dönen API |
| `ModuleNotFoundError` | requirements.txt'te paket eksik veya isim yanlış (`google-genai`) |
| Cron 5 dk önce tetiklendi ama log yok | `cronSchedule` override yapılmamış / watchPatterns yanlış |
| Servis FAILED sebepsiz | `rootDirectory` boş (monorepo'da zorunlu) |
| Build başarılı ama runtime crash | `nixpacks.toml` eksik (ffmpeg/cairo/chromium) |
