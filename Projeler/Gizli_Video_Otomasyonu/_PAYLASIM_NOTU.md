# Paylaşım Notu — Gizli Video Otomasyonu

**Mod:** C (şablona çevrildi)

## Ne yapıldı

- **Temizlenen sırlar:** Kodda gömülü API anahtarı veya token yoktu (tüm gizli değerler
  zaten `.env` / token JSON dosyalarındaydı, bunlar kopyalanmadı). Çalışma durumu
  (`data/processed.json`), indirilen videolar (`*.mp4`) ve `refs/` klasörü kopya dışı
  bırakıldı.
- **Scrub edilen kişisel veriler:**
  - `config.py` — sahibin YouTube kanal ID'si (`UCKL5...`) → `<YOUTUBE_CHANNEL_ID>`
    (env'den okunuyor); sahibin Notion DB ID'si (`27b9...`) → `<NOTION_DB_ID>`;
    hardcoded e-posta varsayılanları (sahibin + ekip adresleri) kaldırıldı,
    yerine env-driven `NOTIFY_EMAILS` listesi + `ADMIN_EMAIL` geldi.
  - `config.py` / `core/cover.py` / `integrations/describe_runner.py` — komşu motorların
    sahibe özel kaynak klasör adları, bu paketteki jenerik adlara çevrildi
    (`Youtube_Aciklama_Otomasyonu`, `Otonom_Kapak_Uretici`, `YouTube_Otomasyonu`) ve
    env override'ı eklendi (`ACIKLAMA_ENGINE_DIR_NAME` / `KAPAK_ENGINE_DIR_NAME` /
    `FORCESSL_PROJECT_DIR_NAME`).
  - `integrations/describe_runner.py` — sahibe özel önekli env adı ve domain referansları
    jenerik `OPENAI_API_KEY` + "ucuz/bedava OpenAI katmanı" ifadesine çevrildi; token dosya
    adı `gmail-outreach-token.json` → `google-oauth-token.json`.
  - `main.py` / `core/notion_match.py` — docstring ve log mesajlarındaki kişisel isimler
    jenerik dile çevrildi ("ekip", "yöneticiye sorulur", örnek 'Proje YT').
  - `data/glossary.json` — sahibin ~17 maddelik kişisel marka/araç sözlüğü (CreateUGC,
    Owala, Antigravity, Skool vb.) 2 nötr örnek satıra (ChatGPT, Notion) indirildi;
    "kendi terimlerini ekle" notu eklendi.
  - `.env.example` — gerçekçi görünen tüm değerler açık `<...>` placeholder'a çevrildi;
    yeni env değişkenleri (kanal ID, NOTIFY_EMAILS, ADMIN_EMAIL, motor klasör adları)
    eklendi.
  - `README.md` baştan yazıldı (jenerik amaç + "bu desen şuna yarar" + komşu motorlara
    bağımlılık jenerik anlatıldı, mutlak yol yok).
- **Mutlak yol kontrolü:** `Desktop/Antigravity` araması 0 sonuç. Tüm yollar `__file__`'a
  göre dinamik (`_find_repo_root` paket kökünü kendisi bulur).

## Öğrenci ne yapmalı

1. `.env.example`'ı `.env` olarak kopyala ve doldur:
   - `YOUTUBE_FORCESSL_TOKEN_JSON` — gizli video listeleme + altyazı (youtube.force-ssl).
   - `GOOGLE_OUTREACH_TOKEN_JSON` — Drive yazma + mail (drive.file + gmail.send).
   - `YOUTUBE_CHANNEL_ID` — kendi kanalın.
   - `NOTION_SOCIAL_TOKEN` + `NOTION_DB_REELS_YT` — video planı/script veritabanın.
   - `OPENAI_API_KEY` — açıklama motoru için ucuz/bedava katman.
   - `NOTIFY_EMAILS` + `ADMIN_EMAIL` — haber/soru alıcıları.
2. **Komşu motorları kur:** `Youtube_Aciklama_Otomasyonu` ve `Otonom_Kapak_Uretici`
   projeleri bu pakette kurulu olmalı. Klasör adlarını değiştirdiysen `.env`'de
   `ACIKLAMA_ENGINE_DIR_NAME` / `KAPAK_ENGINE_DIR_NAME` ile bildir.
3. **`data/glossary.json`** — ASR'nin yanlış duyduğu kendi marka/terimlerini ekle
   (örnek 2 satır şablon olarak duruyor).
4. **`core/notion_match.py`** — Notion property adların farklıysa (`Name`, `Drive`,
   `Status`) ve gövde başlık satırı (`BAŞLIK:`) kendi şemana göre güncelle (dosyada
   TODO notu var).
5. Önce kuru çalış: `python main.py` (mail/Drive/kapak yok). Doğru çalışınca
   `python main.py --live`.

## Orijinal amaç → yeni jenerik çerçeve

- **Orijinal:** Sahibin kendi YouTube kanalına gizli yüklediği videoları, kendi Notion
  veritabanı + kendi marka sözlüğü + kendi ekibinin mailleri + komşu
  kapak/açıklama projelerine sabit yollarla bağlı, kişisel bir köprü servis.
- **Yeni:** Herhangi bir içerik üreticisi/ajansın, bir videoyu gizli yükleyince
  kapak + açıklama + bildirim hazırlığını otomatik tetikleyen jenerik köprü motoru.
  Kanal, Notion veritabanı, alıcı adresler, marka sözlüğü ve komşu motor klasör adları
  tamamen env/config-driven. Çekirdek desen korundu: gizli video tespiti → güven eşikli
  Notion eşleştirme (belirsizse insana sor) → sahip-yetkili bedava transkript + sözlük
  düzeltme → açıklama motoru tetikle → kapak motoru tetikle → tek mail haber.
