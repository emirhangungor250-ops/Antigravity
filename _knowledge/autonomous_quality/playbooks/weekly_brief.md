# Weekly Brief — Otonom Haftalık Özet Mail

**Çalışma sıklığı:** Pazartesi UTC 08:00 (İstanbul 11:00)
**Hedef süre:** ≤ 20 dakika
**Çıktı:** kullanıcıya tek özet e-posta (`<EMAIL>`)

## Amaç

Otonom kalite sistemi (bug_hunt, test_coverage, simplify, runbook, cost_optimization, blind_automation_hunt) son 7 günde ne yaptı? Kullanıcı `logs/` JSON'larını okumak zorunda kalmasın — Pazartesi sabah inbox'ında özet bulsun.

## Adım adım

### 1) Repo'yu çek

```
git clone <GITHUB_REPO_URL> /tmp/antigravity
cd /tmp/antigravity
git checkout main
git pull --rebase origin main
```

### 2) Son 7 günün log'larını oku

```bash
find _knowledge/autonomous_quality/logs/ -name "*.json" -mtime -7
```

Veya tarih bazlı:

```python
import json, glob, datetime
since = datetime.date.today() - datetime.timedelta(days=7)
logs = []
for f in glob.glob("_knowledge/autonomous_quality/logs/*.json"):
    with open(f) as fh:
        log = json.load(fh)
    log_date = datetime.date.fromisoformat(log["date"])
    if log_date >= since:
        logs.append(log)
```

### 3) Aggregate metrics

- Toplam commit sayısı (low-risk fix, doc, test, refactor)
- Toplam PR sayısı (henüz merge edilmemiş — kullanıcı kararı bekliyor)
- Hangi projeler tarandı, hangileri hâlâ rotasyona uğramadı (son tarama 14+ gün önce)
- Test sayısı (eklenen toplam)
- Runbook sayısı (yazılan toplam)
- Routine başına süre dağılımı + hata sayısı
- Cost optimization: tahmini USD/ay + trend

### 4) "Karar gerektirenler" bölümü

Açık PR'ları listele (henüz merge edilmemiş `autonomous/*` branch'leri):

```bash
gh pr list --label autonomous --state open --limit 20 --json number,title,createdAt,url
```

Her PR için 1 satır özet: ne yapıyor, hangi proje, neden human gerekli.

Ayrıca `cost_optimization` `recommendations` field'ından "human action needed" olanları topla (atıl servis adayları vb.).

### 5) Mail içeriği

E-posta gönderim için projedeki mevcut altyapıya bak:
- `_skills/eposta-gonderim/` skill'i Gmail API ile gönderim yapıyor
- Veya `_skills/akilli-watchdog` / `Projeler/Akilli_Watchdog` içinde mail sender kodu var
- En basit: Python `smtplib` + Gmail App Password (master.env'de)

**Subject:** `[Otonom Kalite] Haftalık Özet — <YYYY-MM-DD>`

**Body (HTML veya markdown-to-HTML):**

```markdown
# Geçen hafta sistemde neler oldu

## Özet
- **<N> commit** ana branch'e atıldı (otomatik, low-risk)
- **<M> PR** kararını bekliyor
- **<X> proje** tarandı, **<Y> proje** son 14 günde hiç görülmedi
- **<Z> yeni test** eklendi, **<W> runbook** üretildi

## Kararını bekleyen PR'lar
| # | Proje | Konu | Risk | Link |
|---|---|---|---|---|
| 42 | eCom | Race condition fix | medium | <url> |
| ... | ... | ... | ... | ... |

(Hiç PR yoksa: "Bu hafta kararını bekleyen şey yok.")

## Yapılanlar (özet)

### Bug Hunt (7 gece çalıştı)
- <proje>: <kısa açıklama>
- <proje>: <kısa açıklama>
...

### Test Coverage (2 koşu)
- <proje>: 7 test
- <proje>: 4 test

### Simplify (1 koşu)
- <proje>: 87 satır silindi

### Runbook (1 koşu)
- <proje>: RUNBOOK.md eklendi

### Cost Optimization
- Bu hafta tahmini Railway: $<X>/ay (trend: <%Y> <yön>)
- Atıl servis adayı: <varsa>
- Worker→cron geçiş PR'ı: <varsa, link>

## Kör Nokta — gözden kaçan zayıf mekanizmalar

`blind_automation_hunt` log'larındaki `findings`'i buraya **olduğu gibi** taşı — onlar zaten ürün dilinde yazıldı, teknik dile çevirme, kısaltma.

Her bulgu için: ne yapıyor, neyi kaçırıyor, öneri + maliyet. Varsa öneri PR linki.

(Bulgu yoksa: "Bu hafta gözden kaçan zayıf mekanizma bulunmadı.")

## Otomasyon filosu sağlığı — ölü ve kayıtsız routine kontrolü

`_knowledge/routines.json` tüm cron'ların kaydıdır. İki kontrol yap:

1. **Ölü routine:** `routines.json`'daki `log_prefix`'i dolu her routine için `logs/<prefix>_*.json`'a bak. En yeni log `beklenen_aralik_gun * 3` günden eskiyse o routine ölmüş olabilir — brief'te "**X routine'i N gündür log yazmıyor, kontrol et**" diye yaz.
2. **Kayıtsız routine:** `logs/` altında `routines.json`'da karşılığı olmayan bir prefix varsa — biri yeni routine ekleyip kayda yazmayı unutmuş demektir. "**X log yazıyor ama routines.json'da yok, eklenmeli**" diye yaz.

İkisi de yoksa: "Otomasyon filosu temiz — tüm cron'lar kayıtlı ve çalışıyor."

## Riskler / hatalar
- <routine> <proje>: <ne hata aldı> — gelecek hafta tekrar denenecek

## Rotasyon durumu
Son 14 gündür dokunulmamış projeler: <liste> — önümüzdeki haftalarda rotasyon onlara gelecek.

---
🤖 Otonom Sistem Kalitesi — weekly_brief routine · Claude Opus 4.7
```

### 6) İki kanala birden yaz

Gmail MCP'de `send` tool'u yok — sadece `create_draft` var. Bu yüzden brief iki kanala birden gider:

**(a) Gmail taslağı:**
- `create_draft` ile `<EMAIL>`'a taslak oluştur
- `list_labels` ile `OtomKalite/Haftalik` var mı bak, yoksa `create_label`
- `label_message` ile taslağa bu label'ı uygula
- ASLA `WatchdogInternal` kullanma (o auto-archive)

**(b) Repo dosyası:**
- Aynı özeti `_knowledge/autonomous_quality/WEEKLY_BRIEF_LATEST.md`'ye yaz (üzerine yaz, append değil)
- kullanıcı Pazartesi `git pull` yapınca en güncel brief bu dosyada hazır olur

İkisi de zorunlu — biri başarısız olursa diğeri yine de garanti bilgi kanalı.

### 7) Log yaz

`logs/weekly_brief_<YYYY-MM-DD>.json`:

```json
{
  "routine": "weekly_brief",
  "date": "<YYYY-MM-DD>",
  "logs_processed": 12,
  "stats": {
    "commits": 18,
    "prs_open": 3,
    "tests_added": 14,
    "runbooks_added": 1,
    "lines_removed": 287
  },
  "draft_created": true,
  "draft_id": "<gmail draft id>",
  "latest_md_written": true,
  "duration_min": 8
}
```

### 9) Yapma

- **Asla** birden fazla mail at (sadece 1 özet)
- **Asla** `WatchdogInternal` label'ı kullan (o auto-archive)
- **Asla** secret/token mail body'sine sızsın
- **Asla** kararını beklemeyen PR'ı "karar bekleyen" olarak gösterme (gh pr list ile gerçek state'i çek)
- **Asla** "Geçen hafta yaptıklarım listesi" yerine genel teknik özet yaz — somut sayılar + somut proje adları

## Output kontrol

Mail body ≤ 800 kelime. Daha uzun = okunmayacak; daha kısa = bilgi yetersiz. PR tablosu varsa o ayrı sayılır.
