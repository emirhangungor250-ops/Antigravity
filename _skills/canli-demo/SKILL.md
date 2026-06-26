---
name: canli-demo
description: |
  Bir projeyi lokalde başlatıp paylaşılabilir canlı demo URL'i üretir.
  Kullanıcı ya kendisi kontrol için ya da müşteriye/öğrenciye
  link olarak paylaşmak için tetikler.

  Tetikleyici cümleler (Türkçe):
  - "X projesinin demosunu başlat"
  - "X için canlı demo aç"
  - "müşteriye göstereceğim, demoyu hazırla"
  - "Skool öğrencisine demo linki yolla"

  Skill, Railway production servisini (varsa) geçici stop eder, lokal'de
  proje main.py'sini DASHBOARD_ENABLED=1 ile başlatır, cloudflared quick
  tunnel ile paylaşılabilir URL üretir, Ctrl+C sonrası Railway servisini
  geri açar.

  ⚠️ Bu skill **chat'ten Claude tetikler**. Kullanıcıya "şu komutu yapıştır"
  DEMEZSİN; sen `python _skills/canli-demo/start.py <proje>` çağırırsın.
---

# Canlı Demo Skill'i

## Ne işe yarar

Antigravity'deki interaktif projelerin (Telegram bot, WhatsApp asistan, vb.)
pipeline'ını canlı izlenebilir bir dashboard üzerinden gösterir. Sahnelerin
ne kadar sürdüğü, hangi adımda olduğu, alt-akışların durumu hepsi tarayıcıdan
canlı görünür. Eski statik `Sistem_Nasil_Calisir.html` sisteminin yerini aldı.

## Mimari

```
_skills/canli-demo/
├── SKILL.md
├── start.py                     # chat-trigger: Railway stop → tunnel → main.py
├── sync.py                      # template'i projeye kopyala
├── mock.py                      # gerçek API'siz dashboard test runner
├── resources/
│   └── tunnel.py                # cloudflared quick tunnel sarmalayıcı
└── template/
    ├── core/run_state.py        # generic RunStateEmitter (event_log + replay)
    ├── dashboard_server.py      # FastAPI + SSE + Last-Event-ID reconnect
    ├── dashboard/
    │   ├── index.html           # title app.js'den dinamik
    │   ├── app.js               # idempotent events, reconnect banner
    │   ├── style.css            # --stage-count CSS var ile dinamik grid
    │   └── payloads.example.js  # proje-spesifik render örnek
    └── stages_example.py        # her proje kendi stages.py'sini yazar
```

Railway rootDirectory kısıtı: paket lokalde tüm projelere `sync.py` ile
kopyalanır (Railway'in göremeyeceği `_skills/` altından import yapılamaz).

## Bir projeye demo entegrasyonu

```bash
# 1. Şablonu projeye kopyala
python _skills/canli-demo/sync.py Projeler/<isim>

# 2. <proje>/stages.py'yi düzenle — projeye özgün 4-8 stage tanımla:
#    META: dashboard başlığı + alt başlık
#    STAGES: pipeline akışı (her stage emitter.start_stage(id) ile başlar)

# 3. <proje>/main.py'a emitter event'lerini yerleştir:
#    from core.run_state import emitter
#    ...
#    emitter.start_run(input_label="Kullanıcı X'in talebi")
#    emitter.start_stage("stage1", sub_text="Veri çekiliyor…")
#    emitter.update_stage("stage1", progress=0.5)
#    emitter.end_stage("stage1", payload={"sonuc": "...", "url": "..."})
#    ...
#    emitter.end_run(final_payload={"final_url": "..."})

# 4. main.py içine dashboard server'ı arka plan task'ı olarak ekle:
#    if os.getenv("DASHBOARD_ENABLED") == "1":
#        from dashboard_server import start_dashboard
#        asyncio.create_task(start_dashboard())

# 5. Test (gerçek API çağırmadan):
python _skills/canli-demo/mock.py Projeler/<isim>

# 6. Canlı:
python _skills/canli-demo/start.py Projeler/<isim>
```

## Proje-spesifik payload rendering (opsiyonel)

Stage end'inde `emitter.end_stage(stage_id, payload={"key": "value"})` gönderirsen
generic key/value tablosu olarak gösterilir. Proje-özel render istersen
`<proje>/dashboard/payloads.js` oluştur ve `window.PROJECT_PAYLOAD_RENDERERS`'a
stage_id → fonksiyon eşlemesi koy. Örnek için `template/dashboard/payloads.example.js`'e bak.

`sync.py` `payloads.js`'i overwrite ETMEZ — yazdığın render mantığı korunur.

## start.py akışı

1. Proje klasöründe `stages.py`, `core/run_state.py`, `dashboard/index.html`
   var mı kontrol → yoksa kullanıcıya `sync.py` öner ve dur
2. `cloudflared` kurulu mu — yoksa `bash _skills/canli-demo/install.sh` ile paket-içi bin/'e kurar ve durur
3. `_knowledge/credentials/master.env`'den `RAILWAY_TOKEN` oku
4. Railway GraphQL ile proje folder adına en yakın servisi bul
5. Servis polling tabanlı mı (`run_polling` / `start_polling` pattern'i) →
   ise replicas=0 ile stop (collision önlenir). Webhook/cron tabanlı → stop etme
6. Boş port bul (rastgele, 8000+)
7. `cloudflared tunnel --url http://localhost:<port>` background → URL parse
8. `DASHBOARD_ENABLED=1 DASHBOARD_PORT=<port> python main.py` (cwd = proje, .env merge)
9. Public URL'i ekrana yaz: `🎬 Demo aktif: https://<random>.trycloudflare.com`
10. Ctrl+C → main.py terminate → cloudflared terminate → Railway replicas=1

## Flag'ler

- `--no-tunnel` — sadece lokal (paylaşılabilir URL üretme)
- `--skip-railway` — Railway stop/start atlama (cron projeler için)

## Hangi projelere demo eklenmeli

**Yüksek değer (interaktif, müşteri/öğrenci tanıtımı için güçlü):**
- Çok adımlı otomasyon projeleri (örn. reklam üretimi, onboarding akışları)
- WhatsApp/Telegram asistan botları
- Lead bildirim botları, dashboard projeleri, mail otomasyonları

**Orta değer (görsel/video pipeline'ı izlemesi anlamlı):**
- Görsel/video üretim pipeline'ı olan projeler
- Carousel / sosyal medya içerik üreten cron'lar

**Demo gereksiz (saf monitor/rapor cron):**
- Sadece izleme/raporlama yapan, kullanıcı etkileşimi olmayan cron'lar

## Sorun giderme

- **cloudflared bulunamadı:** `bash _skills/canli-demo/install.sh` (brew gerektirmez, GitHub release'ten binary çeker)
- **Railway servisi bulunamadı / 403:** `--skip-railway` ile çalıştır; polling tabanlı projelerde collision uyarısı görülürse Railway servisini manuel stop et
- **Polling collision:** start.py polling tespiti yapıp Railway servisini stop eder; --skip-railway ile manuel akış
- **SSE bağlantı kopuyor:** Client otomatik reconnect (3s) + Last-Event-ID replay → buffered event'ler kaçırılmadan ulaşır
- **Tunnel URL 60s'den geç geliyor:** start.py 60s timeout ile bekler; daha uzun sürerse Cloudflare API gecikmesi, tekrar dene
- **QR kod görünmüyor:** DASHBOARD_PUBLIC_URL boşsa /qr.svg 404; tunnel açıkken tunnel URL otomatik geçer

## Flag'ler

- `--mock` — main.py yerine sahte event üreticisi (müşteri tanıtımında pipeline tetiklemeden kullan)
- `--no-tunnel` — sadece lokal http://localhost:PORT (paylaşılmaz)
- `--skip-railway` — Railway stop/start atla (cron veya webhook projelerinde)
