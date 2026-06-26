---
name: reklam-fabrikasi-ugc-scraper
description: UGC Scraper v2.0. reklam-fabrikasi-ugc-scraper'ın halefi. Kullanıcı /ugc-scrape, /scrape ugc, /ugc inspiration, /find viral ugc, /tiktok scrape yazdığında ya da viral UGC TikTok senaryoları, yüksek dönüşümlü UGC transkriptleri, UGC swipe dosyası veya senaryo yazarı için eğitim verisi istediğinde kullan. Yerel TikTok sıralamasıyla (En Beğenilen + 90 günlük filtre) scraptik/tiktok-api kullanır ve scrape-creators transkriptleri ekler. Puanlama ile transkripsiyon arasında LLM alaka denetimi yapar; son swipe dosyası yalnızca kullanıcının VOC nişiyle gerçekten eşleşen videoları içerir. /ugc senaryo yazma becerisine beslemeye hazır düz metin swipe dosyası üretir.
---

# Reklam Fabrikası, UGC Scraper 2.0

TikTok'un yerel sıralamasıyla scraptik aracılığıyla organik TikTok'u kazır, düşük hesap formülüyle puanlar, her adayı VOC alaka için LLM ile denetler, transkriptleri yalnızca altın seçimler için oluşturur ve /ugc senaryo yazma becerisine hazır 25 gerçek viral UGC transkriptli düz metin swipe dosyası çıktılar.

Akış: Apify REST API ile kaz -> sert filtrele -> düşük hesap puanı ver -> LLM alaka denetimi (transkript harcamadan önce niş dışı gürültüyü temizler) -> yalnızca altın seçimleri transkribe et -> swipe dosyası oluştur.

Çalıştırma başına maliyet: ~0,06 dolar. Apify ücretsiz plan (aylık 5 dolar) ~90 çalıştırmayı karşılar.

---

## Adım 0, Apify MCP'nin bağlı olduğunu doğrula

Mevcut araçları kontrol et. `mcp__apify__add-actor` veya herhangi bir `mcp__apify__*` aracı görüyorsan Apify bağlı demektir, Adım 1'e atla.

Hiçbir `mcp__apify__*` aracı yoksa, kullanıcı henüz Apify tokenını sağlamamıştır. Tam olarak şu mesajı gönder ve DUR:

> Apify henüz bağlı değil. Apify Kişisel API tokenını eklemek için `/reklam-fabrikasi:setup-apify` çalıştır. Kurulum 30 saniyelik akışta seni yönlendirir ve tokenı kaydetmeden önce Apify API'sine karşı doğrular. Tamamlandıktan sonra Claude'dan tamamen çık (Cmd+Q) ve yeniden aç, ardından `/ugc-scrape`'i yeniden çalıştır.

MCP sunucusunu kendin kurmaya çalışma, `~/.claude.json`'ı düzenleme, kullanıcıdan buraya token yapıştırmasını isteme. Kurulum komutu tümünü yönetir ve tokenı eklentinin hassas userConfig alanı üzerinden saklar. Bu eklentinin `.mcp.json`'ındaki Apify MCP girişi, başlangıçta tokenı `Authorization: Bearer` başlığı olarak enjekte eder; token hiçbir zaman diskte bir URL'ye düşmez.

Güvenlik notu: 1.3.3'ten önceki sürümlerde bu beceri kullanıcıdan tokenı buraya yapıştırmasını isteyip `~/.claude.json`'a URL sorgu dizesi olarak yazıyordu. Bu, MCP yetkilendirme spesifikasyonu tarafından işaret edilen bir anti-pattern'di; URL'ye gömülü tokenlar kabuk geçmişine, log dosyalarına ve diskteki duruma sızar. 1.3.3'ten bu yana token, eklentinin `apify_api_key` userConfig alanı altında saklanır; macOS ve Windows'ta işletim sistemi anahtarlığında, anahtarlığın bulunmadığı Linux'ta ise `~/.claude/.credentials.json`'da tutulur. Düz token hiçbir zaman `~/.claude.json`'a yazılmaz.

(Bakıcılar için sonda not: `https://mcp.apify.com/?actors=scraptik/tiktok-api` adresine `Authorization: Bearer <fake_token>` ile curl testi, "Bir Apify API tokenını Authorization: Bearer <token> başlığında geçirin" mesajıyla HTTP 401 döndürdü. Bu, header tabanlı kimlik doğrulamanın aynı MCP uç noktasında desteklenen ve belgelenmiş mekanizma olduğunu doğruladı.)

---

## Adım 0.5, Proje çıktı klasörünü belirle

Çıktılar, Claude Code'un açık olduğu çalışma klasörüne kaydedilir. Girdileri toplamadan önce bu Bash bloğunu çalıştır:

```
PWD_ABS="$(pwd)"
TARGET="${PWD_ABS}/Reklam Fabrikası"
PROTECTED=0
case "$PWD_ABS" in
  "$HOME"|"$HOME/"|"/"|"/tmp"|"/tmp/"|"$HOME/Downloads"|"$HOME/Desktop")
    PROTECTED=1 ;;
esac
if [ "$PROTECTED" = "1" ] && [ ! -d "$TARGET" ]; then
  echo "PROTECTED:$PWD_ABS"
elif [ ! -f "$TARGET/_meta/folder-confirmed.flag" ] && [ ! -d "$TARGET" ]; then
  echo "FIRSTRUN:$TARGET"
else
  mkdir -p "$TARGET/05_UGC/scraper" "$TARGET/_meta"
  echo "READY:$TARGET"
fi

# Marka klasörü varsa ve dosya eksikse marka belleğini (CLAUDE.md) başlat.
# Yapacak bir şey olmadığında sessizce ve tekrar çalıştırılabilir biçimde çalışır.
if [ -d "$TARGET" ] && [ -n "${CLAUDE_PLUGIN_ROOT:-}" ] && [ -f "$CLAUDE_PLUGIN_ROOT/scripts/seed-claude-md.sh" ]; then
  bash "$CLAUDE_PLUGIN_ROOT/scripts/seed-claude-md.sh" >/dev/null 2>&1 || true
fi
```

- `PROTECTED:<path>`: reddet ve kullanıcıya Claude Code'u markaya özel bir alt klasörde açmasını söyle. Dur.
- `FIRSTRUN:<path>`: "Çıktıları `<path>/` konumuna kaydedeceğim. Bu klasöre ilk kez kaydediliyor, doğru mu? (evet/hayır)" diye sor. Evet'e klasörleri oluştur ve `<path>/_meta/folder-confirmed.flag` dosyasını yaz. Hayır'a dur.
- `READY:<path>`: sessizce devam et.

Çözümlenen yolu `$RFLAB` olarak kaydet.

Otomatik keşif: en son VOC dosyası için `$RFLAB/01_VOC_Research/` klasörünü tara. Biri varsa, kullanıcıdan VOC'u tekrar yapıştırmasını istemek yerine onu kullanmayı öner:

```
ls -t "$RFLAB/01_VOC_Research/"*.html "$RFLAB/01_VOC_Research/"*.md 2>/dev/null | head -n 1
```

Bulunursa kullanıcıya söyle: "Bu proje klasöründen VOC için `<dosyaadı>` kullanılıyor. Devam etmek için 'kullan', farklı bir VOC sağlamak için 'yapıştır' yaz."

## Adım 1, Girdileri topla

> **UGC Scraper 2.0 kurulumu**
>
> İhtiyacım olan 2 şey:
>
> **1. Müşteri Sesi (VOC) belgesi**, yükle veya yapıştır. Hem 6 sorguyu oluşturmak hem de sonda alaka denetimi yapmak için kullanıyorum.
>
> **2. Ürün veya niş**, ne arıyoruz? (örn. "DTC kurucular için AI reklam üretici", "retinol serum", "taşınabilir blender")
>
> İsteğe bağlı:
> - Ülke (varsayılan: US)
> - Özel sorgular (atlarsan VOC'tan oluştururum)

VOC yoksa: iste. VOC içeriği hiçbir zaman uydurma.

---

## Adım 2, VOC'tan 6 arama sorgusu oluştur

VOC'u oku ve bu 6 kapsam slotunu içeren 6 sorgu çıkar. Tam metodoloji için `references/Query_Building_Strategy.md` dosyasını yükle.

Kapsam slotları:
1. **Müşteri dilinde acı**, örn. "reklamlar çalışmayı durdurdu"
2. **Çözüm veya AI iş akışı**, örn. "gerçekten işe yarayan AI reklamları"
3. **Kimlik / ICP vlog**, örn. "dtc kurucu meta reklamları"
4. **Problemi bilen ham**, örn. "meta reklamlar bozuk" ("facebook reklamları ölüyor" kaçın, hesap-yardım gürültüsü çeker)
5. **İş akışı / nasıl yapılır**, örn. "ai ugc reklamları eğitimi"
6. **Akran güveni / format**, örn. "medya alıcısı günlük yaşam"

Her sorguyu 2 ila 4 kelimede tut. Çalıştırmadan önce 6 sorguyu kullanıcıya göster:

> İşte kullanacağım 6 sorgu:
> 1. ...
> 6. ...
>
> Hazır mısın? Yoksa kredi harcamadan önce herhangi birini düzenle.

Yalnızca kullanıcı onayladıktan sonra devam et.

---

## Adım 3, Apify REST API ile kaz (scraptik)

**MCP araçlarını kullanma.** MCP araç kaydı, aktör eklemelerinin gerisinde kalır ve çağrılar sessizce başarısız olabilir. Apify REST API'sini doğrudan eklentinin hassas userConfig alanındaki tokenı kullanarak çağır.

### 3.1, Tokenı settings.json'dan oku

Eklenti, kullanıcı `/reklam-fabrikasi:setup-apify` çalıştırdığında tokenı `pluginConfigs["reklam-fabrikasi"].apify_api_key` altına kaydeder. Değeri yankılamadan oku:

```bash
TOKEN=$(python3 -c "import json,os,sys; p=os.path.expanduser('~/.claude/settings.json'); d=json.load(open(p)) if os.path.exists(p) else {}; t=d.get('pluginConfigs',{}).get('reklam-fabrikasi',{}).get('apify_api_key',''); sys.stdout.write(t)")
```

`TOKEN` boşsa kullanıcı henüz kurulum yapmamış demektir. `/reklam-fabrikasi:setup-apify` çalıştırmasını söyle ve dur.

Token, aşağıdaki tüm Apify REST çağrılarında `Authorization: Bearer` başlığı olarak geçirilmelidir. URL sorgu dizesine asla koyma; bu pattern, v1.3.3'te kabuk geçmişine ve log dosyalarına sızdığı için kaldırıldı.

### 3.2, 6 sorguyu paralel olarak çalıştır

Her sorgu için tokenı başlıkta kullanarak Apify'ın senkron uç noktasına POST yap:

```bash
for i in 0 1 2 3 4 5; do
  curl -sS -X POST "https://api.apify.com/v2/acts/scraptik~tiktok-api/run-sync-get-dataset-items?timeout=120" \
    -H "Authorization: Bearer ${TOKEN}" \
    -H "Content-Type: application/json" \
    -d @"/tmp/ugc-scrape/in-${i}.json" \
    -o "/tmp/ugc-scrape/out-${i}.json" \
    -w "q${i} HTTP=%{http_code} TIME=%{time_total}s\n" &
done
wait
```

**Sorgu başına girdi yükü** (`/tmp/ugc-scrape/in-<i>.json` dosyasına yaz):

```json
{
  "searchPosts_keyword": "<sorgu>",
  "searchPosts_count": 20,
  "searchPosts_publishTime": 90,
  "searchPosts_sortType": 1,
  "searchPosts_region": "US"
}
```

**Kritik parametreler:**
- `searchPosts_sortType: 1` = En Beğenilen (görüntülemeler için TikTok'un yerel vekili). **0 (Alaka) kullanma**; çok daha zayıf sinyal.
- `searchPosts_publishTime: 90` = son 90 gün (zorunlu; trendler hızlı değişir).
- `searchPosts_count: 20` = sorgu başına maksimum. Sorgu başına daha fazlası azalan sinyal döndürür.
- `searchPosts_region: "US"` = büyük harfli ISO-2 ülke kodu.

### 3.3, Yanıtı ayrıştır

Her yanıt bir nesne içeren bir JSON dizisidir. Video listesi `[0].search_item_list` adresindedir, **`aweme_list` DEĞİL** (bu alan mevcut ama scraptik çıktısında her zaman boş). Her öğenin `aweme_info`'su tam TikTok meta verisini içerir.

6 sorgu arasında `aweme_info.aweme_id` ile tekrarları temizle. Tipik verim: 120 ham -> 100 ila 115 benzersiz.

Kullanıcıya söyle:
> "scraptik ile 6 sorgu x 20 sonuç kazınıyor, ~10 saniye sürer."

**Maliyet: 6 istek x 0,001 dolar = kazıma için 0,006 dolar.**

---

## Adım 4, Şemayı uyarla + sert filtrele + puanla

### 4.1, scraptik çıktısını puanlama şemasına uyarla

```bash
python3 ~/.claude/skills/reklam-fabrikasi-ugc-scraper-2.0/scripts/adapt_scraptik.py \
  /tmp/ugc-scrape/raw_unique.json \
  /tmp/ugc-scrape/adapted.json
```

scraptik alanlarını puanlama şemasına eşler:
- `statistics.play_count` -> `views`
- `author.follower_count` -> `channel.followers`
- `aweme_id` -> `id`
- vb.

### 4.2, Takipçi tabanıyla puanla

```bash
python3 ~/.claude/skills/reklam-fabrikasi-ugc-scraper-2.0/scripts/score_videos.py \
  /tmp/ugc-scrape/adapted.json \
  /tmp/ugc-scrape/scored.json \
  80
```

Son argüman tutulacak en iyi N değeridir. 80 kullan (alaka denetimi için geniş bir havuz istiyoruz).

Sert filtre şunları eler:
- görüntüleme < 10.000
- süre < 5s veya > 180s
- paylaşım == 0 ve yorum < 5
- eksik kanal/kullanıcıadı
- yüklendiği zaman == 0 veya yaşı > 90 gün

Puanlama formülü: `FinalScore = ViewPower x CreatorUnderdog x EngagementQuality x Recency`

**Takipçi tabanı**: Çıkış etiketi yalnızca `views/followers >= 50 VE followers >= 100` ise uygulanır. Bu, düşük hesap oranını manipüle edebilen sahte/bot hesapları dışlar.

Kullanıcıya raporla:
> "X kazındı -> Y sert filtreyi geçti -> alaka denetimi için en iyi Z"

---

## Adım 5, LLM alaka denetimi (satır içi, API maliyeti yok)

**Bu adım swipe dosyasını gerçekten kullanışlı yapan şeydir.** TikTok'un En Beğenilen sıralaması iyi ama mükemmel değil; yine de anahtar kelimelerle eşleşen ama niyetle eşleşmeyen videolar döndürüyor. Alaka denetimi, transkript adımına ulaşmadan önce bunları filtreler.

`/tmp/ugc-scrape/scored.json` dosyasını oku. `top_n`'deki her aday için `title` (başlık) + `hashtags`'in kullanıcının VOC nişiyle ne kadar eşleştiğini 0 ila 10 üzerinden puanla.

### 5.1, Değerlendirme ölçütü

| Puan | Anlam | Reklam Fabrikası VOC için örnek |
|---|---|---|
| **10** | Mükemmel uyum. Doğrudan tam niş hakkında. | "meta reklamlarımı Claude'a bağladım ve sonuçlar çılgınca" |
| **8 ila 9** | Çok yakın. Bitişik konu, doğru kitle. | "gerçekten değer verdiğim 5 UGC uygulaması", "7-8 rakamlı marka meta reklam ayarları" |
| **6 ila 7** | Teğet. Doğru alan ama spesifik ICP değil. | "2026'da işletmeler için en iyi AI araçları" |
| **4 ila 5** | Zayıf. Aynı anahtar kelime, yanlış bağlam. | "okul ödevleri için AI araçları" |
| **1 ila 3** | Konu dışı. Yalnızca anahtar kelime eşleşmesi. | TikTok AI ayar serzenişleri, Facebook hesap yardımı |
| **0** | Tamamen alakasız. | Golf vuruşu, bahçe düzenlemesi, komplo teorileri |

### 5.2, Puanlama prosedürü

Adayları tek tek (veya toplu olarak) incele. Şunları değerlendir:
- Başlık, VOC hedef kitlesinin ilişki kuracağı bir ürün, iş akışı veya sıkıntı noktasını açıklıyor mu?
- İngilizce mi? (Niş açıkça o dili içermedikçe diğer dillerdeki içerik için ≤2 puan.)
- İçerik üreticisi gerçekten ICP'ye mi hitap ediyor? (Sephora vlog'unun "medya alıcısı" anahtar kelimesi üzerine puan alması gürültüdür.)

**7'nin altındaki her şeyi ele.** Sınırdaki 6'lar için, yalnızca 25'i daha yüksek puanlardan dolduramıyorsak tut.

### 5.3, İçerik üreticisi sınırı

Son altın sette içerik üreticisi başına maksimum 2 video tut (açı çeşitliliğini teşvik eder).

### 5.4, Son 25 altın seçimi belirle

Hayatta kalan adayları şu sıraya göre sırala: (alaka AZALAN, final_score AZALAN).

En iyi 25'i al. 25'ten az >=7 puan alırsa kullanıcıya söyle:
> "Yalnızca N aday alaka denetimini geçti. Seçenekler: sahip olduğumuz N'yi transkribe et veya daha fazla aday çekmek için farklı sorgularla yeniden çalıştır."

Altın seti her öğede `_relevance` alanıyla `/tmp/ugc-scrape/gold25.json` dosyasına yaz.

Transkribe etmeden önce kullanıcıya 25 seçimi kısaca göster (kullanıcıadı, alaka, görüntüleme). Sor:
> "İşte 25 altın seçim. Tümünü transkribe edeyim mi? (~0,05 dolar, scrape-creators üzerinden)"

Yalnızca kullanıcı evet derse transkriptleri çalıştır.

---

## Adım 6, Altın seçimleri transkibe et

`gold25.json`'dan 25 URL çıkar. Tokenı başlıkta kullanarak scrape-creators'a tek toplu çağrı yap:

```bash
python3 -c "
import json
gold = json.load(open('/tmp/ugc-scrape/gold25.json'))
urls = [v['postPage'] for v in gold]
json.dump({'videos': urls}, open('/tmp/ugc-scrape/transcripts-input.json','w'))
"

curl -sS -X POST "https://api.apify.com/v2/acts/scrape-creators~best-tiktok-transcripts-scraper/run-sync-get-dataset-items?timeout=300" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d @/tmp/ugc-scrape/transcripts-input.json \
  -o /tmp/ugc-scrape/transcripts.json \
  -w "HTTP=%{http_code} TIME=%{time_total}s\n"
```

**Maliyet: 25 x 0,002 dolar = 0,050 dolar.**

Beklenen isabet oranı: ~%95+ (alaka denetimi çoğu müzik/metin bindirmeli gürültüyü filtreler).

Transkriptler `transcript` alanında WebVTT olarak gelir. Null = konuşma içeriği yok.

**Asla video başına toplu işlem yapma.** Her zaman tüm 25 URL'yi tek bir çağrıda geçir.

---

## Adım 7, Swipe dosyasını oluştur

Yapı betiği çıktıları yalnızca Adım 0.5'te belirlenen proje klasörü altına yazar. `--output-dir` olmadan çalışmayı reddeder; böylece asla yanlışlıkla bir ev klasörüne veya masaüstü yoluna geri dönemez. Windows'ta OneDrive Bilinen Klasör Taşıma etkinleştirilmişse, swipe dosyası her zaman Claude Code'u açtığın proje klasörüne düşer; asla OneDrive'la eşitlenen bir masaüstü yönlendirmesine değil.

```bash
python3 ~/.claude/skills/reklam-fabrikasi-ugc-scraper-2.0/scripts/build_swipe.py \
  /tmp/ugc-scrape/gold25.json \
  /tmp/ugc-scrape/transcripts.json \
  <niche-slug> \
  --output-dir "$RFLAB"
```

Tam şablon için `references/Plain_Text_Output_Format.md` dosyasını yükle.

Çıktı dosyası (Adım 0.5'te belirlenen proje klasörü altında):
```
$RFLAB/05_UGC/scraper/<niche-slug>/ugc-winners-v2-<YYYY-MM-DD>.txt
```

(Betik `$RFLAB/05_UGC/scraper/<niche-slug>/` klasörünü otomatik olarak oluşturur. Niş alt dizini oluşturulamazsa `$RFLAB/05_UGC/scraper/ugc-winners-v2-<YYYY-MM-DD>-<niche-slug>.txt` konumuna geri döner. Kullanıcıya onaylarken `$RFLAB` yerine mutlak yolu yaz.)

Her kazanan bloğu şunları içerir:
- Sıra, alaka puanı, final_score, varsa çıkış bayrağı
- İçerik üreticisi meta verisi (kullanıcıadı, takipçiler, takipçi başına görüntüleme oranı, doğrulanmış)
- Etkileşim metrikleri (görüntüleme, beğeni, paylaşım, yorum, kaydetme, süre)
- Bağlam (yaş, hashtagler, şarkı, arama sorgusu)
- Başlık metni (TikTok başlığı, metin bindirme hookları burada yaşar)
- Transkript kaynağı + tam transkript
- Hook satırı (konuşmanın ilk ~12 kelimesi)

Kazananları şu sıraya göre sırala: alaka AZALAN, final_score AZALAN.

---

## Adım 8, Dosyayı sun

> **UGC swipe dosyası v2 hazır.**
>
> [N] benzersiz kazındı -> [M] hayatta kalana filtrelendi -> [25] altın seçim (ort. alaka X.X/10) -> [K] transkribe edildi.
>
> Yalnızca nişteki viral kazananlara dayanan senaryolar oluşturmak için bunu /ugc'ye besle.

Mutlak yolu markdown bağlantısı olarak ver.

Uzun bir özet yazma. Dosya TESLİMAT'IN kendisidir.

---

## Maliyet özeti

| Adım | Çağrılar | Birim | Ara toplam |
|---|---|---|---|
| scraptik kazıma | 6 istek | 0,001 dolar | 0,006 dolar |
| scrape-creators transkriptleri | 25 URL | 0,002 dolar | 0,050 dolar |
| LLM alaka denetimi (satır içi) | 0 API | 0 dolar | 0 dolar |
| **Çalıştırma başına TOPLAM** | | | **~0,056 dolar** |

Apify ücretsiz plan (aylık 5 dolar) = **ayda ~90 çalıştırma.**

---

## Hiçbir zaman yapma

1. **Alaka denetimini asla atlama.** Sorgular ne kadar temiz görünse de TikTok'un yerel araması gürültü çeker. Denetim, swipe dosyasını aşağı akış `/ugc` becerisi için gerçekten kullanışlı yapan şeydir.
2. **Aktörleri çağırmak için asla MCP araçlarını kullanma.** MCP araç kaydı gecikebilir ve sessizce başarısız olabilir. REST API doğrudan güvenilir yoldur.
3. **scraptik yanıtında asla `[0].aweme_list` okuma, her zaman boştur.** `[0].search_item_list[].aweme_info` kullan.
4. **`searchPosts_sortType: 0` (Alaka) asla geçirme.** Her zaman `1` (En Beğenilen) kullan. Alaka çok daha gürültülüdür.
5. **`searchPosts_publishTime: 0` (Tüm Zamanlar) asla ayarlama.** Her zaman `90` kullan; eski içerik bayatlamış hooklar içerir.
6. **Asla transkript uydurma.** Video null döndürürse "transkript mevcut değil" olarak işaretle ve başlığı referans olarak tut.
7. **Alaka denetiminden önce asla transkribe etme.** Niş dışı kazananlara para harcamış olursun.
8. **Apify tokenını asla URL sorgu dizesine koyma.** Her zaman başlıkta `Authorization: Bearer ${TOKEN}` olarak geçir. Token-URL'de kabuk geçmişine ve disk log'larına sızar; bu pattern v1.3.3'te kaldırıldı.
9. **Tokenı asla `~/.claude.json`'a yazma.** Eklentinin userConfig sistemi, mevcut olduğunda işletim sistemi anahtarlığında saklar; Linux'ta `~/.claude/.credentials.json`'da. Kurulum `/reklam-fabrikasi:setup-apify` üzerinden çalışır.

---

## Referans dosyaları

| Dosya | Ne zaman yükle | Öncelik |
|---|---|---|
| `scripts/adapt_scraptik.py` | Adım 4.1, scraptik şemasını eşle | Kritik |
| `scripts/score_videos.py` | Adım 4.2, puanlama + filtre | Kritik |
| `scripts/parse_webvtt.py` | Adım 7, build_swipe içinde WebVTT'yi ayrıştır | Kritik |
| `scripts/build_swipe.py` | Adım 7, son metin dosyasını oluştur | Kritik |
| `references/Query_Building_Strategy.md` | Adım 2, VOC'tan sorgu çıkar | Kritik |
| `references/Plain_Text_Output_Format.md` | Adım 7, çıktı format özellikleri | Kritik |

---

## Çıktı doğrulaması

Bu beceriyi tamamlandı olarak bildirmeden önce doğrula:

1. Beklenen yolda çıktı mevcut: `<pwd>/Reklam Fabrikası/05_UGC/scraper/<niche-slug>/ugc-winners-v2-<YYYY-MM-DD>.txt` (veya yedek yol).
2. Çıktı boş değil (25 transkript için dosya boyutu > 8000 bayt sağlıklı minimum).
3. Beklenen içerik sayısı iddia ile eşleşiyor:
   - Swipe dosyası 25'e kadar kazanan içeriyor.
   - Dosyanın aşağı akış /ugc becerisi için kullanışlı olması için en az 10 kazanan mevcut olmalı.
   - Her kazanan bloğunda sıra, alaka puanı, final_score, içerik üreticisi meta verisi, etkileşim metrikleri, başlık, transkript veya "transkript mevcut değil" var.
4. Yer tutucu dize kalmamış:
   - `<niche>`, `<query>`, `<TODO>` veya `lorem ipsum` yok.
5. Tüm zorunlu bölümler doldurulmuş:
   - Başlık (niş, tarih, kazıma istatistikleri)
   - 25 kazanan bloğu (veya alaka denetimini N<25 geçtiyse daha az)
   - Sıralama düzeni: alaka AZALAN, sonra final_score AZALAN

Doğrulama başarısız olursa:

1. Önce otomatik düzeltmeye çalış:
   - Kazanan blokta transkript eksikse "transkript mevcut değil" olarak işaretle ve başlığı referans satırı olarak tut.
   - Swipe dosyasında az kazanan varsa, sınırdaki adaylar için alaka eşiğini 7'den 6'ya düşür ve onları yeniden dahil et.
   - Dosya yapısı bozuksa `gold25.json` ve `transcripts.json` kullanarak `build_swipe.py` ile yeniden oluştur.

2. Otomatik düzeltme başarısız olursa, kullanıcıya dürüst rapor sun:
   "UGC kazıyıcı: Swipe dosyası ürettim ama doğrulama <sorun> gösterdi. <düzeltme girişimi>'ni denedim ve <işe yaramadı / kısmen işe yaradı>. Eksiksiz sonuç almak için şunları yapabilirsin:
   - Sorguların daha alakalı nişleri çekebilmesi için daha zengin VOC belgesi sağla
   - Niş bölgesel ise ülke değişikliğini onayla (örn. US yerine GB)
   - Daha gürültülü ama daha büyük swipe dosyası için daha geniş alaka eşiğini onayla (7 yerine 5)
   Veya nişteki 3 ila 5 bilinen viral içerik üreticisi yapıştır, doğrudan kanallarını kazıyayım."

3. Sert filtreden sonra scraptik 10'dan az aday döndürdüyse:
   - ONCE daha geniş parametrelerle dene:
     - 90 günlük yayın zamanı filtresini 180 güne düşür
     - Görüntüleme tabanını 10000'den 5000'e indir
     - VOC eş anlamlılarından ve bitişik topluluklardan 3 alternatif sorgu ekle
   - Hâlâ 10'un altındaysa, dürüst rapor sun:
     "UGC kazıyıcı: TikTok'ta En Beğenilen sıralamasıyla 6 sorgu (ve 3 daha geniş yedek sorgu) denedim. Sert filtre ve alaka denetiminden sonra yalnızca N aday hayatta kaldı. Bu genellikle niş TikTok'ta çok dar olduğunda ya da VOC aranabilir terimler sunmadığında olur. Devam etmek için şunları yapabilirsin:
     - Daha geniş kategoriyi belirt (belirli bir marka yerine örn. 'ev fitness'i)
     - Nişte bilinen 3 içerik üreticisi kolunu yapıştır, doğrudan kanallarını kazıyayım
     - İngilizce dışı viral içeriğin sayılması için İngilizce filtre gevşetmeyi onayla
     Ya da daha iyi sorgular için önce ilgili bir ürün üzerinde /voc çalıştır."
