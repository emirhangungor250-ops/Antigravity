# Bug Hunt — Otonom Gecelik Bug Avı

**Çalışma sıklığı:** Her gün UTC 23:00 (İstanbul 02:00)
**Hedef süre:** ≤ 60 dakika
**Çıktı:** 0-1 low-risk commit (main'e) + 0-2 medium/high PR (`autonomous/bug-hunt/<tarih>-<proje>` branch'inde)

## Amaç

Antigravity'deki aktif projelerden birini her gece derinlemesine tara. Bulunan bug'ları sınıflandır:
- Low-risk olanları direkt düzelt + push.
- Davranış değiştirenleri PR olarak aç (otomatik merge yok — kullanıcı haftalık brief'ten görüp karar verir).

## Adım adım

### 1) Repo'yu çek

```
git clone <GITHUB_REPO_URL> /tmp/antigravity
cd /tmp/antigravity
git checkout main
git pull --rebase origin main
```

### 2) Proje seç

`_knowledge/autonomous_quality/README.md` içindeki rotasyon formülünü uygula:

```python
import os, datetime, subprocess

EXCLUDED = {"_arsiv", "Patron_Dashboard", "youtube-content-engine"}
projects = sorted([
    p for p in os.listdir("Projeler")
    if not p.startswith("_") and p not in EXCLUDED
    and os.path.isdir(f"Projeler/{p}")
])
epoch_day = (datetime.date.today() - datetime.date(2026, 5, 1)).days
project = projects[(epoch_day + 0) % len(projects)]   # offset=0 → bug_hunt
print(f"Hedef: {project}")
```

`logs/bug_hunt_<son-7-gün>.json` dosyalarına bak — aynı projeyi geçen hafta taradıysan, bir sonraki sıradaki projeye geç.

### 3) Projeyi derinlemesine tara

Şu kategoriler için kontrol et:

**A. Hata yakalama eksikleri**
- `except Exception` veya `except:` ile her şey yakalanıp sessizce yutuluyor mu?
- API çağrıları timeout/retry içermiyor mu?
- Disk/network yazımı flush + sync edilmemiş mi?

**B. Race condition / lock**
- Concurrent çalıştırılabilecek cron'larda dosya lock yok mu?
- `if exists: read; else: create` pattern'i race'e açık mı?

**C. Hardcoded değerler / sızıntı**
- Hardcoded URL, e-posta, telefon, token (env'e taşı)
- Test/staging URL'leri production kodunda?
- API key'in repo'ya kaçtığı yer var mı? (`git log -p -S "sk-" --all` benzeri tarama)

**D. Deprecated API / library**
- `datetime.utcnow()` → `datetime.now(timezone.utc)`
- `requests` retry'sız → `urllib3.Retry` ile
- Python `asyncio.get_event_loop()` → `asyncio.get_running_loop()`

**E. Eksik validation**
- User input doğrudan SQL/shell/eval'a giriyor mu?
- JSON parse'da try/except yok mu?
- File path'lerde traversal (`../`) kontrolü yok mu?

**F. Dead code**
- Asla çağrılmayan fonksiyon, import edilmemiş modül
- `if False:` veya commented-out büyük blok
- `TODO: kaldırılacak` 60+ gündür duranlar

**G. Logging eksikleri**
- Production cron'da `print` kullanan dosya (logger'a geçir)
- Error yakalanıp log'lanmayan branch'ler

### 4) Bulguları sınıflandır

Her bulgu için risk etiketi ata. Sınıflandırma kuralları için `README.md → Risk sınıflandırması`'a bak.

**En fazla:** 1 low-risk commit + 2 medium/high PR. Daha fazlasını bulduysan, en kritik 3'ünü seç, gerisini `actions[].skipped`'a kaydet (ileride başka routine bakar).

### 5) Düzeltmeleri uygula

**Low-risk fix → main'e direkt commit:**

```bash
git checkout main
# fix uygula
python -m py_compile <değişen.py>          # veya node --check <değişen.js>
pytest <proje>/ 2>&1 | tail -20            # mevcut testler hala geçiyor mu?
git add <dosyalar>
git commit -m "fix(<proje>): otonom-kalite — <kısa açıklama>

Detay: <bulgu>
Risk: low

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
git push origin main
```

**Medium/high fix → PR:**

```bash
git checkout -b autonomous/bug-hunt/$(date +%F)-<proje>
# fix uygula
python -m py_compile / pytest doğrulaması
git add <dosyalar>
git commit -m "fix(<proje>): <başlık>

<açıklama>
Risk: medium/high
Neden human review: <sebep>

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
git push -u origin autonomous/bug-hunt/$(date +%F)-<proje>
gh pr create --title "fix(<proje>): <başlık>" --body "$(cat <<'EOF'
## Bug
<kısa açıklama>

## Çözüm
<kısa açıklama>

## Risk
<medium / high>

## Test
- [x] Mevcut testler hala geçiyor
- [x] py_compile / node --check başarılı
- [ ] Production'da gözlemlenmesi gereken davranış: <varsa>

🤖 Generated with [Claude Code](https://claude.com/claude-code) — autonomous bug_hunt routine
EOF
)"
```

### 6) Log yaz

`logs/bug_hunt_<YYYY-MM-DD>.json` dosyasını oluştur (README'deki format). `weekly_brief` Pazartesi okuyacak.

```bash
# Log dosyasını git'e ekle ve push'la (ayrı commit, fix commit'leriyle karışmasın)
git checkout main
git add _knowledge/autonomous_quality/logs/bug_hunt_$(date +%F).json
git commit -m "chore(autonomous): bug_hunt log — $(date +%F)"
git push origin main
```

### 7) Hata durumunda

- py_compile veya test başarısız → fix'i geri al (`git restore`), `errors` field'ına yaz, devam et
- `git push` reddedildi → `git pull --rebase` + tekrar dene; iki kez başarısız → branch'i bırak, `errors`'a yaz
- Routine 60 dakikayı aştı → bulduklarını commit/PR yap, geri kalanı `skipped`'a yaz, çık

### 8) Yapma

- **Asla** main'e force push
- **Asla** commit/PR mesajında "geçici", "WIP", "TODO" kullanma
- **Asla** birden fazla bağımsız bug'ı tek commit'te birleştirme (her bug ayrı commit veya ayrı PR)
- **Asla** üretim env var değerini kod içine yazma (env'e taşırken `.env.example`'a placeholder ekle)
- **Asla** mevcut test'i sil/disable et — sadece yeni test ekle veya bozulmuşsa fix'le
- **Asla** kullanıcının "bekleyen iş" listesinde olan bir feature'ı kendi başına başlatma (sadece bug fix yap)

## Output kontrol

İş bitince log dosyasında şunlar olmalı:
- `actions` (ne yaptın): 0 veya daha fazla commit/pr objesi
- `skipped`: zaman/risk nedeniyle pas geçtiklerin
- `errors`: tekniği başarısız olanlar (test geçmedi, push başarısız vs.)
- `duration_min`: toplam süre

Hiçbir bug bulamadıysan da log yaz: `actions: []`, `note: "Temiz tarama, fix gerekmedi"`.
