# RUNBOOK — Sosyal Video ManyChat Yazıcı

## Ne yapar

Notion video DB'sini izler. İkonu hedef sınıfta (varsayılan **reels** / **ai-factory**) ve statüsü
olgunlaşmış (Çekime Hazır / Çekildi / Draft Onayı Bekliyor) videolara çok adımlı ManyChat DM
akışını yazar. Akış: web araması ile gerçek linkler bulunur, sohbet akışı yazılır, Notion sayfasına
kart kart panel eklenir. İdempotent: paneli olan video atlanır.

## Çalıştırma hatları

İki hat var, ikisini de kendin tetikleyebilirsin:

1. **Deterministik hat (API'siz, maliyetsiz):** `routine_io.py`. Notion okuma/yazma + temizliği
   yapar, Anthropic API'ye dokunmaz. Yaratıcı işi (web araması + akış metni) dışarıdan gelir
   (örn. bir Claude Code cloud routine'inin kendi modeli). Akış:
   - `python routine_io.py targets` → hedef videoları JSON listeler.
   - Model bu listeden her video için akış üretir (web araması + `agents/learnings.md` tarzı).
   - `python routine_io.py write <page_id> < flow.json` → akışı temizler, doğrular, Notion'a yazar.
2. **Manuel yedek hat (API harcar):** `python main.py`. `core/llm.py` üzerinden Anthropic API ile
   uçtan uca üretir. `DRY_RUN=1 python main.py` Notion'a yazmadan konsola basar (kuru test).

## Deploy (opsiyonel)

- **En ucuz:** API'siz cloud routine + `routine_io.py`. Routine periyodik tetiklenir, repoyu çeker,
  yukarıdaki iki adımı koşar. Maliyeti sıfırdır (model aboneliğin üzerinden çalışır).
- **Railway cron:** `railway.json` hazır şablondur. CRON kullan (iş bitince süreç çıkar; içinde
  `while True`/scheduler yok). Railway servis ayarında `rootDirectory` bu projeyi göstermeli; boş
  bırakılırsa servis sessizce FAILED olur.
- Kod değişikliği yayını: cloud routine her koşumda repoyu taze çeker, redeploy gerekmez; Railway'de
  watchPattern açıksa `git push` otomatik deploy eder.

## Env değişkenleri

- `NOTION_SOCIAL_TOKEN` (zorunlu): Notion erişimi. Yedek isimler: `NOTION_REELS_TOKEN`, `NOTION_TOKEN`.
- `NOTION_DB_REELS_KAPAK` (zorunlu): hedef DB id. Yedek isimler: `NOTION_DB_REELS`, `NOTION_DB_ID`.
- `NOTION_TARGET_ICONS` / `NOTION_TARGET_STATUSES` (opsiyonel): kendi şemana göre hedef ikon/statü
  listesi (virgülle ayır). Boşsa varsayılanlar geçerli.
- `MAX_VIDEOS_PER_RUN` (default 5) · `MIN_SCRIPT_CHARS` (default 150) · `DRY_RUN`.
- Sadece manuel yedek hattı için: `ANTHROPIC_API_KEY` + `MANYCHAT_MODEL` (default ucuz/küçük model).

## Sorun giderme

- **Koştu ama yeni panel yok:** Çoğu zaman normaldir. Hedef video kalmamıştır (ikon/statü kapısı),
  panel zaten vardır (idempotent) veya script çok kısadır. Log'daki "atla" satırlarına bak.
- **Notion'a bağlanamadı:** `routine_io.py` env eksikliğinde "HATA: env eksik" basar — token/DB id
  ayarını kontrol et. Notion entegrasyonunun DB'ye erişim izni olduğundan emin ol.
- **Tek video sürekli işlenemiyor:** Hatalar video başına izoledir. İlgili Notion sayfasını aç:
  script bloğu bozuk olabilir.
- **Akışta yanlış link / istenmeyen tanıtım sızdı:** `routine_io.py write` temizlik uyarısı basar.
  Düzeltme: `agents/learnings.md`'ye kural ekle, paneli sildirip yeniden ürettir.

## Loglar nerede

Gerçek doğrulama Notion'dur: hedef video sayfasında "📨 ManyChat akışı" paneli oluştu mu bak.
Lokal koşumda her şey konsola yazılır, dosya log'u yoktur. Cloud routine kullanıyorsan koşum
log'unu routine yönetim panelinden görürsün.
