# Paylaşım Notu — Twitter_Text_Paylasim

## Mod
B — İçerik kaynaklarını ve stil rehberlerini öğrenci koyar.

## Ne yapıldı
- **Sırlar:** Koda gömülü API anahtarı bulunmadı (tümü `.env` / env üzerinden). `.env` kopyalanmadı.
- **Kişisel veri temizliği:**
  - `core/mail_sender.py` — hardcoded kişisel e-posta adresi (gönderici + alıcı + from başlığı) kaldırıldı; `MAIL_SENDER` / `MAIL_RECIPIENT` env değişkenlerine taşındı. Marka mail footer'ı kaldırıldı.
  - `config.py` — yorumdaki kişisel sosyal medya handle örneği kaldırıldı.
  - `core/notion_scripts.py`, `core/youtube_watcher.py` — "Dolunay Reels & YouTube" DB adı ve kişisel proje yolu referansları jenerikleştirildi.
  - `core/typefully_publisher.py`, `ops_logger.py` — "Antigravity" / kişisel referanslar jenerikleştirildi.
- **İçerik / stil rehberleri şablona indirildi (davranış korundu, içerik jenerikleştirildi):**
  - `core/tweet_writer.py` — `SCORING_RUBRIC` ve hook örnekleri "Dolunay'ın hesabı", "~250K kitle", "Dolunay'ın eğitim odağı", "Antigravity ekosistemi" referanslarından arındırıldı; "kendi nişine göre uyarla" notları eklendi.
  - `core/use_case_generator.py` — `STYLE_GUIDE` (4 örnek senaryo) kişisel marka referanslarından arındırıldı, "örnek stil rehberi" olarak işaretlendi.
  - `core/linkedin_adapter.py` — `SYSTEM_PROMPT` (LinkedIn profili tanımı) jenerikleştirildi.

## Öğrenci ne yapmalı

### 1. İçerik kaynaklarını kendine bağla
- `.env`'de `YOUTUBE_CHANNEL_ID` → kendi YouTube kanalınızın UC ile başlayan ID'si.
- `NOTION_SOCIAL_TOKEN`, `NOTION_X_DB_ID`, `NOTION_DB_REELS_KAPAK` → kendi Notion workspace'inizdeki DB ID'leri.

### 2. Stil rehberlerini kendi içerik nişine göre yaz
Aşağıdaki üç dosyadaki prompt sabitleri **sizin sesinize ve nişinize göre değiştirilmelidir**:
- `core/tweet_writer.py` → `SCORING_RUBRIC` (X yazım kuralları, hook örnekleri, araç öncelikleri)
- `core/use_case_generator.py` → `STYLE_GUIDE` (içerik serisi örnekleri)
- `core/linkedin_adapter.py` → `SYSTEM_PROMPT` (LinkedIn profil tanımı)

Bunlar şu an bir AI/otomasyon eğitim hesabı için örnek olarak bırakıldı. Kendi konunuz farklıysa baştan yazın.

### 3. `.env` değişkenlerini doldur
`.env.example`'ı `.env` olarak kopyalayın. Doldurulması gerekenler: `TYPEFULLY_API_KEY`, `TYPEFULLY_SOCIAL_SET_ID`, `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `PERPLEXITY_API_KEY`, `GITHUB_TOKEN`, `KIE_API_KEY`, `NOTION_SOCIAL_TOKEN` + DB ID'leri, `YOUTUBE_CHANNEL_ID`, `MAIL_SENDER`, `MAIL_RECIPIENT`, `APPROVAL_*`.

### Not
`env_loader.py` ve `core/mail_sender.py` lokal monorepo'da `_knowledge/credentials/master.env` ve OAuth klasörünü arar; bunlar yoksa düz env değişkenlerine düşer (standalone çalışır). Sabah özet maili Gmail API kullandığından OAuth kurulumu gerektirir; mail göndermek istemiyorsanız bu adım atlanabilir.
