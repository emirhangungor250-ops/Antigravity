# Runbook — Otonom RUNBOOK.md Üretimi

**Çalışma sıklığı:** Pazar UTC 02:00 (İstanbul 05:00)
**Hedef süre:** ≤ 40 dakika
**Çıktı:** Bir projeye `RUNBOOK.md` dosyası, `main`'e direkt commit (low-risk, sadece doc).

## Amaç

Antigravity projelerinin çoğunda README var (amaç + stack + env setup) ama **runbook yok** — bir şey bozulduğunda nereye bakılır, nasıl restart edilir, hangi env var ne işe yarar belli değil. Bu routine her hafta runbook'u olmayan bir projeye otomatik RUNBOOK.md yazar.

## Adım adım

### 1) Repo'yu çek

```
git clone <GITHUB_REPO_URL> /tmp/antigravity
cd /tmp/antigravity
git checkout main
git pull --rebase origin main
```

### 2) Runbook'u olmayan proje bul

```bash
for proj in Projeler/*/; do
    if [ ! -f "$proj/RUNBOOK.md" ]; then
        echo "$proj"
    fi
done
```

Rotasyon offset = 21:

```python
candidates = [p for p in projects if not os.path.exists(f"Projeler/{p}/RUNBOOK.md")]
if not candidates:
    # Hepsinin runbook'u var — refresh modu: en eskisini yenile
    candidates = sorted(projects, key=lambda p: os.path.getmtime(f"Projeler/{p}/RUNBOOK.md"))
project = candidates[(epoch_day + 21) % len(candidates)]
```

### 3) Projeyi tanı

Okumalı dosyalar (varsa):
- `README.md` — amaç + stack
- `railway.json` — deploy config (cron schedule, start command, root directory)
- `.env.example` — env var listesi
- `requirements.txt` / `package.json` — dependency listesi
- Entry point dosyası (`main.py`, `app.py`, `index.js`, `bot.py`)
- En son 5 commit log (`git log --oneline -5 -- Projeler/<proje>`)
- Eğer cron ise: schedule + son çalışma zamanı (Railway API ile, ama bu opsiyonel)

### 4) RUNBOOK.md şablonu

```markdown
# RUNBOOK — <Proje Adı>

> Bu runbook, projenin **production'da bozulduğunda** nereye bakılacağını ve nasıl iyileştirileceğini anlatır.
> Geliştirme dokümantasyonu için: `README.md`.

## Servis kimliği

- **Türü:** cron / worker / web servis / lokal script
- **Railway servis adı:** <varsa>
- **Schedule (cron için):** `<cron expression>` (UTC) → İstanbul `<saat>`
- **Tetikleyici (worker için):** webhook / queue / manuel
- **Komşu servisler:** <bağımlı olduğu/onu çağıran diğer projeler>

## Health check (sağlıklı mı?)

Şunlardan biri yeşilse servis sağlıklıdır:
- Son <X> saat içinde başarılı log: `<beklenen log satırı>`
- Son <Y> dakika içinde "heartbeat" mail/Notion satırı
- Railway dashboard'da son deployment SUCCESS + son cron run SUCCESS

## Hızlı triage (5 dakika)

1. **Railway dashboard'da son deploy ne durumda?** SUCCESS değilse → build log'a bak
2. **Son cron run'ında hata var mı?** → log'da `ERROR`, `Traceback`, `Exception` ara
3. **API anahtarı süresi dolmuş mu?** → `.env` ile `<dış servis>` token'ı arasındaki bağı kontrol et
4. **Bağımlı servis ayakta mı?** → `<bağımlılıklar>` listelendi mi

## Sık karşılaşılan hatalar

### Hata: `<örnek hata mesajı veya pattern>`

- **Sebep:** <bilinen sebep, yoksa "henüz görülmedi">
- **Çözüm:** <adımlar>
- **Geçmişte vuku bulan:** <varsa commit veya tarih referansı>

(Bu bölüm runbook ilk üretildiğinde boş olabilir; bug_hunt routine'leri buraya zamanla yazar.)

## Manuel çalıştırma

Lokalde test etmek için:

```bash
cd Projeler/<proje>
cp .env.example .env       # değerleri _knowledge/credentials/master.env'den al
pip install -r requirements.txt   # veya npm install
python main.py             # veya entry point
```

Production'da anlık tetiklemek için (Railway):

- Cron: cronSchedule override (min 5 dk) — `serviceInstanceDeployV2` mutation
- Worker: `serviceInstanceRedeploy` mutation
- Web: HTTP endpoint mevcutsa direkt request

## Rollback

Son deploy'u geri almak için:

1. `gh run list -L 10 -R <GITHUB_REPO>` veya git log'dan son SUCCESS commit'i bul
2. `git revert <bozuk-commit>` → push
3. Railway watchPattern açıksa otomatik deploy başlar; kapalıysa `serviceInstanceDeployV2` ile manuel

## Env var sözlüğü

| Env var | Ne işe yarar | Nereden alınır | Süresi dolar mı? |
|---|---|---|---|
| `<ÖRNEK_TOKEN>` | <açıklama> | `_knowledge/credentials/master.env` | <var/yok> |

(`.env.example`'daki tüm değişkenleri buraya tek tek ekle. Comment'lerden açıklama oku.)

## Maliyet notları

- Railway: <vCPU/RAM tahmini, varsa>
- Dış servis (Apify, Kie AI, Anthropic, OpenAI vb.): <aylık tahmini USD>
- Pahalandığı durumlar: <varsa>

## İletişim

Bu servis bozulduğunda etkilenenler:
- <kullanıcı/ekip>

Production'a deploy yetkisi: proje sahibi.

---
Üretildi: <YYYY-MM-DD> · Otonom runbook routine (Claude Opus 4.7)
```

### 5) Spesifik proje için doldurma

Şablonu doldururken **uydurmayın**:
- Dosyalardan, README'den, env.example'dan çıkarabildiğin şeyi yaz
- "Bilinmiyor" yazmak, hayal etmekten iyidir
- "Sık karşılaşılan hatalar" bölümü genelde boş çıkar (henüz görülmemiş) — boş bırak, gelecekte bug_hunt dolduracak
- "Komşu servisler" — projedeki dosyalarda diğer projelerin URL/API'sini grep'le; bulamıyorsan "yok"

### 6) Commit + push

```bash
git add Projeler/<proje>/RUNBOOK.md
git commit -m "docs(<proje>): otonom-kalite — RUNBOOK.md eklendi

Üretildi: $(date +%F)
Risk: low (sadece doc)

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
git push origin main
```

### 7) Log yaz

`logs/runbook_<YYYY-MM-DD>.json`:

```json
{
  "routine": "runbook",
  "project": "<proje>",
  "mode": "new | refresh",
  "sections_filled": ["servis_kimligi", "health_check", "triage", "env_vars", ...],
  "sections_left_empty": ["sik_hatalar", "rollback"],
  "duration_min": 32
}
```

### 8) Yapma

- **Asla** runbook'a hayal mahsulü bilgi yaz (uydurma env var, var olmayan komşu servis, çalışmayan komut)
- **Asla** `README.md`'yi sil veya değiştir (runbook README'ye ek, yerine geçmez)
- **Asla** runbook'a secret/token yaz
- **Asla** "TODO: doldur" placeholder bırakma — doldurulamayanı tamamen sil veya "(henüz görülmedi)" yaz

## Output kontrol

Runbook 150-400 kelime arası olmalı. Daha kısa = yetersiz, daha uzun = uydurma var.
