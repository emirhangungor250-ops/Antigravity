# Düz Metin Çıktı Formatı v2

Tek `.txt` dosyası. Hem insan tarafından okunabilir hem de aşağı akış `/ugc` becerisi tarafından makine ile ayrıştırılabilir biçimde tasarlanmıştır.

`build_swipe.py` betiği bu dosyayı üretir. Bu belge, betiğin uyguladığı özelliktir.

## Tam Şablon

```
================================================================================
UGC SCRAPER 2.0, VIRAL TIKTOK WINNERS, {{NICHE_TITLE_UPPER}}
================================================================================

Niche:             {{NICHE_TITLE}}
Date:              {{YYYY-MM-DD}}
Source:            tiktok_organic
Pipeline:          scraptik (scrape) + LLM relevance vet + scrape-creators (transcripts)

Final winners:     {{FINAL_COUNT}}
Transcripts:       {{WHISPER_N}} usable / {{UNAVAIL_N}} unavailable
Pure breakouts:    {{BREAKOUT_COUNT}}
Avg relevance:     {{AVG_REL}}/10
Avg scoring:       {{AVG_SCORE}}

================================================================================
  WINNER #1    |    REL: {{REL}}/10    |    SCORE: {{SCORE}}    |    {{BREAKOUT_TAG_IF_APPLICABLE}}
================================================================================

CREATOR:       @{{USERNAME}}{{VERIFIED_TAG}}
FOLLOWERS:     {{FOLLOWERS_FORMATTED}}
RATIO:         {{RATIO}}x views per follower

METRICS:       {{VIEWS}} views, {{LIKES}} likes, {{SHARES}} shares, {{COMMENTS}} comments, {{SAVES}} saves
DURATION:      {{DURATION}} seconds
AGE:           {{AGE_DAYS}} days ago ({{UPLOADED_AT_FORMATTED}})

HASHTAGS:      {{HASHTAGS_COMMA_SEPARATED}}
AUDIO:         {{SONG_TITLE}}
SEARCH QUERY:  {{SEARCH_QUERY}}

TIKTOK URL:    {{TIKTOK_URL}}
CAPTION TEXT:  {{CAPTION_UP_TO_500_CHARS}}
TRANSCRIPT:    {{TRANSCRIPT_SOURCE_LABEL}}

HOOK LINE:
>>> {{HOOK_LINE}}

FULL TRANSCRIPT:
{{FULL_TRANSCRIPT}}

================================================================================
  WINNER #2    |    REL: {{REL}}/10    |    SCORE: {{SCORE}}    |    {{BREAKOUT_TAG_IF_APPLICABLE}}
================================================================================

... (tüm 25 kazanan için aynı yapı)

================================================================================
END OF SWIPE FILE
================================================================================

HOW TO USE THIS FILE:

1. Open the /ugc skill
2. Attach or paste this file when the skill asks for UGC inspiration
3. The script writer learns from these real viral hooks and writes new scripts
   grounded in actual language that stopped scroll in your niche

v2 guarantee: every winner here passed an LLM relevance vet against your VOC.
No off-niche noise, no unrelated viral content padding the file.

Scoring notes:
  REL (0-10) = VOC relevance. Higher is more directly on-niche.
  SCORE combines views, creator underdog ratio, engagement quality, recency.
  BREAKOUT WINNER = follower floor 100+ AND views/followers >= 50.
  These are cleanest examples of hooks carrying videos (not audience size).
```

## v1'e göre yenilikler

- **Her kazanan blokta alaka alanı (REL).** v1'de alaka puanlaması yoktu.
- **TIKTOK URL'nin altına CAPTION TEXT alanı eklendi.** Konuşma transkriptlerinin kaçırdığı metin bindirme hooklarını korur.
- **SEARCH QUERY alanı**, 6 sorgudan hangisinin bu videoyu bulduğunu gösterir. Sorgu ince ayarı için kullanışlı.
- **Sıralama düzeni** alaka AZALAN, sonra final_score AZALAN (v1 yalnızca final_score'du).
- **Başlık**, aşağı akış araçların v2'nin kullanıldığını bilmesi için akış tanımı içeriyor.

## Biçimlendirme kuralları

### Sayı biçimlendirme
- 1.000'in altında: tam sayı (`847`)
- 1.000 ile 999.999 arası: bir ondalık + K (`12.4K`, `450.0K`)
- 1.000.000 ve üzeri: bir ondalık + M (`2.3M`, `12.1M`)

Şunlara uygula: görüntüleme, beğeni, paylaşım, yorum, kaydetme, takipçi.

### Oran
`{{RATIO}}` = görüntüleme / takipçi.
- 100'ün altında: bir ondalık (`2.4`, `85.1`)
- 100 ve üzeri: tam sayı (`150`, `4416`)

### Doğrulanmış etiketi
`channel.verified` true ise kullanıcıadına ` (verified)` ekle. Aksi takdirde boş.

### Çıkış etiketi
`_scoring.underdog_flag` true ise: dördüncü boru slotuna `BREAKOUT WINNER` yaz.
Aksi takdirde: dördüncü slotu tamamen atla (boş boru yok).

Çıkış için her ikisi de zorunlu: `views/followers >= 50` VE `followers >= 100`.

### Transkript kaynak etiketi
- `whisper_fallback`: `WHISPER AI (FALLBACK)` olarak göster
- `unavailable`: `UNAVAILABLE` olarak göster

### Transkript mevcut değil
HOOK LINE ve FULL TRANSCRIPT'i şununla değiştir:

```
HOOK LINE:
>>> (transcript unavailable, rely on caption above)

FULL TRANSCRIPT:
This video does not have usable speech content. Caption and hashtags are
above for reference. Text-overlay hooks may be present in the video itself.
```

v2 swipe dosyası, transkript mevcut olmadığında hook bağlamı sağlamak için CAPTION TEXT alanına dayanır.

### Hashtagler
İlk 5, `#` ile önek, `, ` ile birleştirilmiş. 5'ten az varsa hepsini birleştir. Sıfırsa `none` göster.

### Şarkı başlığı
- `music.title` "original sound" + sanatçı içeriyorsa: `original sound by @{{artist}}`
- Sanatçı varsa: `{{title}} by {{artist}}`
- Sanatçı yoksa: `{{title}}`
- Başlık yoksa: `no audio info`

Maksimum 60 karakter ile kısalt.

### Yaş ve tarih
- `{{AGE_DAYS}}` = `uploadedAt` unix ile şimdiki zaman arasındaki gün farkı (tam sayı).
  - 0 ise: `today`
  - 1 ise: `1 day ago`
  - 2 ve üzeri: `{{N}} days ago`
- `{{UPLOADED_AT_FORMATTED}}` = insan tarafından okunabilir, örn. `April 8, 2026`

### Satır genişlikleri
Her ayırıcı (`===` veya `---`) tam olarak 80 karakterdir.

Transkript gövde metni SARMALANMAZ; doğal akışına bırak. Aşağı akış becerisi metni ayrıştırır; metin sarmalama cümle yeniden yapılandırmayı bozar.

### HTML kaçış
Yok. Düz metin. Tüm karakterleri olduğu gibi geçir. Yalnızca kontrol karakterlerini sıyır (`\x00` ile `\x1F` arası, `\n` ve `\t` hariç).

### Em-dash veya tire ayırıcı yok
Kullanıcı tercihi: cümle ayırıcısı olarak em-dash veya tire asla kullanma. Virgül, nokta veya satır sonu kullan.

**İzin verildi:** `pay-per-use`, `well-known`, `on-niche` gibi bileşik kelimeler.
**Yasak:** `Real hooks, real transcripts, ready to use.` (em-dash)
**Yasak:** `Real hooks, real transcripts - ready to use.` (cümle ayırıcısı olarak tire)

## Sıralama

Kazananlar şu sırayla gösterilir: `alaka AZALAN, final_score AZALAN`. En yüksek alaka üstte. Eşitlikler puanlama ile bozulur.

`build_swipe.py` yazmadan önce bellekte sıralar.

## Dosya konumu

Yapı betiği, proje başına kökü `--output-dir` aracılığıyla alır ve yalnızca o kök altına yazar. `~/Desktop`'a hiçbir zaman dokunmaz. Windows'ta OneDrive Bilinen Klasör Taşıma etkinleştirilmişse, swipe dosyası her zaman Claude Code'u açtığın proje klasörüne düşer; asla OneDrive'la eşitlenen bir ev yönlendirmesine değil.

```
$RFLAB/05_UGC/scraper/<niche-slug>/ugc-winners-v2-<YYYY-MM-DD>.txt
```

Alt dizin oluşturulamazsa şuna geri dön:

```
$RFLAB/05_UGC/scraper/ugc-winners-v2-<YYYY-MM-DD>-<niche-slug>.txt
```

## Tipik dosya boyutu

Transkript uzunluğuna bağlı olarak 40 KB ile 80 KB arası. Herhangi bir bağlam sınırının çok altında.
