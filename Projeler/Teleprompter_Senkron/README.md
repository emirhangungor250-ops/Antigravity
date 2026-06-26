# Teleprompter_Senkron

Notion'daki bir script veritabanında **"hazır"** duruma gelen video metinlerini, çekimde
okunacak temiz prompter metnine çevirip Google Drive'daki bir teleprompter klasörüne yazan
otomasyon. Tabletteki teleprompter uygulaması (ör. **Nano Teleprompter**, Android) Drive'a
bağlanınca KENDİ klasörünü açar ve yalnızca onu gerçek zamanlı senkronlar. Hiçbir dosya
import etmenize gerek kalmaz: kartı "hazır" işaretlersiniz, script tablette belirir.

## Bu desen ne işe yarar
İçerik üreten, sunucu konuşması yazan ya da düzenli kamera önü çekim yapan herkes için:
script'i yazdığınız yerden (Notion), prompterda okunacak temiz metne otomatik dönüştürür.
Ham notlar (linkler, hashtag, prodüksiyon yönergeleri, dağıtım/DM blokları) atılır; yalnızca
söylenecek metin kalır. Çekim öncesi kopyala-yapıştır / elle temizleme zahmetini kaldırır.

## Stack
- Python 3.11, cron ile periyodik çalışır (GitHub Actions örneği aşağıda)
- Notion API (`notion-client`) — kaynak script'ler
- AI temizleme: birincil **OpenAI** (varsayılan ucuz model) → anahtar yoksa/patlarsa
  **Anthropic (Claude)** fallback. Modeller `.env`'den değiştirilebilir.
- Google Drive API (OAuth, **tam `drive` scope**) — teleprompter klasörüne yazar

## Teleprompter klasör davranışı (KRİTİK)
Teleprompter uygulaması kendi klasörünü İKİ YÖNLÜ senkronlar ve sahiplenir:
- Bıraktığınız `.txt`'i **Google Doc'a çevirir** (`.txt` uzantısı düşer).
- Drive'dan **sildiğiniz** dosyayı **geri getirir** (uygulamadaki kopyayı tekrar yazar).

Sonuç: klasörü siz yönetemezsiniz (sil/yeniden adlandır kalıcı olmaz). Tasarım bu yüzden
**"bir kez bırak"**: yeni script'i bir kez koyarsınız, sonra dokunmazsınız. Silme/güncelleme
uygulamanın işi, uygulamadan yapılır.

## Çalışma Şekli
1. Status = hazır kartları çekilir. Adı veya gövdesi boş olan atlanır.
2. Klasördeki dosya adları (Doc'lar dahil) okunur; gün damgası ayıklanıp kart adına eşlenir
   (`7 Haziran - X`, `X.txt`, `X` hepsi -> `X`). Kart için dosya zaten varsa dokunulmaz.
3. Yoksa sayfa GÖVDESİ (özet/caption değil) AI ile temizlenir: linkler, hashtag, emoji,
   prodüksiyon notları, dağıtım/DM blokları çıkarılır; diyalog, "Yanlış→Doğru", ekran
   ipuçları, "BİTİŞ", kapanış korunur. (Kurallar `core/cleaner.py` içindeki SYSTEM
   prompt'unda; kendi script formatınıza göre uyarlayın.)
4. Temiz metin `{gün} - {kart adı}.txt` olarak klasöre **bırakılır**. Silme/çöp YOK —
   uygulama zaten geri getirir.

## Neden tam `drive` scope (drive.file değil)
Teleprompter uygulaması klasörünü kendi açar; `drive.file` başka uygulamanın oluşturduğu
klasörü göremez/yazamaz. O yüzden yalnız `drive` scope'lu ayrı bir token kullanılır.
Üretmek için (bir kerelik):
1. Google Cloud Console'da proje aç, Drive API'yi etkinleştir, **Desktop app** tipinde bir
   OAuth client ID oluştur. İnen JSON'u proje köküne `client_secret.json` olarak koy.
2. `python core/reauth_drive_full.py` çalıştır → tarayıcı açılır, izin verilince token
   proje köküne `drive-full-token.json` olarak kaydedilir.

## Environment
`.env.example`'ı `.env` olarak kopyalayıp doldurun:
- `NOTION_REELS_TOKEN` — Notion integration token (DB'yi bu integration ile paylaşın)
- `PROMPTER_NOTION_DB_ID` — script DB ID'niz
- `PROMPTER_DRIVE_FOLDER_ID` — teleprompter uygulamasının açtığı klasör ID'si
- `GOOGLE_DRIVE_TOKEN_JSON` — tam drive token (lokal'de `drive-full-token.json`'dan da okunur)
- `OPENAI_API_KEY` ve/veya `ANTHROPIC_API_KEY` — AI temizleme
- (Opsiyonel) `NOTION_STATUS_PROPERTY` / `NOTION_STATUS_READY` — DB şemanız farklıysa
- (Opsiyonel) `EXPECTED_DRIVE_DOMAIN` — yanlış Google hesabına yazmayı önleyen güvenlik kapısı

## Çalıştırma
```
python sync.py            # gerçek senkron
python sync.py --dry-run  # plan; Drive'a dokunmaz
```

## Güvenlik kapısı
`EXPECTED_DRIVE_DOMAIN` ayarlıysa, kod yazmadan önce token'ın o domain'e ait bir Google
hesabına bağlı olduğunu doğrular; değilse hiçbir şey yazmadan durur. Boş bırakırsanız kapı
kapalıdır (her hesaba yazar).

## Deploy — GitHub Actions cron örneği
Aşağıdaki dosyayı `.github/workflows/sync.yml` olarak ekleyin. Secret adlarını repo
ayarlarından (Settings → Secrets and variables → Actions) doldurun.

```yaml
name: Teleprompter Sync
on:
  schedule:
    - cron: "0 */2 * * *"   # 2 saatte bir
  workflow_dispatch: {}       # elle tetik

jobs:
  sync:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: pip install -r requirements.txt
      - run: python sync.py
        env:
          NOTION_REELS_TOKEN: ${{ secrets.NOTION_REELS_TOKEN }}
          PROMPTER_NOTION_DB_ID: ${{ secrets.PROMPTER_NOTION_DB_ID }}
          PROMPTER_DRIVE_FOLDER_ID: ${{ secrets.PROMPTER_DRIVE_FOLDER_ID }}
          GOOGLE_DRIVE_TOKEN_JSON: ${{ secrets.GOOGLE_DRIVE_TOKEN_JSON }}
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
```

`railway.json` da pakette: isterseniz Railway'de cron olarak (`python sync.py`) koşturabilirsiniz.
