---
name: reklam-fabrikasi-meta-handoff
description: Kullanıcının claude.ai web uygulamasına yapıştırdığı, Meta'nın mcp.facebook.com/ads adresindeki resmi Ads MCP'sinin çalıştığı zengin bağlamlı bir aktarım promptu hazırlar. /reklam-fabrikasi:meta-handoff, /meta-handoff, /handoff, "kampanyalarımı analiz etmek istiyorum", "kampanya oluşturmak istiyorum", "reklam yayınlamak istiyorum", "Meta'yı analiz edelim", "kampanya oluşturalım", "kampanyalarımı teşhis et", "kazanan reklamları bul", "yeni kampanya başlat", "Meta'da kampanya kur" komutlarında tetikle. İki mod; mevcut kampanyaları analiz et veya yeni kampanyalar oluştur. Mevcut proje klasöründen Marka DNA'sı, VOC, reklam metni ve kreatif referansları, artı kullanıcının kısa ön alım sorularına verdiği yanıtları bir araya getirir. Aktarım promptunu diske kaydeder ve kullanıcının kopyalaması için yazdırır. Claude Code içinden Meta'nın MCP'sini asla çağırmaz.
---

# Reklam Fabrikası, Meta Reklamları Aktarımı

## Kesin kural

**Bu beceri Meta'nın MCP'sini doğrudan asla çağırmaz. Meta'nın MCP'si yalnızca claude.ai web uygulamasında çalışır, Claude Code'da çalışmaz. Becerinin tek işi, kullanıcının claude.ai'ye yapıştırması için zengin bağlamlı bir aktarım promptu hazırlamaktır.**

Kendini `meta_` veya `mcp__meta_` ile başlayan herhangi bir aracı kullanmaya ulaşırken bulursan dur. Bu araçlar bu Claude Code oturumunda yüklü değildir ve yüklenmemelidir. Bu becerinin çıktısı, diskteki metin ve sohbette yazdırılan metindir. Bundan ibaret.

## Bu beceri neden var

Meta, resmi Ads MCP sunucusunu 29 Nisan 2026'da `https://mcp.facebook.com/ads` adresinde yayınladı. MCP mükemmeldir. Kampanyaları uçtan uca oluşturabilir, bütçeleri yönetebilir, tam hedefleme JSON ile reklam kümeleri oluşturabilir, image_hash veya video_id aracılığıyla kreatifleri ekleyebilir, içgörüler çalıştırabilir, tanılama yapabilir, katalogları yönetebilir. Aynı zamanda katı sınırları var; medya yüklemesi yok, özel veya benzer kitle oluşturulamıyor ve kalıcı silme yok.

Sorun OAuth istemci yapılandırmasında. Meta yalnızca `https://claude.ai/api/mcp/auth_callback` yönlendirme URI'sini beyaz listeye alıyor. Bu geri çağırma yalnızca claude.ai web uygulamasında çözümleniyor. Claude Code OAuth el sıkışmasını tamamlayamıyor, bu nedenle kullanıcı özel bir bağlantı olarak eklemeyi denese bile MCP Claude Code içinde çalışamıyor.

Kullanıcı, Meta'nın MCP'sini yararlı kılan tüm girdilere zaten sahip; müşteri sesi dili, marka DNA'sı renkleri ve konumlandırması, reklam metni paketleri, kreatif açılar, görsel referanslar. Bu girdiler mevcut Claude Code proje klasöründe yaşıyor. Temiz bir aktarım olmadan kullanıcının, tüm bunları yeni bir claude.ai sohbetinde yeniden açıklaması gerekir. Bu beceri bunu çözüyor.

## Adım 0a, Proje çıktı klasörünü çöz

Çıktılar, Claude Code'un açık olduğu çalışma klasörüne kaydedilir. Önce bu Bash bloğunu çalıştır:

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
  mkdir -p "$TARGET/09_Meta_Handoff" "$TARGET/_meta"
  echo "READY:$TARGET"
fi

# Marka hafızasını (CLAUDE.md) başlat: marka klasörü varsa ve dosya
# eksikse. Yapacak bir şey yokken sessiz ve tekrar güvenli çalışır.
if [ -d "$TARGET" ] && [ -n "${CLAUDE_PLUGIN_ROOT:-}" ] && [ -f "$CLAUDE_PLUGIN_ROOT/scripts/seed-claude-md.sh" ]; then
  bash "$CLAUDE_PLUGIN_ROOT/scripts/seed-claude-md.sh" >/dev/null 2>&1 || true
fi
```

- `PROTECTED:<path>`: reddet ve kullanıcıya markaya özel bir alt klasörde Claude Code'u açmasını söyle. Dur.
- `FIRSTRUN:<path>`: "Aktarım promptunu `<path>/` klasörüne kaydedeceğim. Bu klasöre ilk kez kaydediliyor, doğru mu? (evet/hayır)" diye sor. Evet cevabında klasörleri oluştur ve `<path>/_meta/folder-confirmed.flag` dosyasını yaz. Hayır cevabında dur.
- `READY:<path>`: sessizce devam et.

Çözümlenen yolu `$RFLAB` olarak yakala. Aktarım promptunu şuraya Markdown olarak kaydet:

```
$RFLAB/09_Meta_Handoff/handoff-<YYYY-MM-DD-HHMMSS>.md
```

## Adım 0b, Önceki proje bağlamını otomatik keşfet

Aktarım promptunun bir araya getirmesi gereken girdiler için proje klasörünü taramak amacıyla `ls`, `find` ve `Read` (gerçek araçlar) kullan. Herhangi bir Meta aracı çağırma.

Bu yollara bak ve var olanları yakala:

- `$RFLAB/01_VOC_Research/` en son VOC araştırma çıktısı için (markdown veya HTML)
- `$RFLAB/02_Brand_DNA/` en son marka DNA'sı belgesi için
- `$RFLAB/03_Ad_Spy/` tüm swipe dosyaları için (bilgilendirici, canlı kampanya çalışması için her zaman ilgili değil)
- `$RFLAB/04_Static_Ads/` kullanıcının oluşturduğu en son statik reklam promptları için
- `$RFLAB/05_UGC/` tüm UGC senaryoları veya video promptları için
- `$RFLAB/06_Ad_Copy/` en son metin paketi (başlıklar, ana metin, açıklamalar) için
- `$RFLAB/07_Multiplied_Ads/` tüm çoğaltıcı çıktıları için
- `$RFLAB/08_Rebuilt_Competitor_Ads/` tüm yeniden oluşturma çıktıları için

Var olan her yol için bulduğun dosya adlarını listele. En ilgili olanları aktarım promptunun içinde özetleyeceksin. Uzun belgelerin tamamını aktarım promptuna YAPISTIRMA. Her birini maksimum 5-10 satırda özetle; başlıklar, sloganlar ve yüksek sinyalli ifadeler için yalnızca birebir alıntılar kullan.

Bir klasör boş veya eksikse atla. Aktarım promptu neyin mevcut olup olmadığı konusunda dürüst olmalı.

## Adım 1, Kullanıcıdan modu sor

Tam olarak şu mesajı gönder:

> claude.ai web uygulamasına yapıştırabileceğiniz zengin bağlamlı bir aktarım promptu hazırlayacağım; Meta'nın resmi Ads MCP'si orada çalışıyor. Oradaki Claude'un canlı reklam hesabınıza tam erişimi olacak.
>
> Hangi modu istiyorsunuz?
>
> 1. **Mevcut kampanyaları analiz et**: Prompt, alıcı Claude'u profesyonel bir Meta reklamları analisti olarak yapılandırır. Kampanya performansını okuyacak, dökümler çalıştıracak, kreatif yorgunluğunu, kitle örtüşmesini ve hız sorunlarını teşhis edecek, ardından alabileceğiniz spesifik eylemleri önerecek.
> 2. **Yeni kampanyalar oluştur**: Prompt, alıcı Claude'u profesyonel bir Meta reklamları stratejisti ve kampanya oluşturucusu olarak yapılandırır. Doğru yapı, metin, hedefleme ve eklenen kreatif referanslarla birlikte DURAKLATILMIŞ durumda bir kampanya, reklam kümesi ve reklam başlatmanıza yardımcı olacak.
>
> `1` veya `2` yanıtlayın.

Cevabı bekle.

## Adım 2, Moda özgü ön alım

### Mod 1 ise (analiz)

Sor:

> Aktarım promptunu yazmadan önce kısa ön alım:
>
> 1. Analiz edilmesini istediğiniz zaman aralığı nedir? Varsayılan `last_7d`. Diğer seçenekler: `last_3d`, `last_14d`, `last_28d`, `last_30d`, `last_90d`, `this_month`, `last_month`, `last_quarter`, `maximum`. `2026-04-01 ile 2026-04-29` gibi özel bir aralık da verebilirsiniz.
> 2. Spesifik endişeniz nedir, bir veya iki cümlede? Örnekler: "Bu hafta EBM arttı", "en çok harcayan reklam kümesinde kreatif yorgunluğu", "A ve B kampanyaları arasında kitle örtüşmesi", "hız sorunları, harcama günlük bütçenin altında", "tam hesap denetimi istiyorum, spesifik endişe yok".
> 3. Derinlemesine incelenmesini istediğiniz spesifik kampanya, reklam kümesi veya reklamlar var mı? Varsa ID'leri yapıştırın. Yoksa analist en çok harcayan kampanyalarla başlayacak.

Cevapları bekle ve yakala.

### Mod 2 ise (oluştur)

Sor:

> Aktarım promptunu yazmadan önce kısa ön alım:
>
> 1. Bu kampanya hangi ürün veya teklif içindir?
> 2. Kampanya hedefi nedir? Birini seçin: satış, lead, trafik, etkileşim, farkındalık, uygulama kurulumu.
> 3. Reklam kümesi başına günlük bütçe (dolar cinsinden) veya toplam bütçe? Dolar miktarını belirtin; stratejist aktarım sırasında sente çevirecek.
> 4. Coğrafi hedefleme? Varsayılan ABD.
> 5. Bir veya iki cümlede kitle açıklaması. Örnek: "temiz güzellik ve cilt bakımıyla ilgilenen 30-55 yaş arası kadınlar". Not: Stratejist yalnızca reklam hesabınızda zaten mevcut özel kitlelere başvurabilir, yenilerini oluşturamaz çünkü Meta'nın MCP'si kitle oluşturamaz.
> 6. Kreatif hazırlık, iki soru:
>    a. Zaten bir `image_hash`'iniz var mı (Ads Manager'da daha önce yüklenmiş bir görselden) veya `post_id`'niz (yayınlanmış bir Sayfa gönderisinden)? Varsa yapıştırın.
>    b. Görseliniz yalnızca bilgisayarınızdaysa bu sorun değil. Aktarım promptu, referansı geri almak için ilk kez Ads Manager'a (Kütüphane, Görseller, Yükle) veya bir Sayfa gönderisi yayınlamak için size talimat verecek.
> 7. Stratejistin bilmesi gereken başka bir şey var mı? (teklifler, eşsiz satış noktası, aciliyet, uyumluluk kısıtlamaları vb.)

Cevapları bekle ve yakala.

## Adım 3, Aktarım promptunu oluştur

Kullanıcının claude.ai'ye yapıştıracağı tek bir Markdown belgesi oluştur. Belge aşağıdaki bölümleri sırasıyla içermelidir. Moda göre rol atamasını ayarla.

Bu şablonu birebir kullan. Köşeli parantezli yer tutucuları topladığın değerlerle değiştir. YAPILABILIR ve YAPILAMAZ listelerini birebir koru, düzenleme.

### Şablon iskeleti

```
# Claude Code'dan Meta Reklamları <mod> aktarımı, [YYYY-MM-DD HH:MM]

## Rolünüz

[Mod 1 ise] Siz profesyonel bir Meta reklamları analistisiniz. Kullanıcı bu sohbeti claude.ai'de açtı çünkü Meta'nın mcp.facebook.com/ads adresindeki resmi Ads MCP'si burada çalışıyor, Claude Code'da değil. Kullanıcı yukarı akış kreatif ve marka çalışmasını Claude Code'da zaten yaptı. Şimdi canlı kampanyalarının temiz bir teşhisini istiyor. Verileri okuyun, somut metrikler ve tarih aralıklarıyla sorunları belirleyin ve spesifik sonraki adımlar önerin. Her iddia için metriği ve zaman penceresini belirtin.

[Mod 2 ise] Siz profesyonel bir Meta reklamları stratejisti ve kampanya oluşturucususunuz. Kullanıcı bu sohbeti claude.ai'de açtı çünkü Meta'nın mcp.facebook.com/ads adresindeki resmi Ads MCP'si burada çalışıyor, Claude Code'da değil. Kullanıcı yukarı akış kreatif ve marka çalışmasını Claude Code'da zaten yaptı. Şimdi her şeyin doğru kurulmuş şekilde DURAKLATILMIŞ durumda, inceleyip etkinleştirmeye hazır yeni bir kampanya başlatmak istiyor. Her geri dönüşü olmayan adımı onlarla onaylamadan MCP'yi çağırmayın.

## Meta'nın MCP'sinin yapabilecekleri

mcp.facebook.com/ads adresindeki MCP şunları yapabilir:

- Hedef, bütçe (CBO veya ABO), teklif stratejisi, özel reklam kategorileri ve zamanlamayla kampanya oluştur.
- Tam hedefleme JSON ile reklam kümesi oluştur. Bu şunları kapsar: coğrafya, yaş, cinsiyet, ilgi alanları, davranışlar, saved_audience_id aracılığıyla özel kitleler, yerleşimler, optimizasyon hedefi, faturalandırma olayı, günlük veya toplam bütçe, atıf, ve pixel_id'nizi referans alan promoted_object.
- Tam kreatif JSON özelliğiyle reklam oluştur. Bu şunları kapsar: başlık, ana metin, açıklama, bağlantı, CTA, page_id, instagram_actor_id, image_hash referansı, video_id referansı, takip özellikleri ve dönüşüm alanı.
- Mevcut bir kampanya, reklam kümesi veya reklamın herhangi bir alanını güncelle. Bu, status alanıyla duraklatmayı kapsar.
- DURAKLATILMIŞ'tan ETKİN'e geçir.
- Tanılamalar, hatalar, performans eğilimleri, fırsat puanı, referans değerler ve reklamveren bağlamı çek.
- Veri kümesi (piksel) meta verilerini, kalitesini ve istatistiklerini oku.
- Katalog yönetimi. Oluştur, listele, ayrıntıları al, tanılamaları, akış kurallarını, ürünleri, ürün kümelerini. Katalog, base64 aracılığıyla doğrudan dosya yüklemesini destekler.
- Bir işletme için Sayfaları al.

## Meta'nın MCP'sinin yapamayacakları

MCP şunları yapamaz:

- Reklam kreatifleri olarak görsel veya video dosyası yükle. Hesapta zaten mevcut olan bir image_hash veya video_id'ye ihtiyacı var. Yükleme uç noktası açık değil.
- Özel kitleler oluştur. Yalnızca hesapta zaten mevcut olan kitlelere saved_audience_id ile başvurabilir.
- Benzer kitleler oluştur.
- Müşteri listelerini yükle.
- Pikseller oluşturmak veya kurmak (yalnızca okuma).
- Yeni reklam hesapları, Sayfalar veya Business Manager varlıkları oluştur.
- Kullanıcı rolleri, izinler, faturalandırma, ödeme yöntemleri veya harcama limitleri yönet.
- Organik gönderiler oluştur veya öne çıkar.
- Yorumlara veya mesajlara yanıt ver.
- Varlıkları kalıcı olarak sil. En yakın eylem, status PAUSED ile güncelleme aracılığıyla duraklatmaktır.
- Fatura veya faturalandırma geçmişine eriş.
- Meta Reklam Kütüphanesi'ne eriş.

## Kreatif için pratik iş akışı notu

[Mod 2 ise] Kullanıcının görseli zaten reklam hesabına yüklenmiş ve bir image_hash'i varsa VEYA kullanmak istedikleri mevcut bir Sayfa gönderisi varsa, tam kopya ve kreatif eklenmiş kampanya ve reklam kümesi ve reklamın tamamını bu sohbeti terk etmeden uçtan uca DURAKLATILMIŞ olarak oluşturabilirsiniz.

Görsel yalnızca kullanıcının bilgisayarındaysa iş akışı şudur:

1. Kullanıcı Ads Manager'ı açar, Varlık Kütüphanesi veya Sayfa Gönderileri alanına gider, görseli yükler (veya Sayfa gönderisini yayınlar), image_hash'i (veya gönderi ID'sini) buraya kopyalar.
2. Oradan her şey MCP aracılığıyla gerçekleşir.

meta_create_ad'ı çağırmaya çalışmadan önce her zaman kullanıcının image_hash veya post_id'ye sahip olduğunu onaylayın. Yoksa durun, tam olarak nereye yükleyeceğini ve ne kopyalayacağını söyleyin.

## Kullanıcının proje bağlamı

Kullanıcı yukarı akış kreatif çalışmasını Claude Code'da Reklam Fabrikası eklentisi altında yaptı. Aşağıdaki özetler o proje klasöründen bir araya getirildi.

### Marka DNA'sı özeti

[Marka DNA'sı belgesi bulunduysa 5-10 satırlık özet ekle. Marka adını, birincil renkleri, konumlandırmayı, ses tonunu ve görsel kısıtlamaları dahil et. Belge yoksa şunu yaz: "Mevcut değil, 02_Brand_DNA/ klasöründe Marka DNA'sı belgesi bulunamadı."]

### Müşteri sesi özeti

[VOC araştırması bulunduysa 5-10 satırlık özet ekle. Baskın sorun noktalarını ve arzu dilini yakalayan 3-5 birebir müşteri alıntısı dahil et. Belge yoksa şunu yaz: "Mevcut değil, 01_VOC_Research/ klasöründe VOC belgesi bulunamadı."]

### Mevcut reklam metni paketleri

[06_Ad_Copy/ içindeki tüm reklam metni dosyalarının listesini ekle. En son için başlıkları, ana metin varyantlarını ve açıklamaları birebir yapıştır. Boşsa şunu yaz: "Mevcut değil, 06_Ad_Copy/ klasöründe metin paketi bulunamadı."]

### Kreatif referanslar

[Mod 2 ise ve kullanıcı bir image_hash veya post_id sağladıysa, stratejistin kullanması için burada açıkça listele. Kullanıcı görselinin hâlâ diskinde olduğunu söylediyse şunu yaz: "Kullanıcının kreatifleri hâlâ yerel bilgisayarındadır. Henüz Ads Manager'a yüklemediler. Yapmanız gereken ilk eylem için aşağıdaki Nereden Başlanır bölümüne bakın."]

### Diğer proje çıktıları

[Kullanıcının sahip olduğu diğer ilgili çıktıları listele; örn. reklam casusu swipe dosyaları, çoğaltıcı varyasyonlar, yeniden oluşturulmuş rakip reklamlar, UGC senaryoları. Dosya adıyla başvur. Alıcı Claude, konuşma sırasında kreatif ilhama ihtiyaç duymadıkça bunları görmezden gelebilir.]

## Kullanıcının ön alım cevapları

[Mod 1 için: zaman aralığını, spesifik endişeyi ve adını verdikleri spesifik varlık ID'lerini listele.]

[Mod 2 için: ürünü veya teklifi, hedefi, dolar cinsinden günlük veya toplam bütçeyi, coğrafi hedeflemeyi, kitle açıklamasını, kreatif hazırlığı (image_hash, post_id veya "hâlâ diskte") ve diğer notları listele.]

## Nereden Başlanır

[Mod 1 ise] Konuşmayı gerçek varlık ID'lerine dayandırmak için `meta_list_campaigns(status_filter="ACTIVE", limit=50)` ile kullanıcının aktif kampanyalarını listeleyerek başlayın. Ardından genel toplamı almak için `meta_account_insights(date_preset="<pencere>")` çalıştırın. Ardından en çok harcayan kampanyalara `meta_campaign_insights` ile inin ve tanılama çerçevelerini uygulayın: yorgunluk için frekans artışı, Simpson paradoksu için döküm etkisi, 7 gün içinde 50'den az dönüşümü olan reklam kümeleri için öğrenme aşaması çıkarımı, açık artırma örtüşme sinyalleri, hız anormallikleri, CTR ve CPM aracılığıyla kreatif sıralama proxy'leri. Her bulgu için metriği ve tarih aralığını belirtin. Hedef ID'leriyle spesifik sonraki adımlar önerin.

[Mod 2 ise] Kullanıcının hazır bir image_hash veya post_id'ye sahip olduğunu onaylayarak başlayın. Yoksa durun, tam olarak nereye yükleyeceğini (image_hash için Ads Manager, Varlık Kütüphanesi, Görseller veya post_id için Sayfa gönderisi yayınla) ve ne kopyalayıp bu sohbete geri yapıştıracağını söyleyin. Referansa sahip olduğunuzda, kampanya ve reklam kümesi ve reklam yapısını düz İngilizce olarak önce önerin: hedef, optimizasyon hedefi, kitle hedefleme JSON, sent cinsinden günlük bütçe ve kreatif özelliği. Kullanıcının evet demesini bekleyin, ardından DURAKLATILMIŞ durumda MCP aracılığıyla her şeyi oluşturun. Herhangi bir kampanyayı ETKİN'e çevirmeden önce kullanıcıyla onaylayın.

## Bu sohbet için kesin kurallar

1. Her iddiayı metrik ve tarih aralığıyla belgeyin. "EBM yüksek" işe yaramaz; "EBM 42 dolar last_7d'de 28 dolara karşı, yüzde 50 artış" bir bulgudur.
2. Her oluşturma çağrısında varsayılan olarak DURAKLATILMIŞ. Yalnızca açık kullanıcı onayıyla ETKİN'e çevirin.
3. Bütçeler sent cinsindendir. 50 dolar/gün, daily_budget 5000 demektir. Sent değerini geçmeden önce her zaman dolar miktarını kullanıcıyla onaylayın.
4. Toplu değişikliklerden önce onaylayın. Kullanıcı bir seferde 3'ten fazla varlığı değiştirmek isterse önce listeleyin ve açık onay alın.
5. 500 dolar/gün üzerindeki günlük bütçe için ikinci onay gereklidir. Hesabı açıklayın: "[X] dolar/gün çarpı [N] reklam kümesi [Y] dolar/gün toplamı. Onaylıyor musunuz?"
6. Erişim token'ını asla yankılamayın.
7. Araç adları uydurmayın. Bir araç resmi MCP sunucusunun yüzeyinde değilse mevcut değildir.
```

Şablonu doldururken:

- `[YYYY-MM-DD HH:MM]` yerine mevcut yerel zaman damgasını koy.
- `[Mod 1 ise]` ve `[Mod 2 ise]` bloklarını ilgili blokla değiştir, diğerini sil.
- Özetleri Adım 0b'de keşfedilen proje bağlamından doldur. Marka DNA'sı ve VOC için her bölümü 5-10 satırda tut. Metin paketleri için başlıkları ve ana metni birebir yapıştır çünkü stratejistin tam olarak ihtiyaç duyduğu bunlardır.
- Bir bölümde içerik yoksa gerçek "Mevcut değil, ..." satırını yaz ve devam et. Dürüstlük dolgu maddeden iyidir.
- Promptun hiçbir yerinde cümle duraksatıcısı olarak kısa çizgi veya em-dash kullanma. Virgül, "ve" veya cümleleri böl.

## Adım 4, Aktarım promptunu kaydet ve yazdır

Oluşturulan Markdown'ı şuraya kaydet:

```
$RFLAB/09_Meta_Handoff/handoff-<YYYY-MM-DD-HHMMSS>.md
```

Ardından kullanıcının temizce kopyalayabilmesi için tüm aktarım promptunu Claude Code sohbetinde çevrili kod bloğu içinde yazdır. Çevrili bloktan sonra kaydedildiği mutlak dosya yolunu söyle.

## Adım 5, Kullanıcıya tam olarak ne yapacağını söyle

Kullanıcıya düzenleme yapmadan tam olarak şu mesajı gönder:

> Şimdi şunları yap:
>
> 1. Web tarayıcında claude.ai'yi aç (Claude Code değil, claude.ai'deki normal web uygulaması)
> 2. Ayarlar'a, Özelleştir'e, Bağlantılar'a git
> 3. Özel bağlantı ekle'ye tıkla
> 4. Bu URL'yi yapıştır: https://mcp.facebook.com/ads
> 5. Ekle'ye tıkla ve istendiğinde Facebook OAuth girişini tamamla
> 6. claude.ai'de yeni bir sohbet başlat
> 7. Yukarıdaki aktarım promptunu o sohbete yapıştır
> 8. claude.ai'deki Claude artık canlı reklam hesabına tam erişimle Meta reklamları uzmanın olarak hareket edecek

## Çıktı Doğrulaması

Bu beceriyi tamamlandı ilan etmeden önce şunları doğrula:

1. Aktarım Markdown'ı beklenen yolda diskte mevcut.
2. Dosya en az 2000 bayt (ince aktarım yararlı değildir).
3. Dosya rol atama satırını içeriyor (mod 1 veya mod 2 ifadesi).
4. Dosya YAPILABILIR ve YAPILAMAZ yetenek listelerini birebir içeriyor.
5. Dosya image_hash ve post_id hakkında pratik iş akışı notunu içeriyor (yalnızca mod 2 için zorunlu, mod 1 için isteğe bağlı).
6. Dosya proje bağlamı bölümünü içeriyor; Marka DNA'sı, VOC ve metin paketi alt bölümleriyle birlikte, her biri ya özetlenmiş ya da "Mevcut değil" olarak işaretlenmiş.
7. Dosya Nereden Başlanır talimatlarıyla bitiyor.
8. Yer tutucu dizeler kalmadı. `[YYYY-MM-DD HH:MM]`, `[Mod 1 ise]`, `<pencere>`, `<TODO>` veya `lorem ipsum` yok.

Doğrulama başarısız olursa, dosya yazımını körce yeniden deneme. Eksik bölümü kullanıcıya sun, eksik girdiyi onaylamalarını iste (örn. "Metin paketi bulamadım, atlamamı mı yoksa önce bir tane eklemenizi mi istiyorsunuz?"), ardından yeniden oluştur ve yeniden kaydet.

## Kesin kurallar

1. Herhangi bir Meta MCP aracını asla çağırma. Bu araçlar bu Claude Code oturumunda mevcut değildir ve gelecekteki bir oturumda benzer adlı bir araç görünse bile bu beceri onu çağırmamalıdır. Beceri bir aktarımdır, bir çalıştırıcı değil.
2. Herhangi bir token, şifre veya kimlik bilgisini asla yankılama. Kullanıcı bu beceri için hiçbir zaman bir tane yazmaz.
3. Uzun belgelerin tamamını (Marka DNA'sı, VOC vb.) aktarım promptuna asla yapıştırma. Özetle. Alıcı Claude gerekirse kullanıcıdan belirli bilgileri paylaşmasını isteyebilir.
4. Araç adlarını asla uydurma. Yukarıdaki YAPILABILIR listesi, 29 Nisan 2026 itibarıyla desteklenen yüzeyi gösteriyor. Abartma.
5. Beceri çıktısında hiçbir yerde, hiçbir zaman em-dash veya cümle duraksatıcısı olarak kısa çizgi kullanma. Virgül, "ve" veya cümleleri böl.
6. Beceri diskteki metin ve sohbette yazdırılan metni çıktılar. Teslim edilebilir olan bunlardır.
