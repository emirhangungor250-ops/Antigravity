# Proje Dashboard

Çok-projeli bir filonun **sağlık + maliyet + bekleyen iş** durumunu tek
HTML ekrandan gösteren panel.

**Bu desen şuna yarar:** Birden fazla Railway servisi, cron'u veya AI
otomasyonu çalıştıran herkes için. "Hangi servis çöktü, bu ay ne kadar
harcadım, hangi iş yarım kaldı" sorularını her sabah elle kontrol etmek
yerine, `run.py` tüm kaynakları çekip tek bir statik HTML üretir.

5 sekme:
1. **Bugün** — KPI kartları (bugün üretim, onay bekleyen, kırık servis, aylık toplam) + bugünün hareketleri + ilk 5 bekleyen iş
2. **İş Çıktıları** — Notion DB sayaçları + Railway servisleri sağlık + maliyet
3. **Para** — Sabit abonelikler + canlı API kullanımı + manuel tahmin + Railway gerçek harcama
4. **Bekleyen** — HANDOVER / FAILED deploy / deploy edilmemiş / README'de yarım iş + Notion'da Draft/Pending kayıtlar (her birine "Brief kopyala" butonu)
5. **Otomasyon** — Tüm cron'ların haftalık ritim takvimi (yeşil sağlıklı / sarı gecikmiş / kırmızı ölü). Kutuya tıklayınca ne işe yaradığı + son/sonraki koşu açılır.

## Çalıştırma

```bash
cd Projeler/Proje_Dashboard
python3 run.py
open proje-dashboard.html
```

`run.py` tüm veri kaynaklarını çekip `data/state.json` snapshot üretir, sonra `proje-dashboard.html` render eder. Repo kökünde aynı dosyaya symlink oluşturulur.

## Otomatik Çalıştırma (LaunchAgent — macOS)

Saat başı otomatik yenileme için `launchagent/com.proje-dashboard.plist`
içindeki `<PROJE_YOLU>` yer tutucularını kendi mutlak yolunla değiştir, sonra:

```bash
cp launchagent/com.proje-dashboard.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.proje-dashboard.plist
```

Loglar `data/launchagent.log` ve `data/launchagent.err`'a yazılır.

## Veri Kaynakları

| Kaynak | Tipi | Notlar |
|---|---|---|
| Railway | GraphQL | Resmi `currentUsage` + son 30 gün vCPU·sn / GB·sn servis kırılımı |
| Notion | REST API | `notion_collector.py` → `DB_SPECS`'te tanımlı her DB için sayaç |
| OpenAI | `/v1/organization/costs` | Admin key gerekli |
| Anthropic | `/v1/organizations/usage_report/messages` | Admin key gerekli |
| ElevenLabs | `/v1/user` | Tier + char usage % |
| Hunter | `/v2/account` | Plan + kredi % |
| Firecrawl | `/v1/team/credit-usage` | Kredi kalan |
| Apify | `/v2/users/me/usage/monthly` | 2 hesap destekli |
| Replicate | `/v1/account` | Sağlık check (USD ölçülemez) |
| ManyChat | `/fb/page/getInfo` | Sağlık check (USD ölçülemez) |
| Sabit abonelikler | YAML | `config/subscriptions.yaml` |
| Bekleyen iş | Lokal tarama | HANDOVER_*.md, FAILED deploy, deploy edilmemiş, README'de TODO satırı |

Bir kaynak yanıt vermezse o panel "veri yok" der, dashboard yine açılır.

## Konfigürasyon

- `config/projects.yaml` — izlenecek Railway servisleri + lokal projeler. Pakette **2 örnek satır** var, kendi servislerinle değiştir.
- `config/subscriptions.yaml` — sabit aylık abonelikler + AI usage tahminleri. Pakette **örnek satırlar** var.
- `config/ignored_signals.yaml` — "bekleyen" listesinde görmek istemediğin sinyaller.
- `collectors/notion_collector.py` — `DB_SPECS` ve `DB_METRICS` yapılarına izlemek istediğin Notion DB'leri ekle (pakette 2 örnek var).

## Token Bağlama

Token'lar `.env` dosyasından okunur. `.env.example` hangi anahtarların gerektiğini gösterir. `python3 run.py` çalıştırınca konsol çıktısında her sağlayıcı için "✓" görmelisin.

## Yeni Proje Eklendiğinde

- Railway'e bağlı proje: `config/projects.yaml` `projects:` listesine satır ekle (folder + display_name + railway_service_id + railway_project_id).
- Sadece lokal proje: `local_projects:` listesine ekle.
- Notion DB sayacı: `notion_collector.py` `DB_SPECS` listesine satır + `.env`'e DB ID + `DB_METRICS`'e metrik tanımı.

## Sorun Giderme

| Belirti | Bakılacak yer |
|---|---|
| Notion DB "ok=False" | `.env`'de DB ID var mı + token doğru DB'ye yetkilendirilmiş mi |
| Railway "current=0" | RAILWAY_TOKEN expire olmuş olabilir, Account → Tokens'tan yenile |
| Saat başı otomatik çalışmıyor | `launchctl list \| grep proje-dashboard` ve `data/launchagent.err` |
