# Paylaşım Notu — YouTube Yorum Otomasyonu

**Mod:** C (şablona çevrildi)

## Ne yapıldı

- **Temizlenen sırlar:**
  - Kaynakta gerçek bir OAuth token dosyası vardı (`youtube_forcessl_token.json` — canlı refresh_token + client_secret). Allowlist kopyalamaya HİÇ alınmadı (pakette yok), `.gitignore`'da zaten dışlıydı.
  - `.env`, token/credential dosyaları kopyalanmadı; pakette yalnız `.env.example` var, tüm değerler boş/`<PLACEHOLDER>`.
- **Scrub edilen kişisel veriler:**
  - Kanal sahibinin gerçek ad-soyadı tüm prompt/docstring/yorumlardan kaldırıldı; LLM artık `YT_CREATOR_NAME` + `YT_CREATOR_BIO` env'inden gelen jenerik kimlikle çalışıyor (`core/llm.py` WORTH_SYSTEM, `core/reply_writer.py` REPLY_SYSTEM artık f-string ile env okuyor).
  - Hardcoded YouTube kanal ID'si → `YOUTUBE_CHANNEL_ID` env (artık zorunlu; default yok). `config.py`, `.env.example`, README, RUNBOOK temizlendi.
  - Kişisel e-posta ve domain → `YT_REPORT_TO` / `YT_REPORT_FROM` / `YT_REPORT_REPLY_TO` env, default'lar boşaltıldı. `core/llm.py` içindeki kişisel domain'li `HTTP-Referer` başlığı kaldırıldı.
  - Sahibin Supabase proje referansı `db/schema.sql`, README, RUNBOOK, `.env.example` yorumlarından kaldırıldı.
  - Sahibin deploy platformuna ait servis/proje ID'si ve dahili proje adı RUNBOOK'tan çıkarıldı.
  - Sahibin mono-repo marka ibaresi mail footer'ından ve docstring'lerden temizlendi ("YouTube Yorum Otomasyonu" oldu).
  - README **baştan yazıldı** (jenerik amaç + "bu desen şuna yarar" çerçevesi). RUNBOOK platform-bağımsız hale getirildi (Railway'e özel ID/proje detayları çıkarıldı).
  - Klasör adı zaten jenerik: `YouTube_Yorum_Otomasyonu`.

## Öğrenci ne yapmalı

1. `.env.example`'ı `.env` olarak kopyala. Faz 1 için zorunlu doldur:
   `YOUTUBE_CHANNEL_ID`, `YOUTUBE_API_KEY`, `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`,
   `VOYAGE_API_KEY`, `RESEND_API_KEY`, `OPENAI_API_KEY`.
2. **`YT_CREATOR_NAME` + `YT_CREATOR_BIO`** — AI'nın hangi kimlikle yorum sınıflayıp cevap
   yazacağı. Kendi adın + tek satır kanal tanımın. Bu, üretilen cevapların sesini belirler.
3. **`YT_REPORT_TO` / `YT_REPORT_FROM`** — raporun nereye, hangi (doğrulanmış) adresten gideceği.
4. `db/schema.sql`'i kendi Supabase projende (SQL Editor) çalıştır.
5. Faz 2 isteğe bağlı: `YOUTUBE_CLIENT_ID/SECRET` ekle, `python setup_youtube_forcessl.py` ile
   bir kez OAuth onayı ver (kendi YouTube hesabınla), çıkan token'ı `YOUTUBE_FORCESSL_TOKEN_JSON`'a koy.
   Kopyala butonu için eşlik eden **YouTube_Kopya_Sayfa** projesini deploy edip `YT_COPY_PAGE_URL`'i ver.

Not: Bu projede kanal sahibinin gerçek cevapları AYRI bir "corpus" tablosunda **çalışırken
otomatik birikir** (Faz 1 sırasında kanalın kendi cevaplarından öğrenir). Pakette sahibin
hiçbir gerçek cevabı/öğrenme verisi yoktur — sistem senin kanalında sıfırdan öğrenir.

## Orijinal amaç → yeni jenerik çerçeve

- **Orijinal:** Tek bir içerik üreticinin kendi YouTube kanalının yorumlarını tarayan,
  o kişinin adı + biyografisi + kanal ID'si + e-postası prompt ve config'e gömülü olan
  kişisel yorum-yanıt asistanı.
- **Yeni:** Herhangi bir YouTube kanalı için, kimin sesi/hangi kanal/hangi mail tamamen
  env'den gelen jenerik bir yorum tarama + akıllı sıralama + (opsiyonel) AI taslak motoru.
  İki fazlı desen (Faz 1 rapor+öğrenme, Faz 2 few-shot taslak + tek-tık onay), LLM ile
  "cevaplanmaya değerlik" sınıflaması ve pgvector ile kendi sesini öğrenme yapısı korundu.
