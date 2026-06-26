# Autonomous Quality — Otonom Sistem Kalitesi

Bu klasör, Anthropic cloud routine'lerinin her gece/hafta çalıştırdığı otonom kalite operasyonlarının kılavuzunu (playbook'larını) tutar.

## Sistemin amacı

Antigravity monorepo'sundaki 25+ aktif projenin kalitesini, kullanıcının müdahalesi olmadan sürekli artırmak.

Cloud routine'ler bu klasördeki playbook'ları okur, talimatlara uyar, yaptıklarını `logs/` altına JSON olarak yazar. Pazartesi sabahı `weekly_brief` playbook'u tüm log'ları okur, tek özet mail atar.

## Routine takvimi (saatler İstanbul, UTC+3)

| Routine | Cron (UTC) | Cron (IST) | Playbook | Çıktı türü |
|---|---|---|---|---|
| bug_hunt | `0 23 * * *` | Her gün 02:00 | playbooks/bug_hunt.md | Commit + PR |
| test_coverage | `0 0 * * 2,5` | Salı + Cuma 03:00 | playbooks/test_coverage.md | Commit |
| simplify | `0 1 * * 6` | Cumartesi 04:00 | playbooks/simplify.md | Commit + PR |
| runbook | `0 2 * * 0` | Pazar 05:00 | playbooks/runbook.md | Commit |
| cost_optimization | `0 4 * * 3` | Çarşamba 07:00 | playbooks/cost_optimization.md | Rapor + opsiyonel commit |
| blind_automation_hunt | `0 0 * * 4` | Perşembe 03:00 | playbooks/blind_automation_hunt.md | Rapor + opsiyonel PR |
| weekly_brief | `0 8 * * 1` | Pazartesi 11:00 | playbooks/weekly_brief.md | E-posta |

## Aktif proje rotasyonu

Playbook'lar her çalıştığında deterministik formula ile bir aktif proje seçer:

```
project = ACTIVE_PROJECTS[(epoch_day + routine_offset) % len(ACTIVE_PROJECTS)]
```

`routine_offset` her routine için farklıdır (bug_hunt=0, test_coverage=7, simplify=14, runbook=21, blind_automation_hunt=28, cost_optimization=tüm projeler — tek tek dolaşmaz, hepsini tarar).

**Aktif proje listesi** (rotasyona dahil — `Projeler/` altındaki `_` ile başlamayan dizinler, hariç tutulanlar listesi `excluded_projects` field'ında):

```yaml
excluded_projects:
  - _arsiv                      # zaten arşivde
  - Patron_Dashboard            # tek seferlik HTML üretici, kalite işine değmez
  - youtube-content-engine      # ham repo, henüz Antigravity standartlarına alınmadı
```

Diğer her şey rotasyona dahildir. Liste `git ls-tree --name-only HEAD Projeler/` ile dinamik okunur — yeni proje eklendiğinde otomatik rotasyona girer.

## Log formatı

Her routine işini bitirince `logs/<routine>_<YYYY-MM-DD>.json` dosyasına şu formatta yazar:

```json
{
  "routine": "bug_hunt",
  "date": "2026-05-14",
  "project": "eCom_Reklam_Otomasyonu",
  "started_at": "2026-05-14T02:00:00+03:00",
  "finished_at": "2026-05-14T02:34:12+03:00",
  "actions": [
    {
      "type": "commit",
      "sha": "abc1234",
      "message": "fix(ecom): otonom-kalite — race condition in publish lock",
      "files_changed": ["Projeler/eCom_Reklam_Otomasyonu/publish.py"],
      "risk": "low"
    },
    {
      "type": "pr",
      "url": "https://github.com/.../pull/42",
      "title": "refactor(ecom): unify config loader",
      "branch": "autonomous/bug-hunt/2026-05-14-ecom",
      "risk": "medium",
      "needs_human": true,
      "reason": "Davranış değişebilir — config kaynağı sırası değiştirildi"
    }
  ],
  "skipped": [],
  "errors": [],
  "duration_min": 34
}
```

`weekly_brief` bu JSON'ları okur, tek mail'e topartlar.

## Risk sınıflandırması (commit vs PR kararı)

Her playbook bir değişiklik yaparken `risk` etiketi atar:

- **low** → direkt commit + push, `main` branch'e
  - Typo, format, lint, deprecated API → modern karşılığı (no behavior change), dead branch/import temizliği, hardcoded değer → env var taşıması (test edilmiş), eksik docstring/comment ekleme, test yazımı (yeni test ekleme, mevcut testi değiştirmeme), RUNBOOK.md / README.md ekleme
- **medium / high** → PR aç, `main`'e merge etme
  - Davranış değişebilen fix (race condition, retry/timeout, error handling değişikliği), refactor (fonksiyon/dosya bölme/birleştirme), dependency major bump, API endpoint/contract değişikliği, schema migration, env var rename/delete

Karar verirken playbook şu testleri uygular:
1. Bu değişikliği geri almak için tek `git revert` yeterli mi? (Hayır → high risk)
2. Bu değişiklik production'da gözlenebilir davranışı değiştirir mi? (Evet → medium veya high)
3. Bu değişiklik dış tüketiciye (kullanıcı, API client, webhook) sızar mı? (Evet → high)

## Self-validation zorunluluğu

Her commit veya PR'dan önce playbook şunları yapmak ZORUNDA:

1. Değiştirilen dosya **gerçekten compile ediyor mu** — Python: `python -m py_compile <file>` / Node: `node --check <file>`
2. Mevcut testler varsa **çalıştır**, hepsi geçiyor mu — `pytest` veya `npm test`
3. **Yeni test** yazıldıysa, en az 1 kez başarılı çalıştığı doğrulansın
4. Eğer commit `requirements.txt` veya `package.json` değiştiriyorsa, dependency install dene (`pip install -r requirements.txt --dry-run` veya `npm ci --dry-run`)

Doğrulama başarısız olursa: değişikliği iptal et, `logs/.../errors` field'ına yaz, brief'te raporla.

## Çakışma kuralları

İki routine aynı projede aynı gün çalışabilir. Çakışma riskini şu kurallarla yönet:

- Her routine kendi branch'inde çalışır: `autonomous/<routine>/<tarih>-<proje>`
- `main`'e commit eden routine'ler her zaman önce `git pull --rebase` yapar
- Aynı dosyayı iki routine aynı gün değiştirmek isterse, sonraki routine **skip** eder ve `logs/.../skipped`'a kaydeder

## Repo'da kalıcı state yok

Playbook'lar kendi state'lerini `logs/` JSON'larından ve git history'sinden okur. Hiçbir routine "şu proje son ne zaman tarandı"yı state dosyasında tutmaz — log dosyalarının tarihinden anlaşılır.

## Güncelleme süreci

Bu klasördeki dosyaları değiştirmek yeterli — bir sonraki çalıştırmada routine en güncel hali okur.

Üretildi: 2026-05-13
Yazar: Claude (Mimar Modu, kullanıcı onayı: 2026-05-13)
