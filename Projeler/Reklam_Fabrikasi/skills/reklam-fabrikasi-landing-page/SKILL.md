---
name: reklam-fabrikasi-landing-page
description: "Bu beceriyi, kullanıcı kazanan bir Meta reklamını markalı ve yüksek dönüşümlü tek dosyalı HTML açılış sayfasına dönüştürmek istediğinde kullan. /reklam-fabrikasi:landing-page, /landing-page, /lp, /build landing page, /create landing page komutlarında ya da 'bu reklamdan açılış sayfası yap', 'bu reklamı açılış sayfasına çevir', 'reklamımla eşleşen sayfa oluştur', 'Meta reklamım için açılış sayfası lazım' gibi doğal dilde taleplerde tetikle. Bu beceri kullanıcının reklam kreatifini (görsel veya video karesi), 02_Brand_DNA/ klasöründeki en güncel Marka DNA belgesini ve 01_VOC_Research/ klasöründeki en güncel VOC belgesini alır; ardından Tailwind, CSS özellik değişkenleri olarak marka tokenları, Google Fonts içe aktarımı, VOC verilerinin sayfanın en kritik slotlarına birebir enjeksiyonu, reklam başlığıyla H1 arasında mesaj uyumu zorunluluğu, DTC için mobil yapışkan CTA, Meta Pixel iskeleti, FAQ JSON-LD şeması, 5 yorumlanmış A/B varyant bloğu ve çıktı öncesi 34 maddelik yapay zeka klişesi öz denetimi içeren tek, kendi kendine yeten bir HTML dosyası üretir. Açılış sayfası talepleri bir Meta reklamıyla ilgiliyse bu beceriyi her zaman tetikle. Genel web sitesi tasarımı, çok sayfalı siteler, gösterge panelleri veya e-posta tasarımı için tetikleme."
license: MIT
credits: "Anti slop tells adapted from awaken7050dev/anti-slop-ui (MIT). HTML scaffold pattern adapted from jezweb/claude-skills/landing-page (MIT). Design principles from anthropics/skills/frontend-design."
---

# Reklam Fabrikası, Açılış Sayfası Üreticisi

Kazanan bir Meta reklamını markalı, tek dosyalı HTML açılış sayfasına dönüştür. Mevcut proje klasöründen Marka DNA'sını, VOC'u ve reklam kreatifini okur; DTC ile potansiyel müşteri (lead gen) rotasını otomatik belirler; reklam başlığıyla H1 arasındaki mesaj uyumunu zorunlu kılar ve dosyayı yazmadan önce 34 yapay zeka klişesine karşı öz denetim uygular.

## Değişmez kural

Bu beceri TEK bir çıktı üretir: mevcut projenin `10_Landing_Pages/` klasörüne yazılan, kendi kendine yeten tek bir HTML dosyası. Meta MCP çağırmaz, hiçbir yere deploy etmez, Shopify veya Cloudflare'e push yapmaz. Kullanıcı deploy işlemini kendisi yapar. Becerinin işi dosyayı üretmek ve deployment için net bir devir notu sunmaktır.

## Bu becerinin var oluş nedeni

Eklentinin ilk on becerisi reklam kreatifleri üretir. Meta devir becerisi, canlı kampanya yönetimi için bir prompt üretir. Ancak reklamın trafiği gönderdiği hedef sayfayı gerçekten inşa eden hiçbir şey yoktur. Genel bir Shopify ürün sayfasına veya ana sayfaya yönlendirilen iyi bir reklam, mesaj uyumunu bozar ve dönüşümü eritir. Imprint LA karşılaştırması: Meta trafiği için özel açılış sayfaları yaklaşık yüzde 15 dönüşüm sağlarken ana sayfalar yüzde 1 ile 2 arasında kalır. Bu beceri o açığı kapatır.

Eklentinin `02_Brand_DNA/` altında yapılandırılmış Marka DNA'sı ve `01_VOC_Research/` altında birebir müşteri sesi (VOC) verisi zaten mevcuttur. Başka hiçbir açılış sayfası üreticisi bu kalitede girdiyle çalışamaz. VOC enjeksiyon haritası (bkz. `references/voc-injection-map.md`) bu becerinin rekabet avantajıdır. Sayfadaki her slotun hangi içerik türüne ev sahipliği yapacağı sabit kurallara bağlıdır: H1 reklam başlığını yansıtır, alt başlık cilalı bir müşteri sonucu taşır, sorun pekiştirme bir müşterinin birebir ağrı alıntısını ve nitelendirmeyi kullanır, SSS soruları pazarlamacının yeniden yorumlaması değil müşterinin tam ifadeleridir.

## Adım 0a: Proje çıktı klasörünü belirle

Çıktılar Claude Code'un açık olduğu çalışma klasörüne kaydedilir. Önce bu Bash bloğunu çalıştır:

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
  mkdir -p "$TARGET/10_Landing_Pages" "$TARGET/_meta"
  echo "READY:$TARGET"
fi

# Seed brand memory (CLAUDE.md) if the brand folder exists and the file
# is missing. Idempotent and silent when there is nothing to do.
if [ -d "$TARGET" ] && [ -n "${CLAUDE_PLUGIN_ROOT:-}" ] && [ -f "$CLAUDE_PLUGIN_ROOT/scripts/seed-claude-md.sh" ]; then
  bash "$CLAUDE_PLUGIN_ROOT/scripts/seed-claude-md.sh" >/dev/null 2>&1 || true
fi
```

- `PROTECTED:<path>`: Kullanıcıya reddet ve Claude Code'u markaya özel bir alt klasörde açmasını söyle. Dur.
- `FIRSTRUN:<path>`: "Açılış sayfasını `<path>/10_Landing_Pages/` konumuna kaydedeceğim. Bu klasöre ilk kez kayıt yapılıyor, doğru mu? (evet/hayır)" diye sor. Evet cevabında klasörleri oluştur ve `<path>/_meta/folder-confirmed.flag` dosyasını yaz. Hayır cevabında dur.
- `READY:<path>`: Sessizce devam et.

Belirlenen yolu `$RFLAB` olarak sakla. Nihai HTML'i şu konuma kaydet:

```
$RFLAB/10_Landing_Pages/landing-page-<YYYY-MM-DD-HHMMSS>.html
```

## Adım 0b: Önceki proje bağlamını otomatik keşfet

`ls`, `find` ve Read aracını kullanarak proje klasörünü girdiler için tara. Şu yollara bak ve var olan her şeyi yakala:

- `$RFLAB/01_VOC_Research/`: en güncel VOC araştırması çıktısı (HTML veya markdown). Zorunlu.
- `$RFLAB/02_Brand_DNA/`: en güncel Marka DNA belgesi. Zorunlu.
- `$RFLAB/04_Static_Ads/`, `$RFLAB/07_Multiplied_Ads/`, `$RFLAB/08_Rebuilt_Competitor_Ads/`: kullanıcının kaynak reklam olarak kullanmak isteyebileceği üretilmiş reklam çıktıları. İsteğe bağlı.
- `$RFLAB/06_Ad_Copy/`: en güncel kopya destesi. İsteğe bağlı. Mevcutsa ve kaynak reklamda okunabilir başlık metni yoksa başlıkları yedek olarak kullan.

Bir keşif özeti yazdır:

```
Bu projede bulunanlar:
- VOC: <dosya adı veya "EKSİK">
- Marka DNA'sı: <dosya adı veya "EKSİK">
- En son reklam çıktıları: <04, 07, 08'den dosya adlarını listele veya "henüz yok">
- Kopya destesi: <dosya adı veya "henüz yok">
```

VOC veya Marka DNA'sı EKSİK ise reddet ve kullanıcıya önce hangi kardeş beceriyi çalıştırması gerektiğini söyle:

- VOC yok: önce `/reklam-fabrikasi:voc` çalıştır.
- Marka DNA'sı yok: önce `/reklam-fabrikasi:brand-dna` çalıştır.

Eksik girdileri uydurma. Tüm beceri bu belgeler üzerine kurulu.

## Adım 1: Bilgi alma

Kullanıcıdan kaynak reklam kreatifini ve iki isteğe bağlı alanı iste:

> Bu klasördeki mevcut VOC ve Marka DNA'nı kullanarak açılış sayfasını oluşturacağım. Yalnızca bu sayfayla eşleştirilecek reklam kreatifine ihtiyacım var. Seçenekler:
>
> 1. Kazanan Meta reklamının görselini buraya yapıştır veya bırak.
> 2. `04_Static_Ads/`, `07_Multiplied_Ads/` veya `08_Rebuilt_Competitor_Ads/` içinde bulduğum dosyalardan birine dosya adıyla başvur.
> 3. Görsel yoksa reklamı 2-3 cümleyle tanımla.
>
> İki isteğe bağlı soru (girdilerinden belli oluyorsa atla):
> a. Birincil CTA'nın bağlandığı hedef URL (DTC için "Şimdi Satın Al" hedefi, lead gen için form işleyici URL).
> b. DTC ise Ortalama Sipariş Değeri; lead gen ise aramanın veya potansiyel müşterinin değeri.

Reklam kreatifinini ve cevapları bekle. Reklam kreatifsiz devam etme.

## Adım 2: Reklam kreatifl analizi

Bu adım fark yaratandır. Diğer açılış sayfası üreticileri bu adımı atlayarak mesaj uyumunu bozar. Atlatma.

Kullanıcı görsel bıraktıysa görme yeteneğini kullan. `04_`, `07_` veya `08_` klasöründeki bir dosyaya başvurduysa oku (dosya prompt ve beklenen kreatifi içerir; mevcut işlenmiş görsel varsa görme yeteneğiyle analiz et, yoksa promptu ayrıştır). Kullanıcı yalnızca açıklama verdiyse açıklamayı şartname olarak ele al.

Bu alanları çıkar ve devam etmeden önce kullanıcıya geri yazdır:

```
Reklam Başlığı (birebir metin): "..."
Baskın Görsel Özne: <kişi / ürün paketi / yaşam tarzı sahnesi / yalnızca metin>
Renk Hikayesi: <görselden çekilen 3-5 hex kodu veya "uygulanamaz, görsel yok">
Vaat veya Kanca: <reklamın sattığı tek cümle>
Farkındalık Düzeyi: <farkında değil / sorundan haberdar / çözümden haberdar / üründen haberdar / en yüksek farkındalık>
Muhtemel Trafik Niyeti: <anlık DTC / düşünülerek DTC / potansiyel müşteri yakalama / demo randevusu>
Reklamda Gösterilen Fiyat: <evet, $XX çıpasıyla veya hayır>
```

Bir onay sor: "Doğru görünüyor mu? `evet` ya da düzeltilecek şeyi yaz."

Onayı bekle. Birebir reklam başlığı en kritik alandır; Adım 4'teki H1 mesaj uyumu kuralı buna bağlıdır.

## Adım 3: DTC mi yoksa lead gen rotası mı?

Bu öncelik sırasıyla rotayı belirle:

1. Marka DNA'sı herhangi bir alanda açıkça `business_model: ecom` veya `business_model: lead_gen` bildiriyorsa bunu kullan.
2. Değilse, reklamda fiyat etiketi, ürün paketi, "Şimdi Alışveriş Yap", "Sepete Ekle" veya ödeme stilinde bir arka plan varsa DTC rotasını seç.
3. Değilse, reklamda "Demo rezervasyonu yap", "Rehberi al", "Ücretsiz danışmanlık", "Kaydol", "Başvur", "İndir" ifadeleri varsa lead gen rotasını seç.
4. Değilse şunu sor: "Bu bir ürün satın alma (DTC) mı yoksa potansiyel müşteri yakalama ya da randevu (lead gen) mi?"

Rota belirlendikten sonra ilgili referans dosyasını yükle:

- DTC rotası için `references/dtc-route.md` dosyasını oku.
- Lead gen rotası için `references/leadgen-route.md` dosyasını oku.

Kullanıcı yanlışsa geçersiz kılabilsin diye rotayı tek cümleyle duyur: "Reklamda ürün paketi ve fiyat göründüğü için DTC olarak yönlendiriyorum." veya "Marka DNA'nızdaki `business_model: lead_gen` bildirimi nedeniyle lead gen olarak yönlendiriyorum."

## Adım 4: VOC enjeksiyonuyla kopya üretimi

`references/voc-injection-map.md` dosyasını oku. Slot haritasını izleyerek bölüm bölüm kopya oluştur. Slot haritası sabit bir nedenden dolayı var: her slotun dönüşüm sağlayan farklı bir içerik türü vardır.

Kopya üretimi sırasında uyulması zorunlu kurallar:

**H1 mesaj uyumu, tartışmasız.** H1, birebir reklam başlığından en az bir 3+ kelimelik ifade içermek zorundadır. İçermiyorsa yeniden üret. Bu tek kural, ücretli trafik için en yüksek kaldıraçlı dönüşüm etkenidir.

**Okunabilirlik hedefi: 7. sınıf altı.** Unbounce 2024 verisi: 5.-7. sınıf okuma düzeyi yüzde 12,9 dönüşüm sağlarken profesyonel düzey yüzde 2,1'de kalır. 7. sınıfın üzerindeki her paragrafı işaretle ve yeniden yaz.

**Kelime sayısı bütçesi: 250-725 kelime.** Unbounce 2024 optimum aralığı. Sert üst sınır: 800.

**Yasaklı ifadeler: varsayılan liste artı Marka DNA'sı ses bloğundaki kaçınılacaklar listesi.** Varsayılan yasak liste: revolutionize, unlock, seamless, leverage, supercharge, game changer, harness, empower, elevate, transformative, in today's fast paced world, level up, paradigm shift, holistic, robust, scalable, synergistic. Marka DNA'sının ses bloğundaki `avoid` listesindeki her şeyi ekle. Markanın kendi yasak listesi varsa her ikisi de geçerlidir.

**Uydurulmuş sayı, isim veya iddia yok.** Her müşteri sayısı, yorum sayısı, yıldız puanı veya referans VOC'tan veya Marka DNA'sından gelir. Bir sayı bu iki belgede yoksa uydurma; bölümü onsuz yaz.

## Adım 5: Marka tokenlarıyla tasarım üretimi

`references/brand-dna-parsing.md` ve `references/34-tells.md` dosyalarını oku.

Marka DNA'sını `:root` konumunda CSS özel özellikleri olarak ayrıştır:

```css
:root {
  --brand-primary: <Marka DNA'sından>;
  --brand-accent: <Marka DNA'sından>;
  --brand-ink: <Marka DNA'sından>;
  --brand-paper: <Marka DNA'sından>;
  --brand-muted: <Marka DNA'sından>;
}
```

Bildirilen ekran ve gövde yazı tiplerini Google Fonts'tan içe aktar. Başlıklarda `font-['DISPLAY_NAME']`, gövde metinlerde `font-['BODY_NAME']` şeklinde Tailwind keyfi değerleriyle uygula.

Marka DNA'sının sesi ve AOV ile uyumlu bir izlenim düzeyi seç (1 GÖRÜNMEZ ile 5 MUHTEŞEM arasında, bkz. `references/34-tells.md`). Düzeyi dosyanın başındaki bir HTML yorumunda belirt. Yoğunluk, hareket ve renk genelinde tutarlı biçimde uygula.

Ardından 34 klişeyi uygula. `references/34-tells.md` dosyasını oku ve her kuralı uygula. Herhangi bir klişe çözülmeden dosyayı gönderme.

**Marka geçersiz kılma sarmalayıcı kuralı.** Marka DNA'sı her zaman estetik tercihin önüne geçer. Marka DNA'sı açıkça Inter'i gövde yazı tipi olarak bildiriyorsa, Tell 9 işaretlese de Inter kullan. 34 klişe YALNIZCA beyan edilmemiş tercihler için geçerlidir. Markaya rağmen değil, marka içinde özgün ol.

## Adım 6: Çıktı montajı ve öz denetim

HTML ve Tailwind şablonları için `references/section-library.md` dosyasını oku. Rotaya özgü bölüm sırasına göre sayfayı monte et.

Dosyayı bellekte oluştur. Şu sırayla şunları içermelidir:

1. Tam DOCTYPE, `lang` ve `scroll-smooth` sınıfı bulunan html, head, body.
2. Head içinde Tailwind Play CDN script etiketi.
3. Head içinde Google Fonts ön bağlantı ve stil sayfası bağlantısı.
4. Head içindeki `<style>` bloğunda `:root` konumunda 5 marka tokenını içeren CSS özel özellikleri.
5. Open Graph etiketleri, Twitter card meta, viewport meta, favicon bağlantısı.
6. `REPLACE_WITH_YOUR_PIXEL_ID` yer tutucu içeren Meta Pixel iskeleti; yükleme sırasında PageView tetiklenir.
7. Yönlendirilen türe ait tam bölüm sırasıyla gövde (bkz. `references/dtc-route.md` veya `references/leadgen-route.md`).
8. FAQ bölümü eklendiyse FAQ JSON-LD şeması.
9. DTC için zorunlu, lead gen için isteğe bağlı mobil yapışkan CTA çubuğu.
10. Minimal alt bilgi (telif hakkı, gizlilik, koşullar, iletişim; en fazla üç satır).
11. Her düzenlenebilir bloğun etrafında `<!-- ====== EDIT: <SLOT ADI> ====== -->` ve `<!-- ====== /EDIT ====== -->` sarmalayıcıları.
12. Kullanıcının gerçek değerlerle değiştirmesi gereken yerlerde (URL'ler, pixel kimliği, görsel yolları, müşteri fotoğrafları) tümü büyük harfle `REPLACE_WITH_*` yer tutucu dizeleri.
13. Dosyanın altında beş yorumlanmış A/B varyant bloğu, açıkça işaretlenmiş:
    - 2 alternatif H1
    - 1 alternatif kahraman düzeni
    - 1 alternatif sosyal kanıt bloğu
    - 1 alternatif son CTA mikrokopyası

Dosyayı yazmadan önce ön gönderim öz denetimini çalıştır. `references/34-tells.md` dosyasını tekrar oku. Bu onay bloğunu yazdır:

```
Ön gönderim denetimi:
  H1 mesaj uyumu (reklam başlığından 3+ kelimelik ifade): GEÇTİ / KALDI
  Okunabilirlik 7. sınıf altı (tüm paragraflar): GEÇTİ / KALDI
  Kelime sayısı 250-725: <sayı> ... GEÇTİ / KALDI
  Yasaklı ifadeler (varsayılan + Marka DNA'sı ses.kaçın): YOK / <liste>
  Tam olarak 1 birincil CTA hedefi: GEÇTİ / KALDI
  Marka tokenları uygulandı (en fazla 5): GEÇTİ / KALDI
  İki yazı tipi ailesi (1 ekran + 1 gövde): GEÇTİ / KALDI
  Mobil yapışkan CTA çubuğu mevcut (DTC) veya değerlendirildi (lead gen): GEÇTİ / KALDI
  Meta Pixel yer tutucusu mevcut: GEÇTİ / KALDI
  Bozuk görsel referans yok (her img'in gerçek src veya REPLACE_WITH_ değeri var): GEÇTİ / KALDI
  Sayfa dışı harici nav bağlantısı yok: GEÇTİ / KALDI
  Hiçbir yerde lorem ipsum yok: GEÇTİ / KALDI
  OG + Twitter + viewport + favicon meta: GEÇTİ / KALDI
  Aile 1 (Görsel Varsayılanlar): 8/8 temiz
  Aile 2 (Tipografi): 8/8 temiz
  Aile 3 (Düzen): 10/10 temiz
  Aile 4 (İçerik Klişesi): 8/8 temiz
```

KALDI olan varsa bellekte düzelt, sonra yaz. Bilinen klişelerle gönderme.

Dosyayı `$RFLAB/10_Landing_Pages/landing-page-<YYYY-MM-DD-HHMMSS>.html` konumuna yaz; zaman damgası `YYYY-MM-DD-HHMMSS` formatında mevcut UTC zamanıdır.

Ardından proje durum dosyasını güncelle:

```
TS="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
printf '{\n  "last_completed_at": "%s"\n}\n' "$TS" > "$RFLAB/_meta/state.json"
```

## Adım 7: Kullanıcıya sonraki adımları anlat

Az önce yazdığın mutlak dosya yolunu yazdır, ardından tam olarak şu kartı ekle:

> Tamam. Kaydedildi: `<mutlak yol>`
>
> Sonraki adımlar:
>
> 1. Yerel olarak önizle: .html dosyasını herhangi bir tarayıcıda aç. Derleme adımı gerekmez.
> 2. Deploy et: dosyayı Cloudflare Pages'e sürükle, Netlify Drop'a bırak ya da Shopify, Webflow veya Framer'da özel sayfa olarak yükle. Dosya tamamen kendi kendine yeten bir yapıdadır.
> 3. Yer tutucuları değiştir: gerçek verilerle doldurulması gereken her yeri bulmak için dosyada `REPLACE_WITH_` ifadesini ara (pixel kimliği, görsel URL'leri, ödeme URL'si, destek e-postası, favicon).
> 4. A/B testi: dosyanın altına kaydıl ve 5 yorumlanmış varyant bloğunu incele. Birini yorumdan çıkar, karşılık gelen canlı bloğu yoruma al, yeniden deploy et.
> 5. Hız notu: bu dosya anında deploy için Tailwind Play CDN kullanır. Günlük $50'nin üzerinde harcamada `<script src="https://cdn.tailwindcss.com">` satırını önceden derlenmiş bir Tailwind stil sayfasıyla değiştir (npx tailwindcss -o style.css --minify) ve sonucu satır içi ekle. Tailwind Play, ölçekte önemli olan 150-300 ms engelleyici script ekler.

İsteğe bağlı önizleme adımını sun:

> Deploy etmeden önce sayfanın ekran görüntüsünü çekmemi ister misin? Playwright MCP ile dosyayı açıp masaüstü ve mobil ekran görüntüsü alarak görsel inceleme yapabilirim. Ekran görüntüsü için `evet` yaz.

Evet cevabında Playwright MCP'yi kullanarak:

1. `file://<mutlak yol>` yerel dosya URL'sini aç.
2. 1280x800 (masaüstü) boyutunda tam sayfa ekran görüntüsü al.
3. 390x844 (iPhone 14 görünüm alanı) boyutunda tam sayfa ekran görüntüsü al.
4. Her ikisini `$RFLAB/10_Landing_Pages/preview-<zaman-damgası>-desktop.png` ve `preview-<zaman-damgası>-mobile.png` konumlarına kaydet.
5. Her iki ekran görüntüsünü satır içi sun.

Playwright MCP kullanılamıyorsa, kullanıcıya önizlemenin atlandığını ve HTML dosyasını açarak manuel önizleme yapabileceğini söyle.

## Çıktı doğrulama

Bu beceriyi tamamlanmış ilan etmeden önce şunları doğrula:

1. HTML dosyası `10_Landing_Pages/` altında beklenen yolda diskte var.
2. Dosya en az 8000 bayt (ince bir sayfa eksik derlemenin işaretidir).
3. Dosya tam olarak bir `<h1>` etiketi içeriyor.
4. H1 iç metni, birebir reklam başlığından 3+ kelimelik bir ifade içeriyor.
5. Dosya `:root` konumunda 5 bildirilmiş değişkenle marka tokenlarını içeriyor.
6. Dosya `REPLACE_WITH_YOUR_PIXEL_ID` içeren Meta Pixel iskeletini barındırıyor.
7. Dosya en az 8 adet `<!-- ====== EDIT:` işareti içeriyor (her düzenlenebilir blok için bir tane).
8. Dosyanın altında 5 yorumlanmış A/B varyant bloğu bulunuyor.
9. `lorem ipsum`, `<TODO>`, `<Marka DNA'sından>` gibi yer tutucu dizeler kalmamış (yalnızca kasıtlı olan `REPLACE_WITH_*` işaretleri kabul edilebilir).
10. `state.json` yeni `last_completed_at` zaman damgasıyla güncellendi.

Herhangi bir maddede doğrulama başarısız olursa, dosyayı körce yeniden yazmaya çalışma. Spesifik başarısızlığı kullanıcıya bil, bir düzeltme öner, ardından yeniden oluştur ve kaydet.

## Kalite kuralları, tartışmasız

1. Her kelime VOC'tan, Marka DNA'sından, reklam kreatifinden veya operasyonel olgulardan (dosya formatı, sayfa sayısı, zaman taahhüdü) gelir. Hiçbir şey uydurulmaz.
2. Bozuk görsel bağlantısı yoktur. Bunların yerine `REPLACE_WITH_<AD>` yer tutucuları kullan.
3. Sayfa başına tam olarak 1 birincil CTA hedefi. Tüm birincil CTA'lar aynı yere bağlanır.
4. Meta Pixel yer tutucusu her zaman dahil edilir.
5. DTC için mobil yapışkan CTA çubuğu zorunludur. Lead gen uzun sayfaları için isteğe bağlı fakat tavsiye edilir.
6. Sayfadan çıkaran harici nav bağlantısı yoktur. Logo varsayılan olarak bağlantısızdır.
7. Tüm gövde metni için okuma düzeyi 7. sınıf altıdır.
8. En fazla 2 yazı tipi ailesi (1 ekran + 1 gövde).
9. En fazla 5 marka rengi tokeni.
10. Tutarlı boşluk ölçeği (Tailwind varsayılanları, 4 / 8 / 16 / 24 / 32 / 48 / 64 / 96 / 128).
11. H1'de mesaj uyumu: birebir reklam başlığından 3+ kelimelik ifade.
12. Tüm 34 yapay zeka klişesi yazılmadan önce çözülür.
13. Çıktıda hiçbir yerde konuşma amaçlı tire veya kısa tire yoktur. Virgül, "ve" veya ayrılmış cümleler kullan. (Eklentinin `enforce-no-dashes` kancası geçen olursa ayıklar, ancak onları ilk etapta yazmak bir klişedir; bkz. Tell 28.)

## Referans dosyalar

Bu dosyaları iş akışı sırasında talep üzerine oku. Tüm token tasarrufu için baştan yükleme; aşamalı açıklama yaklaşımı kullan.

| Dosya | Ne zaman oku |
|---|---|
| `references/voc-injection-map.md` | Adım 4 (hangi VOC içeriği hangi slota gider) |
| `references/brand-dna-parsing.md` | Adım 5 (Marka DNA'sından token çıkarımı) |
| `references/34-tells.md` | Adım 5 (izlenim düzeyi + klişe uygulaması) ve Adım 6 (son denetim) |
| `references/conversion-patterns.md` | Adım 4 (kopya stratejisi) ve Adım 6 (bölüm sıralaması) |
| `references/section-library.md` | Adım 6 (HTML + Tailwind şablonları) |
| `references/dtc-route.md` | Adım 3'te DTC rotası seçilirse |
| `references/leadgen-route.md` | Adım 3'te lead gen rotası seçilirse |

## Değişmez kurallar

1. Çıktı dosyasını asla `$RFLAB/10_Landing_Pages/` dışına yazma. Adım 0a'daki korumalı klasör kılavuzu tartışmasızdır.
2. Adım 0b'de hem VOC hem de Marka DNA belgesi keşfedilmeden asla devam etme. Reddet ve kardeş beceriyi göster.
3. Müşteri sayısı, yorum sayısı, yıldız puanları, referanslar veya başka herhangi bir sosyal kanıt sayısı asla uydurma. VOC ve Marka DNA'sından çek ya da elementi atla.
4. Mesaj uyumunu asla bozma. H1, birebir reklam başlığını yansıtmak zorundadır (3+ kelimelik ifade). Bu, hard fail uygulanan tek kuraldır ve en yüksek kaldıraçlı dönüşüm etkenidir.
5. Dosyayı asla deploy etme. Beceri diske yazar ve sonraki adımları yazdırır. Deployment kullanıcının işidir.
6. Meta MCP, Higgsfield veya herhangi bir görsel ya da video oluşturma modelini asla çağırma. Bu beceri HTML yazar, medya üretmez.
7. Çıktıda hiçbir yerde konuşma amaçlı tire veya kısa tire yoktur. Virgül, "ve" veya ayrılmış cümleler kullan.
