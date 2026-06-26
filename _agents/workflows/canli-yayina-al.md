---
description: Projeyi GitHub'a push et ve Railway'de 7/24 çalışır hale getir — tamamen otonom
---

# /canli-yayina-al — Production Deploy

> ⛔ Kullanıcıya "dashboard'a git", "tıkla", "repo bağla" ASLA deme. Her şey API ile.

## Çağırılacak Skill'ler

Bu workflow'u tetiklediğinde **önce** şu skill'leri yükle (Skill tool):
- `canli-yayina-al` — full deploy akışı (GitHub MCP push + Railway GraphQL).
- `use-railway` — Railway operasyonları (proje/servis/env oluşturma).
- Projede entegrasyon varsa: `supabase`, `notion-api-rules`, `apify-scraping-rules`, `telegram-bot-rules`.

`_knowledge/deploy-registry.md`'yi oku — proje daha önce deploy edildi mi belirle:
- Hiç yoksa → **YENİ** deploy.
- GitHub var, Railway yok → **KISMI** (Railway projesi oluştur, bağla).
- İkisi de varsa → **RE-DEPLOY** (push + redeploy).

## Adım 0 — Pre-Push Sağlık Kontrolü (ZORUNLU, ATLAMA)

Push'tan ÖNCE bu kontroller. Biri kırılırsa **push yapma, düzelt**.

| Kontrol | Komut / Bakış |
|---|---|
| Python syntax | `python3 -m py_compile *.py` |
| Import zinciri | Tüm `.py` dosyalarını `importlib.import_module` ile dene |
| Mevcut testler | `pytest tests/` veya `python3 run_test.py` varsa çalıştır |
| Dependency name mismatch | `google.genai` → `google-genai`, `PIL` → `Pillow`, `telegram` → `python-telegram-bot` |
| Version pinning | `requirements.txt` içinde `==` olmayan kritik paket var mı? |
| Hardcoded secret | `grep -E "(sk-\|AIza\|ghp_\|Bearer )"` — bulursa env'e taşı |
| Sistem bağımlılığı (ffmpeg / cairo / chromium) | `Aptfile`/`apt.txt` varsa SİL (Nixpacks yoksayar). `nixpacks.toml` içinde `nixPkgs` doğru mu? |
| Caller ↔ Callee imza | Entry point'teki çağrı keyword'lerini fonksiyon tanımlarıyla AST üzerinden doğrula |

> Detaylı script şablonları `_skills/canli-yayina-al/SKILL.md` içinde — kopyalayıp çalıştır.

## Adım 1 — Deploy

Skill'in adımlarını harfiyen uygula:
- **Mono-repo:** Tüm kod `<GITHUB_REPO>`'de. Yeni servis için `rootDirectory` = `Projeler/<ProjeAdı>` zorunlu (boş bırakılırsa servis sessizce FAILED).
- **Push yolu:** Sandbox DNS engeli için `mcp_railway_deploy` + `mcp_github-mcp-server_push_files` kullan.
- **Yeni servis:** `serviceCreate` → `serviceInstanceUpdate` (startCommand + restartPolicy + watchPatterns) → `variableCollectionUpsert` (env'ler) → `rootDirectory` set.
- **Re-deploy:** `serviceInstanceDeployV2` (cron projelerde redeploy çalıştırmaz, gerekirse `cronSchedule` override).

## Adım 2 — Smoke Test (60 sn bekle, sonra)

`deploymentLogs` çek, son 100 satırda fatal pattern ara:
`Traceback`, `ImportError`, `ModuleNotFoundError`, `AttributeError`, `NameError`, `KeyError`, `TypeError`, `Process exited with code 1`.

Hata bulursan → "yayına aldım ama hata var, düzeltiyorum" de → fix → tekrar push.

## Adım 3 — Stabilize-Lite (5 kontrol)

1. Son deployment status `SUCCESS` mi?
2. Runtime log'da fatal pattern yok mu?
3. `.env.example` / `config.py`'daki tüm env key'ler Railway'de tanımlı mı?
4. Cron projesi ise → manuel redeploy + 90 sn + log re-check.
5. `_knowledge/platform-checklists/railway.md` ilgili bölümü hızlı tara.

## Adım 4 — Kayıt + Rapor

- `_knowledge/deploy-registry.md`'ye servisi ekle/güncelle (proje ID, servis ID, env ID, GitHub repo, rootDirectory).
- `_knowledge/bekleyen-gorevler.md`'ye 48-saat izleme entry'si ekle.
- Kullanıcıya 1-3 cümlelik rapor: ne deploy oldu, hangi servis, smoke test sonucu.

## ⚠️ Yaygın Tuzaklar

- **Watchdog auto-deploy kapalı projeler:** `twitter-video-cron`, `linkedin-video-cron` gibi `ignoreWatchPatterns=true` olan servislerde push deploy etmez — manuel `serviceInstanceDeployV2` gerekir. Detaylar `_knowledge/deploy-registry.md`'de.
- **Standalone repo dep sync:** Monorepo'dan dosya kopyalandıysa `package.json` / `requirements.txt`'i de güncelle, yoksa build crash.
- **Railway GraphQL domain:** `backboard.railway.com` (NOT `.app` — `.app` her sorguya 401 döner).
