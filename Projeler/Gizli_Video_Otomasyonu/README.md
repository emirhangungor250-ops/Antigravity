# Gizli Video Otomasyonu

YouTube kanalına **gizli (unlisted)** olarak yüklenen yeni bir video çıktığında, onu
otomatik yakalar; kapağını ve açıklamasını üretip videonun Drive klasörüne koyar;
sonra ekibe haber verir. Artık kimsenin video linkini elden ele taşıması gerekmez —
sistem kanalı kendisi düzenli yoklar.

Bu desen şuna yarar: bir videoyu yayına almadan önce **kapak + açıklama + bildirim**
hazırlığını tek bir tetikçiye bağlamak. Çekim biter, gizli yüklersin, gerisini servis
halleder. Köprü mantığı sadece *tespit + eşleştirme + transkript + tetikleme + haber*
işini yapar; yaratıcı işi (kapak, açıklama) bu paketteki iki ayrı motora devreder.

## Bu paketteki diğer motorlarla birlikte çalışır

- **Otonom_Kapak_Uretici** — videodan kare seçip kapak görselini üretir.
- **Youtube_Aciklama_Otomasyonu** — script + gerçek transkriptten açıklama metni yazar.

Bu iki projeyi de pakette kurmuş olman gerekir. Klasör adlarını değiştirdiysen
`.env`'de `ACIKLAMA_ENGINE_DIR_NAME` / `KAPAK_ENGINE_DIR_NAME` ile bildirebilirsin.

## Çalışma Şekli

1. Belirli saatlerde kanaldaki gizli videoları sahip yetkisiyle listeler.
2. Yeni olanı Notion'daki doğru satırla eşleştirir — **sadece YouTube ikonlu** satırlar
   (Reels/diğerleri atlanır). Eşleştirme başlık + videonun gerçek konuşması ↔ Notion
   scripti örtüşmesiyle yapılır; güven eşiğinin altındaysa körlemesine yazmaz,
   yöneticiye sorar.
3. Transkripti sahip yetkisiyle ücretsiz çeker (harici scraping servisi gerekmez),
   `data/glossary.json` sözlüğüyle marka/terim yazımlarını düzeltir.
4. **Açıklama:** açıklama motoru (ucuz/bedava OpenAI katmanı) script + gerçek
   transkriptle yazar, Drive klasörüne bir Google Doc bırakır.
5. **Kapak:** video YouTube'dan indirilip Drive'a app-sahipli konur (drive.file izni
   yalnız app dosyalarını görür), sonra kapak motoru tetiklenir (kapaklar `THUMBNAIL`
   alt klasörüne yazılır).
6. Hazır olunca `NOTIFY_EMAILS`'teki adreslere tek bir haber maili gider.

## Stack

Python · YouTube Data API (force-ssl) · yt-dlp · Notion API · Google Drive/Gmail
(drive.file + gmail.send) · komşu motorlar: Youtube_Aciklama_Otomasyonu,
Otonom_Kapak_Uretici.

## Environment Setup

`.env.example`'ı `.env` olarak kopyala ve doldur. En kritik değişkenler:

- `YOUTUBE_FORCESSL_TOKEN_JSON` — gizli video listeleme + altyazı indirme (youtube.force-ssl scope).
- `GOOGLE_OUTREACH_TOKEN_JSON` — Drive yazma + mail gönderme (drive.file + gmail.send).
- `YOUTUBE_CHANNEL_ID` — senin kanalın.
- `NOTION_SOCIAL_TOKEN` + `NOTION_DB_REELS_YT` — video planı/script veritabanın.
- `OPENAI_API_KEY` — açıklama motoru için ucuz/bedava katman. Bu yoksa açıklama üretimi
  durur; pahalı modele düşmez (maliyet güvencesi).
- `NOTIFY_EMAILS` — haberin gideceği adres(ler).

> **Notion şeması:** Eşleştirme kodu `Name`, `Drive`, `Status` property'lerini ve
> sayfa gövdesinde `BAŞLIK:` satırını arar. Kendi Notion sütun adların farklıysa
> `core/notion_match.py` içindeki adları güncelle.

## Çalıştırma

- Kuru çalışma (güvenli, varsayılan): `python main.py` — mail/Drive/kapak YOK, sadece gösterir.
- Tek videoyu dene: `python main.py --video <VIDEO_ID>`
- Canlı: `python main.py --live` (veya `DRY_RUN=0`).

## Deploy (opsiyonel)

`railway.json` ile Railway cron olarak hazır (`cronSchedule: "0 6-19 * * *"`). Saatleri
kendi saat dilimine göre ayarla. Token'ları env olarak ver
(`YOUTUBE_FORCESSL_TOKEN_JSON`, `GOOGLE_OUTREACH_TOKEN_JSON`). Başka bir platforma da
deploy edebilir veya lokalde elle çalıştırabilirsin.

Not: yt-dlp en iyi formatlar için bir JS runtime (deno) ister; yoksa mevcut mp4
formatlarıyla çalışır.
