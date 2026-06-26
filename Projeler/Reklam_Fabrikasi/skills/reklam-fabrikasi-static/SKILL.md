---
name: reklam-fabrikasi-static
description: "Kullanıcı statik reklam oluşturmak, statik reklam iş akışını çalıştırmak veya bir sonraki yayınlanacağı araştırmak istediğinde bu beceriyi kullan. /create static ads, /static, /static ads, /static research, /static concepts, /generate static, /new statics komutlarında ya da 'statik reklam yapmak istiyorum', 'hangi staticleri yayınlamalıyız', 'statik reklam fikirleri bul', 'bir sonraki statik reklam konseptlerimi hazırla' gibi ifadelerde tetikle. Beceri, Apify aracılığıyla markanın son 20 canlı Meta reklamını çeker, Marka DNA'sı ve VOC belgelerini tarar, web aramasıyla Kreatif Araştırma ve Strateji Motoru'nu çalıştırır, 6 ile 10 arasında kanıta dayalı konsepti sohbette düz metin olarak sunar ve onayla/reddet/düzenle seçeneği sunar, ardından onaylanan her konsept için 5 sabit görsel ailesinde tam 5 GPT Image 2 render promptu yazar. GPT Image 2 olarak sabitlenmiştir. Yol A manuel yapıştırma, Yol B Higgsfield CLI, Yol C fal.ai direkt (fal-ai-prerun-check kapısıyla korunur), Yol D Playwright web arayüzü."
---

# Reklam Fabrikası, Statik Reklam Konseptleri ve Render Promptları

Bu beceri v1 "40 statik şablon" iş akışının yerini alır. Yeni akış kanıt odaklıdır: markanın kendi canlı reklamlarını çek, Marka DNA'sı ve VOC'u tara, 8 sıkı kısıtlamayı geçen konsept adayları üretmek için web aramasıyla tek bir LLM çağrısı yap, kullanıcının onaylamasına izin ver, ardından onaylanan her konsept için 5 sabit görsel ailesinde 5 GPT Image 2 promptu yaz.

Kullanıcı iki kez etkileşime girer. Bir kez girdileri vermek için, bir kez de motora göre konseptleri onaylamak, düzenlemek veya reddetmek için. Geri kalan her şey sessizdir.

GPT Image 2 tek modeldir. Model seçici yoktur.

---

## Adım 0a, Proje çıktı klasörünü belirle

Çıktılar Claude Code'un açık olduğu çalışma klasörüne kaydedilir. Önce şu Bash bloğunu çalıştır:

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
  mkdir -p "$TARGET/04_Static_Ads/_scratch" "$TARGET/04_Static_Ads/path_b_outputs" "$TARGET/04_Static_Ads/path_c_outputs" "$TARGET/04_Static_Ads/path_d_outputs" "$TARGET/_meta"
  echo "READY:$TARGET"
fi

# Marka klasörü mevcutsa ve dosya yoksa marka hafızasını (CLAUDE.md) başlat.
# Yapılacak bir şey yoksa sessiz ve tekrar çalışmaya uygun şekilde çalışır.
if [ -d "$TARGET" ] && [ -n "${CLAUDE_PLUGIN_ROOT:-}" ] && [ -f "$CLAUDE_PLUGIN_ROOT/scripts/seed-claude-md.sh" ]; then
  bash "$CLAUDE_PLUGIN_ROOT/scripts/seed-claude-md.sh" >/dev/null 2>&1 || true
fi
```

- `PROTECTED:<path>`: Reddet ve kullanıcıya Claude Code'u markaya özel bir alt klasörde açmasını söyle. Dur.
- `FIRSTRUN:<path>`: "Çıktıları `<path>/` konumuna kaydedeceğim. Bu klasöre ilk kez kaydediyorum, doğru mu? (evet/hayır)" diye sor. Evet yanıtı gelirse klasörleri oluştur (`04_Static_Ads` altında `_scratch`, `path_b_outputs`, `path_c_outputs`, `path_d_outputs` dahil) ve `<path>/_meta/folder-confirmed.flag` dosyasını yaz. Hayır yanıtı gelirse dur.
- `READY:<path>`: Sessizce devam et.

Belirlenen yolu `$RFLAB` olarak kaydet. Aşağıdaki tüm çıktılar için bunu kullan.

---

## Adım 0b, Apify bağlantı kontrolü

`../_shared/apify-brand-ads-scrape.md` dosyasını yükle ve A.0 adımını çalıştır. Apify bağlı değilse paylaşılan belge `/reklam-fabrikasi:setup-apify` yönlendirmesini halleder ve beceriyi durdurur. Apify bağlıysa Adım 1'e sessizce devam et.

---

## Adım 1, Girdiler

Kullanıcıya şu mesajı tam olarak gönder:

> Statik reklam iş akışı. Markanızın son 20 canlı Meta reklamını çekeceğim, Marka DNA'nızı ve VOC'unuzu tarayacağım, Kreatif Araştırma ve Strateji Motoru'nu çalıştıracağım ve onaylamanız için 6 ile 10 arasında konsept sunacağım. Onay sonrasında her konsept için 5 görsel ailesinde 5 GPT Image 2 render promptu yazarım.
>
> İhtiyacım olan beş şey:
>
> 1. Marka DNA'sı belgesi. Dosyayı yükleyin veya tam metni yapıştırın.
> 2. VOC araştırma belgesi. Dosyayı yükleyin veya tam metni yapıştırın.
> 3. Marka Facebook Sayfa URL'si veya Sayfa ID'si. Son 20 canlı Meta reklamınızı çekmek için kullanılır.
> 4. Ürün görselleri. Ürünün 1 veya daha fazla referans fotoğrafını yükleyin.
> 5. İsteğe bağlı brifing. Kampanya hedefi, mevcut teklif, coğrafi bölge, kitle geçersiz kılma, fiyat noktası, mevsimsel bağlam gibi konulardan herhangi birini kapsayan kısa bir paragraf. Bunların hiçbiri bu çalıştırma için önemli değilse "atla" yazın.

Devam etmeden önce beş girdinin tamamını (veya brifing için "atla") bekle. İlk dördünden herhangi biri eksikse yalnızca eksik alanlar için bir kez daha sor.

Yeniden sormadan önce otomatik keşif: `$RFLAB/01_VOC_Research/` ve `$RFLAB/02_Brand_DNA/` klasörlerini en son dosyalar için tara. Bulunursa kullanıcıya sun:

```
ls -t "$RFLAB/01_VOC_Research/"*.html "$RFLAB/01_VOC_Research/"*.md 2>/dev/null | head -n 1
ls -t "$RFLAB/02_Brand_DNA/"*.html "$RFLAB/02_Brand_DNA/"*.md 2>/dev/null | head -n 1
```

Hangi dosyaların bulunduğunu kullanıcıya söyle ve yalnızca hâlâ eksik olan girdileri iste. Sayfa URL'si, ürün görselleri ve isteğe bağlı brifing her çalıştırmada ayrıca verilmelidir.

Kaydet:
- `$BRAND_DNA` (metin içeriği)
- `$VOC` (metin içeriği)
- `$PAGE_INPUT` (URL veya Sayfa ID'si)
- `$PRODUCT_IMAGES` (yerel dosya yollarının listesi)
- `$BRIEF` (paragraf veya boş)

---

## Adım 2, Markanın son 20 canlı reklamını çek

`../_shared/apify-brand-ads-scrape.md` dosyasını yükle ve şu değişkenlerle A.1'den A.7'ye kadar adımları çalıştır:

- `{{COUNT}}` = 20
- `{{COUNTRY_UPPER}}` = `$BRIEF` bir coğrafi bölge belirtiyorsa oradan türetilir, yoksa varsayılan `US`
- `{{ACTIVE_STATUS}}` = `active`
- `{{SORT_BY}}` = `impressions_desc`
- `{{MEDIA_TYPE}}` = `image` (statik filtresi A.6'da uygulanır)

Paylaşılan belge Sayfa ID'sini pages-scraper üzerinden çözer, sonucu doğrular, `view_all_page_id={PAGE_ID}` ile reklamları çeker, kirlilik kontrolü yapar, statik filtresini uygular ve normalleştirilmiş reklam listesini hafızaya döndürür.

Gönderimden önce kullanıcıya söyle:

> Meta Reklam Kütüphanesi'nden son 20 canlı statik reklamınız çekiliyor. Bu işlem 60 ile 180 saniye arasında sürebilir.

### Sıfır reklam durumu

Paylaşılan belge sıfır reklam döndürürse (statik filtresi uygulandıktan sonra) dur ve kullanıcıya yalnızca şu soruyu sor:

> Bu marka için canlı statik reklam bulamadım. Bunun yerine 1 ile 3 rakip analiz etmemi ister misiniz? Rakip marka adlarını veya Facebook URL'lerini virgülle ayırarak yazın ya da yalnızca Marka DNA'nız ve VOC'unuzla devam etmek için "hayır" yazın.

Bir yanıt bekle.

- Kullanıcı rakip adları veya URL'ler verirse her biri için (en fazla 3) paylaşılan belgeyi aynı değişkenlerle tekrar çalıştır. Sonuçları tek bir birleşik reklam kümesinde birleştir. Strateji motorunun her reklamın hangi markaya ait olduğunu bilmesi için her reklamı `source_brand` etiketiyle işaretle.
- Kullanıcı "hayır" (veya rakip listesi olmayan herhangi bir şey) yazarsa boş bir reklam kümesiyle devam et. Strateji motoru yalnızca Marka DNA'sı, VOC ve isteğe bağlı brifingden çalışır. Motorun marka reklam sinyal katmanının eksik olduğunu bilmesi için bunu hafızaya kaydet.

Rakipleri otomatik olarak araştırma. Kullanıcı kendi rakiplerini bir web aramasından daha iyi bilir.

---

## Adım 3, Normalize et, puanla, etiketle ve taslak dosyasını yaz

Adım 2'den döndürülen her reklam için sessizce normalize et ve etiketle. Hesapla:

- `days_active` = bugün eksi `start_date` (hem unix epoch hem ISO tarih formatını işle)
- `variant_count` = aynı ad_archive_id altındaki farklı kreatif varyant sayısı
- `scoring_tier`:
  - PROVEN: `is_active=true` VE `days_active >= 60`
  - HOT: `is_active=true` VE `days_active >= 21`
  - ACTIVE: `is_active=true` VE `days_active < 21`
  - RETIRED: `is_active=false` VE `days_active >= 60`
  - SHORT_RUN: `is_active=false` VE `days_active < 60`

Her reklam için kreatif ve metinden şu etiketleri türet:

- `angle` (sorun, arzu, kimlik, sosyal kanıt, karşılaştırma, mekanizma, teklif, yaşam tarzı)
- `visual_format` (ürün hero, sorun durumu, sonuç durumu, kanıt veya mekanizma, kimlik veya sosyal kanıt, ugc native, karşılaştırma split, liste veya stat kartı)
- `hook_style` (merak boşluğu, cesur iddia, örüntü kırma, yakınlık kurma, sosyal kanıt, korku veya kayıp, özlem, sorun kışkırtma, doğrudan teklif)
- `copy_length` (yalnızca kısa başlık, alt başlıklı orta, gövde metinli uzun)

Normalleştirilmiş kümeyi taslağa yaz:

```
$RFLAB/04_Static_Ads/_scratch/brand-ads-$(date -u +%Y%m%d).json
```

Bugünün taslak dosyası zaten varsa üzerine yaz. Eski taslak dosyaları önceki çalıştırma geçmişi için kalır.

Taslak dosyası şeması:

```json
{
  "scrape_date": "YYYY-MM-DD",
  "brand_slug": "<slug>",
  "page_id": "<id>",
  "country": "<COUNTRY_UPPER>",
  "ad_count": <int>,
  "ads": [
    {
      "ad_archive_id": "...",
      "page_name": "...",
      "is_active": true,
      "start_date": "...",
      "days_active": 87,
      "variant_count": 3,
      "scoring_tier": "PROVEN",
      "source_brand": "<brand_slug>",
      "snapshot": { "title": "...", "body": "...", "cta_text": "...", "images": [...], "cards": [...] },
      "tags": {
        "angle": "...",
        "visual_format": "...",
        "hook_style": "...",
        "copy_length": "..."
      }
    }
  ]
}
```

Kullanıcı bu dosyayı hiç görmez. Aynı markanın bu becerinin gelecek çalıştırmaları için öğrenme döngüsüdür.

---

## Adım 4, Kanıt bankasını oluştur

Hafızada şunları topla:

1. `$BRAND_DNA` (tam metin)
2. `$VOC` (tam metin)
3. Adım 3'teki normalleştirilmiş reklam kümesi (etiketler ve puanlama kademeleriyle birlikte 20 reklam)
4. `$PRODUCT_IMAGES` (açıklamalar, yüklenen her görselden etiket metni dahil)
5. `$BRIEF` (paragraf veya boş)
6. Önceki çalıştırma geçmişi. Bugününkü hariç `$RFLAB/04_Static_Ads/_scratch/brand-ads-*.json` eşleşen tüm dosyaları oku. Hepsini tarihsel bağlam olarak kanıt bankasına ekle. Motor, markanın zaman içinde neyi denediğini, emekliye ayırdığını ve yeniden başlattığını tespit etmek için önceki çalıştırmaları kullanır.

Bağlamı dar tutmak için önceki geçmişi en son 5 taslak dosyayla sınırla.

---

## Adım 5, Kreatif Araştırma ve Strateji Motoru'nu çalıştır

Tam motor sistem promptu için `references/strategy-engine-prompt.md` dosyasını yükle.

Web araması etkinleştirilmiş şekilde TEK bir LLM çağrısı yap. Adım 4'teki kanıt bankasını kullanıcı mesajı yükü olarak geçir. Motor dahili olarak:

1. Marka örüntü haritasını, müşteri gerçek haritasını, aynılık denizi haritasını ve beyaz alan haritasını oluşturur.
2. Web aramasıyla yeni pazar araştırması yapar (güncel kültürel anlar, ortaya çıkan dil, yeni rekabetçi açılar, mevsimsel bağlam).
3. 8 sıkı kısıtlamayı (4 küme düzeyi, 4 konsept başına) geçen 6 ile 10 arasında konsept üretir.
4. Her konsepti dahili olarak ONAYLA, REVIZE ET veya REDDET olarak işaretler. Revizyonları bir kez döndürür.
5. Döndürmeden önce küme düzeyinde denetim yapar. Küme düzeyi kısıtlamalarını karşılamak gerekirse konseptleri değiştirir.
6. Yalnızca yüzeylenen konseptleri motor promptunda tanımlanan tam formatta düz metin olarak döndürür.

Kullanıcı haritaları, reddedilen adayları veya dahili puanlamayı hiç görmez.

Gönderimden önce kullanıcıya söyle:

> Strateji motoru çalıştırılıyor. Bu işlem 45 ile 90 saniye arasında sürebilir.

Motor döndüğünde yüzeylenen konsept bloklarını kaydet. Her blokta 9 alan vardır: konsept adı, büyük fikir, farkındalık aşaması, kanca, hedef persona, VOC alıntısı, görsel yön, başlık adayları, neden işe yaramalı.

---

## Adım 6, Konseptleri düz metin olarak sun

Yüzeylenen konsept bloklarını doğrudan sohbette yazdır. HTML yok, dosya yok, giriş yok, özet yok. Motorun döndürdüğünü tam olarak düz metin biçiminde yazdır.

Son konsept bloğundan sonra tek kısa bir prompt ekle:

> Her konsepti onaylayın, reddedin veya düzenleyin. Her konsept için virgülle ayrılmış şekilde şu biçimlerde yanıt verin:
>
> - "onayla 1, 3, 5"
> - "reddet 2, 4"
> - "düzenle 6: kanca açısını daha saldırgan yap"
> - "tümünü onayla"
> - "tümünü reddet"
>
> Aynı yanıtta onayla, reddet ve düzenle'yi karıştırabilirsiniz. Düzenlemeler konsepti revize eder ve yeni bir karar için yeniden sunar.

---

## Adım 7, Kullanıcı onay döngüsü

Kullanıcının yanıtını ayrıştır. Her konsept için:

- **onayla**: QA kapısı için işaretle (Adım 8).
- **reddet**: Sessizce bırak.
- **düzenle**: Konsept bloğunu ve kullanıcının düzenleme notunu strateji motoru revizyon çağrısına gönder (`references/strategy-engine-prompt.md` içinde "Revizyon çağrısı" bölümü). Motor düzenlenmiş bir konsept bloğu döndürür (veya düzenleme bir kısıtlamayı kıracaksa `REFUSE: <gerekçe>` satırı). Düzenlenen konsepti yeniden sun ve kullanıcıdan tekrar onaylamasını, reddetmesini veya düzenlemesini iste.

Tüm özgün konseptler bir son duruma (onaylandı, reddedildi veya bırakıldı) ulaşana kadar döngüyü sürdür. Düzenlenen bir konsept `REFUSE:` alırsa reddetme satırını kullanıcıya yazdır ve konsepti bırakmak mı yoksa farklı bir düzenleme notu vermek mi istediğini sor.

Döngü bittiğinde onaylanan kümeyi Adım 8'e taşı. Sıfır konsept onaylandıysa kullanıcıya söyle:

> Hiçbir konsept onaylanmadı. Çalıştırma burada sona eriyor. Aynı girdilerle yeni bir küme oluşturmak için beceriyi istediğiniz zaman yeniden çalıştırın.

Ve dur.

---

## Adım 8, QA kapısı

`references/qa-gate-checks.md` dosyasını yükle. Onaylanan her konsept üzerinde (düzenleme sonrası onaylanan revize konseptler dahil) 6 kontrolün tamamını çalıştır.

Kontroller sessizce çalışır. 6 kontrolün tamamını geçen konseptler Adım 9'a mesaj verilmeden geçer. Herhangi bir kontrolde başarısız olan konseptler kullanıcıya eşleşen tek satırlık başarısız mesajıyla geri sunulur. Kullanıcı başka bir düzenleme notu ile revize eder (Adım 7 revizyonuna yönlendirilir) ya da konsepti bırakır.

Her onaylanan konsept ya QA'dan geçene ya da bırakılana kadar döngüyü sürdür. QA'dan geçen konseptler Adım 9'a gider.

---

## Adım 9, Görsel prompt üretimi

`references/visual-families.md` dosyasını yükle. QA'dan geçen her konsept için tam 5 render promptu üret: her görsel aile için bir tane (Product Hero, Problem State, Outcome State, Proof or Mechanism, Identity or Social Proof). Her prompt, altındaki sabit kısıtlamalar satırıyla birlikte 10 satırlık evrensel yapıyı izler.

9. satır için başlığı konseptin 3 başlık adayından al. Aynı konseptin farklı varyantları aday listesinden farklı başlıklar kullanabilir, ancak her başlık kullanıcının daha önce gördüğü adaylardan biri olmalıdır.

Düzenleme geçiş promptları yok. Varyant başına tek güçlü render promptu.

---

## Adım 10, Final çıktıyı düz metin olarak yazdır

QA'dan geçen her konsepti ve 5 varyant promptunu doğrudan sohbette yazdır. Şu tam düzeni kullan:

```
APPROVED CONCEPT 1: <konsept adı>

VARIANT 1.1, Product Hero
1. Intent. <doldurulmuş>
2. Subject. <doldurulmuş>
3. Action or pose. <doldurulmuş>
4. Environment. <doldurulmuş>
5. Composition. <doldurulmuş>
6. Lighting. <doldurulmuş>
7. Style and medium. <doldurulmuş>
8. Mood and color. <doldurulmuş>
9. Text. <doldurulmuş>
10. Constraints. <sabit kısıtlamalar satırı>

VARIANT 1.2, Problem State
<10 satır>

VARIANT 1.3, Outcome State
<10 satır>

VARIANT 1.4, Proof or Mechanism
<10 satır>

VARIANT 1.5, Identity or Social Proof
<10 satır>

---

APPROVED CONCEPT 2: <konsept adı>
<aynı yapı, 5 varyant>

(QA'dan geçen her konsept için devam et)
```

HTML yok, dosya yok. Sohbetteki düz metin teslimat ürünüdür.

Son konseptin son varyantından sonra kayıtlar için diske bir kopya kaydet:

```
$RFLAB/04_Static_Ads/static-concepts-<YYYY-MM-DD>.txt
```

Dosya sohbet çıktısıyla aynıdır. Kullanıcı daha sonra `/open-folder` aracılığıyla erişebilir.

---

## Adım 11, Yol seçici

Kullanıcıya yol sorusunu sor:

> Konseptleriniz ve render promptlarınız hazır. Görselleri nasıl üretmek istersiniz?
>
> **A. Manuel yapıştırma.** Ücretsiz. Yukarıdaki sohbetten herhangi bir promptu kopyalayın ve GPT Image 2 seçili kendi ChatGPT oturumunuza yapıştırın. Ürün görselinizi ekleyin. Oluştur'a tıklayın.
> **B. Higgsfield MCP.** Higgsfield aboneliğiniz varsa en iyi seçenek. İlk kullanımda tek seferlik OAuth girişi. Görselleri Higgsfield hesabınız üzerinden oluştururum.
> **C. Fal.ai ücret başına sonuç.** Abonelik gerekmez. Üretim başına ödeme. `fal_api_key` gerektirir. Yüksek kalite ve 4K'da görsel başına yaklaşık 0,15 dolar.
> **D. Playwright aracılığıyla web arayüzü otomasyonu.** https://chatgpt.com/ adresini sizin için yönetirim, her promptu yapıştırır, ürün görselini ekler, Oluştur'a tıklarım. Her adımda açık onay gerektirir.
>
> A, B, C veya D yazın. Ya da promptları sohbette bırakmak için "bitti" yazın.

Açık bir seçim bekle. Ardından yalnızca o yolu çalıştır. Aynı prompt kümesi için asla iki yolu paralel olarak çalıştırma.

Kullanıcı "bitti" seçerse onayla ve dur. Promptlar zaten sohbette ve diske kaydedilmiş durumda.

---

### Yol A, Manuel yapıştırma

Kullanıcı A seçerse otomatik hiçbir şey yapma.

Kullanıcıya söyle:

> https://chatgpt.com/ adresini açın. Görsel oluşturucuyla yeni bir sohbet başlatın ve modeli yüksek kalitede GPT Image 2 olarak ayarlayın. Her VARIANT bloğunu (1'den 10'a kadar satırlar) teker teker yapıştırın, ürün görselinizi ekleyin, Oluştur'a tıklayın. Çıktı görsellerini ilerledikçe mevcut en büyük 1:1 boyutunda kaydedin.

Kullanıcı bittiğini onayladığında kabul et.

---

### Yol B, Higgsfield MCP

Yol B, her varyantı Claude Code içinden doğrudan Higgsfield CLI aracılığıyla oluşturur. Kullanıcıya görünen etiket `Yol B, Higgsfield MCP` olarak kalır. Altta Yol B, `@higgsfield/cli@^0.1` üzerinden çalışır. CLI aynı Higgsfield hesabını, aynı kredileri, aynı modelleri kullanıma sunar.

`../_shared/path-b-cli-implementation.md` dosyasını yükle ve şu değişkenlerle B.0'dan B.9'a kadar adımları izle:

- `{{SKILL_SLUG}}`: `static`
- `{{MODEL_ID}}`: `gpt_image_2`
- `{{ASPECT}}`: `1:1`
- `{{QUALITY}}`: `high`
- `{{RESOLUTION}}`: `4k`
- `{{OUTPUT_DIR}}`: `$RFLAB/04_Static_Ads/path_b_outputs`
- `{{OUTPUT_FILENAME}}`: `concept_<C>_variant_<V>.png` (burada `<C>` konsept numarası, `<V>` 1'den 5'e kadar varyant numarasıdır)
- Referans varlıklar: `$PRODUCT_IMAGES`'dan ilgili ürün görseli, kullanıcının sağladığı sırayla

**Alt küme seçici (B.5 prompt numarası sorusunun yerine).** Kullanıcıya söyle:

> <N> konseptim ve toplam <N çarpı 5> varyantım hazır. Hangilerini oluşturmamı istersiniz? Konsept-varyant çiftlerini virgülle ayırarak yazın. Örnek: "generate 1.1, 1.3, 2.4". Ya da her varyantı çalıştırmak için "all concepts", yalnızca bir konseptin tüm varyantları için "concept 1" yazın.

Açık bir liste bekle. Her çiftin gerçek bir konsept ve varyant olduğunu doğrula.

**Onay kapısı (B.5).**

> Higgsfield üzerinden <liste> kullanılarak K varyant oluşturuluyor. Üretim başına maliyet: <B.4'teki krediler>. Toplam: <K çarpı üretim başına> kredi. Mevcut bakiye: <B.3'teki krediler>. Devam etmek için `yes` yazın.

**Paralel gruplar (B.7).** 5 veya daha fazla varyant için Bash aracının `run_in_background` parametresiyle üretim komutlarını paralel olarak çalıştır. Test edilen tavan Higgsfield çalışma alanı başına 8 paralel iştir.

**Manifest (B.9).** Kullanıcının istediği her çift için `{{OUTPUT_DIR}}` ve `concept_<C>_variant_<V>.png` dosya adından oluşan `output_path` ile paylaşılan belgedeki standart şema.

Eski MCP araç adları (`mcp__higgsfield__balance`, `mcp__higgsfield__generate_image` vb.) artık kullanılmıyor. CLI, `/mcp` artı Clerk yerine `higgsfield auth login` aracılığıyla OAuth akışını yönetiyor.

---

### Yol C, Fal.ai direkt API

**Önce kapı.** Herhangi bir Yol C işleminden önce `fal-ai-prerun-check` koruma becerisini çalıştır. `fal_api_key`'nin `pluginConfigs["reklam-fabrikasi"]`'nde mevcut olup olmadığını ve fal-ai MCP'nin erişilebilir olup olmadığını doğrular. Koruma eksik veya geçersiz kimlik bilgisi bildirirse kullanıcıyı `/reklam-fabrikasi:setup-fal-ai` adresine yönlendirir ve durur. Kapıyı atlatma.

Kapı geçildiğinde devam et.

**Adım adım:**

1. **fal-ai MCP bağlantısını doğrula.** `mcp__fal-ai__*` araçlarını ara. Kapı geçilmesine rağmen mevcut değilse, kullanıcıya MCP'nin anahtarı alabilmesi için Claude Code'u yeniden yüklemesini söyle.

2. **Ürün görsellerini bir kez fal'a yükle.** `$PRODUCT_IMAGES`'daki her görsel için `mcp__fal-ai__upload_file` çağır. Döndürülen URL'leri `$PRODUCT_URLS` olarak kaydet.

3. **Alt küme seçici.** Yol B ile aynı ifade. Konsept-varyant çiftlerinin açık listesini al.

4. **Maliyet onayı.** GPT Image 2 yüksek kalite ve 1:1 4K'da görsel başına yaklaşık 0,15 dolar teklif et. Kullanıcının seçtiği çift sayısıyla çarp. "Devam edilsin mi? (yes/no)" diye sor. "yes" bekle.

5. **Her çift için `mcp__fal-ai__run_model` çağır:**

   - `model`: `"openai/gpt-image-2/edit"`
   - `prompt`: tam 10 satırlık varyant promptu düz metin olarak
   - `image_urls`: `$PRODUCT_URLS`
   - `image_size`: `{"width": 2880, "height": 2880}` (1:1, fal.ai'nin GPT Image 2 endpoint'inin 8,3 megapiksel sınırı altında kabul ettiği en büyük 1:1 boyut)
   - `quality`: `"high"`
   - `output_format`: `"png"`
   - `num_images`: 1

   `safety_tolerance` GEÇİRME. GPT Image 2'de endpoint bunu reddeder.

   Döndürülen görsel URL'sini `$RFLAB/04_Static_Ads/path_c_outputs/concept_<C>_variant_<V>.png` konumuna kaydet.

6. **İlerlemeyi bildir.** Her 5 üretimden sonra kullanıcıya "N'nin 5'i tamamlandı. Devam edilsin mi? (yes/stop)" söyle.

7. **Final teslimat.** Her çifti, promptunu, görsel yolunu ve toplam harcamayı listeleyen bir manifest yaz: `$RFLAB/04_Static_Ads/path_c_outputs/manifest.json`.

---

### Yol D, Playwright MCP ChatGPT'yi yönetir

Yol D, GPT Image 2 seçili https://chatgpt.com/ adresini yönetmek için Playwright MCP sunucusunu kullanır.

**Sıkı kurallar:**

1. **Medya hiçbir zaman otomatik yükleme.** Her dosya yüklemesi açık "yes yükle" onayı gerektirir.
2. **Onay olmadan Oluştur'a asla tıklama.** Her Oluştur tıklaması açık "yes git" onayı gerektirir.
3. **Bir seferde bir varyant.** Toplu işlem yok.

**Adım adım:**

1. **Playwright MCP'nin erişilebilir olduğunu doğrula.** `playwright` bağlı değilse kullanıcıya `/reklam-fabrikasi:doctor` çalıştırmasını söyle ve dur.

2. **ChatGPT'yi aç.** https://chatgpt.com/ adresine gitmek için `mcp__playwright__browser_navigate` kullan. Kullanıcı giriş yapmamışsa manuel olarak giriş yapmasını ve bittiğinde onaylamasını iste. KİMLİK BİLGİSİ YAZMA.

3. **Modeli seç.** Görsel oluşturucunun GPT Image 2 seçili ve kalitesi yüksek olarak seçildiğinden emin ol.

4. **Kullanıcının çalıştırmak istediği her çift için (N'nin 1'i):**
   a. **Kullanıcıya** hangi çiftin çalıştırılmak üzere olduğunu söyle.
   b. **Varyant promptunu** `browser_type` aracılığıyla giriş alanına yapıştır.
   c. **Ürün görseli hakkında sor.** "Bu prompta ürün görselini ekleyeyim mi? (yes/skip)". Evet ise yolu ile `browser_file_upload` kullan.
   d. **Oluştur'u onayla.** "Şimdi Oluştur'a tıklayayım mı? (yes/no)". "yes" bekle. Ardından Oluştur için `browser_click`.
   e. **Bekle** görsel render edilene kadar. `browser_take_screenshot` kullan ve `$RFLAB/04_Static_Ads/path_d_outputs/concept_<C>_variant_<V>.png` konumuna kaydet.
   f. **Bir sonraki çifte geç.**

5. **Final teslimat.** Her çifti ve görsel yolunu listeleyen bir manifest yaz: `$RFLAB/04_Static_Ads/path_d_outputs/manifest.json`.

---

## Dört yolda geçerli sıkı kurallar

- **Asla sessizce yol değiştirme.** Kullanıcı bir yol seçtiyse ve bir eylem başarısız olursa yeniden denemek, A'ya (manüel) geçmek veya vazgeçmek isteyip istemediğini sor. Başka bir ücretli yola izinsiz otomatik geri dönme.
- **Yol B ve Yol C için modeli çağırmadan önce her zaman maliyeti göster.**
- **Açık `yes` onayı olmadan Higgsfield kredisi veya fal.ai ücreti yükleme.** Tek bir test çalıştırması bile olsa.
- **Her çıktıyı diske kaydet** `$RFLAB/04_Static_Ads/path_X_outputs/` altına.

---

## Çıktı doğrulaması

Bu beceriyi tamamlandı ilan etmeden önce şunları doğrula:

1. Sohbet çıktısı, tam 10 satırlık yapıda 5 varyantın tamamıyla QA'dan geçen her konsepti içeriyor.
2. `$RFLAB/04_Static_Ads/static-concepts-<YYYY-MM-DD>.txt` konumundaki disk kopyası mevcut ve boş değil.
3. Her varyant promptu tam 10 satır, sabit sırada, kısıtlamalar satırı 10. satır olarak.
4. Her varyant `$PRODUCT_IMAGES`'dan gerçek bir ürüne referans veriyor.
5. 9. satırda kullanılan her başlık, konseptin yüzeylenen bloğundaki 3 adaydan biri.
6. Hiçbir varyanda yer tutucu kalmamış (`<doldurulmuş>`, `<TODO>`, `lorem ipsum` yok).
7. `$RFLAB/04_Static_Ads/_scratch/brand-ads-<YYYYMMDD>.json` konumundaki taslak dosyası mevcut ve çekilen reklam kümesini içeriyor.
8. Bir yol seçildiyse (B, C veya D) ilgili `path_X_outputs/` klasörü beklenen görselleri ve bir manifestı içeriyor.

Doğrulama başarısız olursa:

1. Önce otomatik düzeltmeyi dene:
   - Bir varyant satır eksikse veya satırlar yanlış sıradaysa o varyantı yeniden yaz.
   - Bir başlık 3 adaydan biriyle eşleşmiyorsa bir adayla değiştir.
   - Yer tutucular kalıyorsa konsept bloğundan, Marka DNA'sından ve VOC'tan doldur.

2. Otomatik düzeltme başarısız olursa kullanıcıya dürüst bir rapor sun:
   "Statik: Konseptleri ve varyant promptlarını ürettim ancak doğrulama <sorun> gösterdi. <düzeltme girişimi> denedim ve bu <işe yaramadı / kısmen işe yaradı>. Tam sonuç almak için:
   - Ürün görselinin okunabilir olduğunu onaylayın; böylece etiket doğruluğu kuralı geçerli kalır
   - Daha zengin bir VOC belgesi sağlayın; böylece birebir alıntılar temiz akar
   - Başarısız olan varyant numaralarını paylaşın, sadece onları yeniden oluşturayım."

---

## Sıkı kurallar, beceri düzeyi

| Kural | Detay |
|---|---|
| Yalnızca GPT Image 2 | Model seçici yok. Her varyant promptu GPT Image 2 hedefler. Nano Banana 2 bu beceride sunulmaz. |
| Apify zorunludur | Adım 2 her zaman paylaşılan Apify belgesinden geçer. Sıfır reklam rakip dalını tetikler, atlama değil. |
| Konsept başına 5 varyant | Tam 5. Her görsel aile için bir tane. Ne daha fazla ne daha az. |
| 10 satırlık evrensel yapı | Her varyant promptu tam 10 satır, sabit sırada, kısıtlamalar satırı 10. satır olarak. |
| Düz metin teslimat | Sohbet çıktısı artifakttır. Disk kopyası bir kayıttır, birincil teslimat değildir. HTML yok, dosya formatı müzakeresi yok. |
| QA kapısı revizyonlarda yeniden çalışır | Her revize edilmiş konsept 6 QA kontrolünün tamamından geçmelidir. "Zaten onaylandı" kısayolu yok. |
| Küme düzeyi kısıtlamalar motor tarafından uygulanır | Yüzeylemeden önce motor, 3+ farkındalık aşamasını, 1+ çirkin veya native'i, 1+ sosyal kanıt veya incelemeyi, açı+farkındalık+kanıt çakışmamasını onaylar. |
| Konsept başına kısıtlamalar motor ve QA kapısı tarafından uygulanır | VOC alıntısı birebir, marka reklam sinyali veya beyaz alan boşluğu, FTC 2024 uyumluluğu, klon değil evrimsel. |
| Önceki çalıştırma geçmişi öğrenme döngüsüdür | Her çalıştırma `_scratch/brand-ads-<YYYYMMDD>.json` yazar. Gelecekteki çalıştırmalar önceki taslak dosyalarını (en son 5'e kadar) ek bağlam olarak okur. |
| Em-dash veya cümle arası kısa çizgi yok | Virgül, "ve" kullan veya cümleleri böl. Eklentinin `enforce-no-dashes` kancası sızan herhangi birini kaldırır. |
| `openai/gpt-image-2` ve `openai/gpt-image-2/edit` `safety_tolerance` kabul etmez | Yol C bağlantısı bunu atlamalıdır. |

---

## Referans dosyaları

İş akışı sırasında talep üzerine yüklenir, önceden değil:

| Dosya | Ne zaman okunur |
|---|---|
| `../_shared/apify-brand-ads-scrape.md` | Adım 0b (bağlantı) ve Adım 2 (çekme) |
| `references/strategy-engine-prompt.md` | Adım 5 (motor çağrısı) ve Adım 7 (revizyon çağrısı) |
| `references/qa-gate-checks.md` | Adım 8 (konsept başına QA) |
| `references/visual-families.md` | Adım 9 (varyant üretimi) |
| `../_shared/path-b-cli-implementation.md` | Adım 11 kullanıcı Yol B seçerse |
