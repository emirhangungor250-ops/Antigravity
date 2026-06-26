# Paylaşım Notu — Sosyal Video ManyChat Yazıcı

**Mod:** C (şablona çevrildi)

## Ne yapıldı

- **Temizlenen sırlar:** Kodda gömülü gerçek API anahtarı / token yoktu. `.env.example`'daki tüm
  değerler açık `<...>` placeholder'a çevrildi (`ANTHROPIC_API_KEY`, `NOTION_SOCIAL_TOKEN`,
  `NOTION_DB_REELS_KAPAK`). Gizli dosyalar (`.env`, `HANDOVER.md`, `FEEDBACK_RAW.md`,
  `_brief_cache.json`, `__pycache__`) kopyaya hiç alınmadı.
- **Scrub edilen kişisel veriler:**
  - Sahibin adı tüm dosyalardan kaldırıldı (docstring, sistem prompt'ları,
    `agents/learnings.md`, README, RUNBOOK) → "kullanıcı" / jenerik anlatım.
  - Sahibe özel prod DB adı + kardeş-proje (otonom kapak) referansları kaldırıldı.
  - Sahibe özel marka-tanıtım engel listesi (sahibin topluluk/kurs adları) `core/sanitize.py`'dan
    boşaltıldı; yerine jenerik örnek placeholder (`topluluğum,kursum,eğitimim`) +
    `BRAND_PROMO_PHRASES` env override'ı kondu.
  - Sahibin üyelik platformuna ait yasak-domain'i ve LLM şema regex'indeki o domain engeli
    kaldırıldı; yasak domain artık `BANNED_DOMAINS` env'inden gelir (varsayılan boş).
  - Sahibe özel örnek kupon kodu → jenerik "INDIRIM26"; marka-örnekli kupon ifadesi → jenerik
    "bir markanın indirim kodu".
  - Sahibin Notion şeması (hedef ikon sınıfları + statü adları) hardcoded sabit iken artık
    `NOTION_TARGET_ICONS` / `NOTION_TARGET_STATUSES` env'leriyle override edilebilir; mevcut
    değerler "örnek varsayılan" olarak yorumlandı.
  - Maliyet/operasyon notları (1,8M token Opus yakımı, Railway servis silinme tarihleri,
    cloud routine kayıt id'leri, `routines.json` referansı) tüm dokümandan çıkarıldı.
  - `FALLBACK_MODEL` `claude-opus-4-7` → `claude-haiku-4-5` (pahalı model varsayılanı kaldırıldı).
  - README + RUNBOOK baştan jenerik yazıldı (sahibe özel deploy hikayesi, tarih, marka çıkarıldı).
  - Mutlak yol yok; örnek komut yolları sahibin repo yolundan → proje klasörü göreli hale getirildi.

## Öğrenci ne yapmalı

1. `.env.example`'ı `.env` olarak kopyala ve doldur:
   - `NOTION_SOCIAL_TOKEN` — Notion entegrasyon token'ın (https://www.notion.so/my-integrations).
   - `NOTION_DB_REELS_KAPAK` — video kartlarını tuttuğun Notion DB'sinin id'si.
   - (Manuel yedek hat için) `ANTHROPIC_API_KEY` — sadece `main.py` kullanacaksan.
2. **`NOTION_TARGET_ICONS` / `NOTION_TARGET_STATUSES`** — kendi Notion şemana göre hangi sayfa
   ikonlarının ve hangi statülerin işleneceğini yaz (virgülle ayır). Boş bırakırsan örnek
   varsayılanlar geçerli.
3. **`agents/learnings.md`** — üreteceğin DM akışının TARZINI burası belirler. Açılış tonu, buton
   sayısı, yasak ifadeler, emoji tercihi: kendi markanın diline göre düzenle.
4. İstemediğin doğrudan tanıtım kelimelerini `BRAND_PROMO_PHRASES`, link'te yasak domain'lerini
   `BANNED_DOMAINS` env'ine yaz (ya da `core/sanitize.py` içindeki listeleri elle düzenle).
5. Notion ikon adlandırman bu örnekten farklıysa `core/notion_service.py` içindeki `classify_icon`
   eşlemesini kendi ikon adlarına göre uyarla.

## Orijinal amaç → yeni jenerik çerçeve

- **Orijinal:** Sahibin sosyal videolarına, kendi Notion video prod DB'sini izleyerek, kendi tarz
  feedback'inden damıtılmış kurallarla ManyChat DM akışı yazan kişisel bot. Sahibin topluluk markası
  koda gömülü engel listesi olarak duruyordu; hedef ikon/statü şeması ve operasyon notları sahibin
  ortamına özeldi.
- **Yeni:** Herhangi bir sosyal video üreticisinin (Reels / kısa video / YouTube) Notion'da tuttuğu
  video kartlarından otomatik **çok adımlı ManyChat DM akışı** üreten jenerik araç. İki aşamalı
  desen korundu: (1) script'te adı geçen araçların GERÇEK linklerini web araması ile bulma
  (halüsinasyon yok, ölü/yasak link eleme), (2) açılış teaser + butonlar + takip mesajlarından oluşan
  sohbet akışını üretip Notion'a kart kart yapıştırma (idempotent). Tarz (`agents/learnings.md`),
  hedef şema (ikon/statü) ve yasak ifade/domain listeleri tamamen kullanıcı tarafından doldurulur.
  İki çalıştırma hattı korundu: API'siz deterministik hat (`routine_io.py`) + manuel yedek API hattı
  (`main.py`).
