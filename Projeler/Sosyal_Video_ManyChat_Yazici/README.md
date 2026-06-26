# Sosyal Video ManyChat Yazıcı

Sosyal video üreticileri (Reels / kısa video / YouTube) için **çok adımlı ManyChat DM
akışı yazıcı**. Notion'da tuttuğun video kartlarını izler; bir video yeterince olgunlaşınca
(script kesinleşmiş, çekilmiş) o videonun yorumuna tetik kelimesi yazan izleyiciye gönderilecek
ManyChat sohbet akışını otomatik üretir ve aynı Notion sayfasına kart kart yapıştırır.

## Bu desen şuna yarar

İçerik üretiyorsan, her videonun altına "X yaz, sana göndereyim" dersin; izleyici yorumu yazınca
ManyChat ona DM atar. Bu botun çözdüğü iş: o DM'i tek tek elle yazmak yerine, videonun
script'inden **çok adımlı bir sohbet akışı** üretmek. Akış:

- **Açılış balonu** — kısa merak/değer kancası + butonlar.
- **Link butonları** — videoda adı geçen aracın/sitenin/store sayfasının GERÇEK resmi linki
  (web araması ile bulunur, halüsinasyon yok; ölü/yasak link elenir).
- **Devam butonları** — sohbeti derinleştirir (örn. "Öğren", "Örnekleri Gör").
- **Takip mesajları** — asıl değeri taşır: adım adım rehber, kupon/indirim, özellik listesi.

Çıktı Notion sayfasına kart kart (callout) yazılır; her kopyalanacak parça tek tık kopyalanabilir
kod bloğudur, ManyChat'e elle taşıman kolay olsun diye. İdempotent: paneli olan video atlanır.

## Hedef seçimi (ikon + statü kapısı)

İki kapı birden geçilmeli; ikisi de **config'ten** ayarlanır:
- **İkon:** Notion sayfa ikonu (custom emoji adı) hedef sınıflara giriyorsa işlenir
  (varsayılan: `reels`, `ai-factory`). İstemediğin ikonlu kartlar atlanır.
- **Statü:** video belirli bir olgunluğa gelince yazılır (varsayılan: "Çekime Hazır",
  "Çekildi - Edit YOK", "Çekildi - Edit TAMAM", "Draft Onayı Bekliyor"). Daha erken aşama çok ham.

Bu listeleri kendi Notion şemana göre `NOTION_TARGET_ICONS` / `NOTION_TARGET_STATUSES`
env değişkenleriyle (virgülle ayrılmış) değiştir. Boş bırakırsan yukarıdaki varsayılanlar geçerli.

## Stack

Python 3.11, httpx, Notion REST API. Üretim LLM'i için iki seçenek:
- **API'siz (önerilen, maliyetsiz):** Notion alışverişini `routine_io.py` deterministik yapar;
  yaratıcı işi (web araması + akış metni) bir Claude Code cloud routine'inin kendi modeli yazar.
- **Manuel yedek (API harcar):** `main.py` + `core/llm.py` Anthropic API ile uçtan uca üretir.
  Varsayılan model küçük/ucuz; üst sınıf model bilinçli seçilir (`MANYCHAT_MODEL`).

## Çalıştırma

```bash
# Deterministik hat (API'siz — cloud routine içinden veya elle):
python routine_io.py targets                       # hedefleri JSON listele
python routine_io.py write <page_id> < flow.json   # paneli Notion'a yaz

# Manuel yedek (Anthropic API harcar):
DRY_RUN=1 python main.py   # Notion'a yazmadan üret + konsola bas (kuru test)
python main.py             # tam koşum
```

## Environment Setup

`.env.example`'ı `.env` olarak kopyala. Zorunlu: `NOTION_SOCIAL_TOKEN`, `NOTION_DB_REELS_KAPAK`.
Manuel yedek için ek: `ANTHROPIC_API_KEY`. Ayar: `MAX_VIDEOS_PER_RUN` (default 5),
`MIN_SCRIPT_CHARS` (150), `DRY_RUN`, hedef ikon/statü override'ları. Tüm değişkenlerin açıklaması
`.env.example` içinde.

## Üreteceğin akışın tarzı — `agents/learnings.md`

Bot her üretimde `agents/learnings.md`'yi prompt'a enjekte eder. Burası senin "tarz kuralların":
açılış nasıl olmalı, buton sayısı, ton, yasak ifadeler. Dosya örnek kurallarla gelir; kendi
markanın diline göre düzenle. Bir akışı beğenmediğinde yeni bir kural ekle, ilgili paneli
sildirip yeniden ürettir.

## Deploy (opsiyonel)

`railway.json` Railway cron için hazır şablondur (`rootDirectory` projeyi göstermeli, boşsa
sessiz FAILED). Periyodik üretim CRON'a uygundur (iş bitince süreç çıkar). Maliyet açısından en
ucuz yol API'siz cloud routine + `routine_io.py`'dir; deploy zorunlu değildir, lokalde de
elle çalıştırabilirsin.
