# Cost Optimization — Otonom Railway + Dış Servis Maliyet Optimizasyonu

**Çalışma sıklığı:** Çarşamba UTC 04:00 (İstanbul 07:00)
**Hedef süre:** ≤ 30 dakika
**Çıktı:** Rapor (her zaman) + opsiyonel low-risk commit (worker→cron geçişleri için sadece PR)

## Amaç

Antigravity Railway hesabı her ay ne kadar harcıyor, nereye gidiyor? Bu routine haftalık tarar:
- Worker olarak çalışıyor ama günde 1-2 kez tetiklenen servisler → cron'a çevirme önerisi (PR)
- Atıl servisler (son 7 gün hiç log yok) → kapatma önerisi (sadece rapor, otomatik kapatma yok)
- Pahalı dış servis kullanımı (Kie AI, Apify, Anthropic API) → kullanım trend raporu

## Adım adım

### 1) Repo'yu çek + skill'i yükle

```
git clone <GITHUB_REPO_URL> /tmp/antigravity
cd /tmp/antigravity
git checkout main
git pull --rebase origin main
```

`railway-maliyet` skill'i (`_skills/railway-maliyet/`) maliyet hesabının kuralları için referanstır. Onu oku.

### 2) Railway token'ı yükle

```bash
source _knowledge/credentials/master.env
# RAILWAY_TOKEN değişkeni şimdi yüklü
```

Memory'deki kurallar:
- GraphQL endpoint: `https://backboard.railway.com/graphql/v2` (NOT `.app` — `.app` 401 verir)
- `railway up` yok; deploy için `serviceInstanceDeployV2`

### 3) Tüm servisleri listele

```graphql
query {
  me {
    projects {
      edges {
        node {
          id
          name
          services {
            edges {
              node {
                id
                name
                cronSchedule
                deployments(first: 5) {
                  edges { node { status updatedAt } }
                }
              }
            }
          }
        }
      }
    }
  }
}
```

### 4) Her servis için tarama

**A. Worker mi, gerçekten worker'a ihtiyacı var mı?**

`cronSchedule` null ve `startCommand` "while true" / event loop içermiyorsa, muhtemelen cron olarak çalışmalı.

Memory: `feedback_railway_cost_optimization.md` — Railway saniye-bazlı; idle worker bile fatura keser.

Eğer worker:
- Son 24 saatte log'da kaç kez "iş yaptı" olduğunu say (`requestLogs` query)
- Günde < 24 iş yapıyorsa → cron'a geçiş önerisi
- Günde > 100 iş yapıyorsa → worker doğru

**B. Atıl servis (son 7 gün hiç log yok)**

`deploymentLogs(deploymentId: ...)` son 7 günü tara. Hiç stdout/stderr yoksa atıl. Rapor'a ekle, kullanıcı karar versin.

**C. Cron schedule analizi**

Cron schedule çok mu sık (`* * * * *` = her dakika)? Memory: minimum 5 dk önerilir. Gereksiz sıklık varsa rapor.

### 5) Dış servis kullanımı (opsiyonel — eğer 10 dk içinde yapılabiliyorsa)

Şu servislere uğra ve son 7 günü topla:

- **Kie AI:** API çağrısı sayısı + harcanan USD (`/api/v1/transactions` benzeri endpoint varsa)
- **Apify:** Apify console API ile `actor-runs` listele, compute units topla
- **Anthropic API:** Kullanım sayfası API'si yoksa skip; varsa son 7 gün topla
- **OpenAI:** Aynı

Bu kısım best-effort; servis API key yoksa veya endpoint çekmiyorsa **skip** ve rapor'da `"<servis>: skip — token yok / endpoint yanıtlamadı"` yaz.

### 6) Worker→Cron geçişi (PR olarak)

Eğer aday bulduysan:

```bash
git checkout -b autonomous/cost-opt/$(date +%F)-<servis>
# railway.json'da startCommand'i kaldır, cronSchedule ekle
# kod tarafında while-true loop'unu tek-shot moduna çevir
git add Projeler/<proje>/railway.json Projeler/<proje>/<entry>
git commit -m "perf(<proje>): cost-opt — worker→cron geçişi

Sebep: son 7 gün <X> iş, worker idle %<Y>
Tasarruf: tahmini ~$<Z>/ay
Risk: medium (davranış değişikliği — schedule trigger zamanlaması)

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
git push -u origin autonomous/cost-opt/$(date +%F)-<servis>
gh pr create --title "perf(<proje>): worker→cron geçişi (tasarruf ~\$<Z>/ay)" --body "..."
```

Worker→cron geçişi ASLA direkt main'e commit edilmez — schedule timing davranış değişikliğidir.

### 7) Atıl servis önerisi (sadece rapor)

```json
"recommendations": [
  {
    "type": "shutdown_candidate",
    "service": "<servis adı>",
    "evidence": "Son 7 gün hiç log yok, son successful deploy 45 gün önce",
    "estimated_savings_usd_month": null,
    "action_needed_from_human": "Bu servis hâlâ gerekli mi? Değilse Railway'den sil."
  }
]
```

**Otomatik servis silme YASAK** — kullanıcı onayı şart.

### 8) Log + rapor yaz

`logs/cost_optimization_<YYYY-MM-DD>.json`:

```json
{
  "routine": "cost_optimization",
  "date": "<YYYY-MM-DD>",
  "railway": {
    "total_services": 23,
    "active_last_7d": 19,
    "idle": 4,
    "workers_idle_pct_high": [
      {"name": "twitter-video-cron", "idle_pct": 96, "recommendation": "kalsın — sıklık gerekli"}
    ],
    "estimated_monthly_usd": 14.30,
    "trend_vs_last_week_pct": -3
  },
  "external_services": {
    "kie_ai": {"7d_usd": 4.20, "status": "ok"},
    "apify": "skip — token yok"
  },
  "actions": [
    {"type": "pr", "url": "https://github.com/.../pull/N"}
  ],
  "recommendations": [...],
  "duration_min": 24
}
```

```bash
git add _knowledge/autonomous_quality/logs/cost_optimization_$(date +%F).json
git commit -m "chore(autonomous): cost_optimization log — $(date +%F)"
git push origin main
```

### 9) Yapma

- **Asla** servis sil — sadece rapor
- **Asla** kullanıcı onayı olmadan plan değiştir (Hobby → Pro vs.)
- **Asla** "tasarruf için cache'i kapat" gibi davranış değişikliği öner — kullanıcı tarafı
- **Asla** dış servis API key'ini log'a yaz

## Output kontrol

Rapor her zaman üretilir (atıl servis bulunmasa bile). PR opsiyonel — geçiş adayı yoksa sıfır PR çıkabilir.
