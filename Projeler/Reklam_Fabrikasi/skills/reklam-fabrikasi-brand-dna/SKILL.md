---
name: reklam-fabrikasi-brand-dna
description: "Kullanıcı Playwright kullanarak bir marka için Marka DNA'sı belgesi oluşturmak istediğinde bu beceriyi kullan. /brand dna playwright, /brand dna 3.0, /brand dna, /brand DNA, /create brand dna, /brand research komutlarında veya kullanıcı 'bir markayı araştırmak istiyorum', 'marka DNA belgesi oluştur', 'marka araştırması yapalım', '[marka] için marka DNA'sı yap' ya da 'marka DNA belgesi istiyorum' dediğinde tetikle. Ayrıca kullanıcı Reklam Fabrikası iş akışını başlatıyor ve statik reklamlar yapmadan önce marka araştırmasıyla başlamak istiyorsa da tetikle. Marka DNA'sı oluşturma, marka araştırması veya marka kimliği belgelerine ilişkin her istekte BU BECERİYİ tetikle."
---

# Reklam Fabrikası, Marka DNA'sı Belgesi (Playwright 3.0)

Bu beceri, Marka DNA'sı araştırma iş akışını çalıştırır. Bir markanın tam görsel ve sözel kimliğini tersine mühendislikle çözer ve 40 statik reklam promptu iş akışına girdi olarak kullanılmaya hazır, cilalı, indirilebilir bir HTML Marka DNA'sı belgesi çıktısı üretir.

Bu sürüm, canlı renk çıkarımı için **Playwright MCP**'yi (ekran görüntüleri + sitede tıklama) ve geri kalan her şey için **web aramasını** kullanır.

---

## Bu beceri nasıl tetiklenir

Kullanıcı şunlardan herhangi birini yazar:
- `/brand dna`
- `/brand DNA`
- `/brand dna playwright`
- `/brand dna 3.0`
- `/create brand dna`
- `/brand research`
- "Bir markayı araştırmak istiyorum"
- "Marka DNA belgesi oluştur"
- "[Marka] için marka DNA'sı yap"
- "Marka DNA belgesi istiyorum"
- "Marka araştırması yapalım"
- "Reklam Fabrikası iş akışını başlat"

---

## İş Akışı

### Adım 1, Kullanıcıdan girdileri iste

**Kullanıcıya sor:**
> Hangi markayı araştırmak istiyorsunuz? Bana **marka adını** ve **hedef URL'yi** (web siteleri) verin.

---

### Adım 2, Playwright MCP'yi kontrol et (renkler için ZORUNLU)

Bu beceri, canlı siteyi ziyaret ederek ve birden fazla sayfada gezinerek markanın tam renk paletini çıkarmak için **Playwright MCP**'yi kullanır. Onsuz, renk çıkarımı yalnızca web aramasına geri döner; bu çok daha az hassastır.

**Herhangi bir renk araştırması yapmadan önce, Playwright araçlarını etkinleştirmeyi dene:**

1. Playwright MCP araçlarını yüklemek için `"browser navigate"`, `"browser screenshot"` veya `"playwright"` gibi bir sorguyla `tool_search` kullanarak Playwright MCP araçlarını ara (örn. `browser_navigate`, `browser_take_screenshot`, `browser_click`, `browser_snapshot`, `browser_evaluate`).
2. Yüklendikten sonra, MCP'nin bağlı olduğunu doğrulamak için markanın ana sayfasına hızlı bir `browser_navigate` dene.

**Playwright MCP bağlıysa** (gezinti başarılı):
- Adım 3'e (Canlı Renk Çıkarımı) geç.

**Playwright MCP bağlı DEĞİLSE** (araç hata döndürür veya eksikse):
- İş akışını HEMEN durdur.
- Düşürülmüş, yalnızca web aramasına dayalı bir sürümle devam ETME.
- Kullanıcıya aşağıdaki kurulum talimatlarını göster ve yeniden denemeden önce bağlı olduklarını onaylamalarını bekle:

> **Doğru renk çıkarımı için Playwright MCP'nin kurulu olması gerekiyor.**
>
> Onsuz yalnızca web aramasından hex kodlarını tahmin edebiliyorum, bu da canlı sitenin CSS'inden doğrudan çekmekten çok daha güvenilmez.
>
> Kurulum adımları:
>
> 1. Playwright MCP'yi yükle: `claude mcp add playwright npx @playwright/mcp@latest`
> 2. MCP bağlanması için Claude Code'u yeniden başlat
> 3. "Hazırım" yaz ve yeniden deneyeyim
>
> Playwright olmadan devam etmemi istiyorsanız (yalnızca web araması ile renk tahmini) bana söyleyin, bunu da yapabilirim (renk doğruluğu belirgin ölçüde düşük olur).

Kullanıcı hazır olduğunu onayladığında, Playwright bağlantı kontrolünü yeniden çalıştır ve devam et.

---

### Adım 3, Playwright ile Canlı Renk Çıkarımı (yalnızca renkler)

Playwright MCP bağlıyken, bu adımın amacı **yalnızca markanın tam renk paletini yakalamaktır**. Kopya, tipografi açıklamaları, ses/ton veya diğer araştırma verilerini toplamak için Playwright kullanma; bunlar 4. Adımda web aramasından gelir.

1. Hedef URL'yi (ana sayfa) açmak için `browser_navigate` kullan.
2. `browser_take_screenshot` ile tam sayfa ekran görüntüsü al.
3. **Sitede tıkla**; ana sayfada kalma. Tıklanabilir referansları bulmak için `browser_snapshot` kullan, ardından aşağıdakiler gibi en az 3-5 ek sayfaya gitmek için `browser_click` kullan:
   - Hakkında / Hikayemiz
   - Ürün / Mağaza / Koleksiyon sayfaları
   - Belirli bir ürün detay sayfası
   - Sürdürülebilirlik / Misyon / Değerler
   - Alt bilgi sayfaları (örn. İletişim, SSS)
4. Yüklendikten sonra her sayfada ekran görüntüsü al.
5. Her sayfada, gerçek hesaplanmış CSS renk değerlerini çekmek için `browser_evaluate` (veya eşdeğeri) çalıştır. Kullanışlı JS parçacıkları:
   - `body`, `header`, `footer`, `section`, `.btn`, `[class*="cta"]`, `[class*="button"]`'ın arka plan renkleri
   - Başlıklar (`h1`, `h2`, `h3`) ve gövde metnindeki ön plan/metin renkleri
   - Düğme/CTA `background-color` ve `color`
   - Herhangi bir CSS özel özelliği (`getComputedStyle(document.documentElement).getPropertyValue('--primary')` vb.)
6. Tüm sayfalardaki benzersiz hex kodlarını topla. Şunları belirle:
   - **Birincil renk** (en çok kullanılan marka rengi, genellikle logo/CTA'da)
   - **İkincil renk** (destekleyici marka rengi)
   - **Vurgu rengi** (vurgu için seyrek kullanılır)
   - **Arka plan renkleri** (sayfa/bölüm arka planları)
   - **CTA rengi** (düğme arka planı + metin)

Bu adımdan yalnızca renk bilgilerini kaydet. Ekran görüntülerini sakla, 4. Adımda gerekirse görsel onay için başvurulabilir.

---

### Adım 4, Araştırma promptunu çalıştır (geri kalan her şey için web araması)

Şuradan tam araştırma promptunu yükle:
`references/brand-dna-prompt.md`

Renkler dışındaki her şeyi toplamak için **web araması etkin** şekilde çalıştır:
- Tasarım ajansı / yeniden markalaşma geçmişi
- Marka kılavuzları / basın kiti / medya kiti
- Tipografi yığını (logo fontu, görüntü fontu, gövde fontu)
- Ses ve ton (5 sıfat)
- Fotoğraf yönü
- Ambalaj ayrıntıları
- Rekabetçi farklılaşma
- Marka hikayesi, misyon, konumlandırma
- Basın kapsamı ve reklam kreatif stili (Meta Reklam Kütüphanesi)

Prompttaki her `[BRAND]` ve `[TARGET URL]` yer tutucusuna kullanıcının marka adını ve URL'sini geçir. Promptun başka hiçbir bölümünü değiştirme.

Prompt renk bilgisi istediğinde (Aşama 2 #4 "Renk uygulaması", Aşama 4 "GÖRSEL SİSTEM" hex kodları), **3. Adımda Playwright aracılığıyla çıkarılan renkleri kullan**; bunlar web aramasının döndürdüğü her şeyin üzerine yazar.

---

## Çıktı

Markanın kendi görsel kimliğiyle eşleşen stil üzerine indirilebilir HTML Marka DNA'sı belgesi. Belge şunları yapmalı:

- Markanın gerçek renk paletini (3. Adımda Playwright aracılığıyla canlı çekilen hex kodları), tipografi stilini ve görsel ruh halini kullan
- Açık bölüm başlıklarıyla temiz profesyonel düzen ve geniş boşluk içer
- Görsel açıdan etkileyici olsun; bir müşteriye veya kreatif ekibe gösterilebilecek bir şey
- Anında indirilebilir olsun
- Siteden çekilen tam hex kodlarını listeleyen "Canlı Site Renkleri" bölümü içersin

### Çıktı yolunu çöz (proje başına)

Çıktılar ana klasöre değil, Claude Code'un açık olduğu çalışma klasörüne kaydedilir. Her marka kendi "Reklam Fabrikası" alt klasörünü alır.

Aşağıdaki İLK ÇALIŞMA KORUMA bloğunu Bash aracıyla çalıştır, ardından HTML'i şuraya kaydet:

```
<pwd>/Reklam Fabrikası/02_Brand_DNA/brand-dna-[marka-slug].html
```

Kaydederken ve kullanıcıya geri bildirirken mutlak çözümlenmiş yolu kullan.

### İLK ÇALIŞMA KORUMA ("./Reklam Fabrikası/" oluşturmadan önce Bash aracıyla çalıştır)

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
  mkdir -p "$TARGET/02_Brand_DNA" "$TARGET/_meta"
  echo "READY:$TARGET"
fi

# Marka hafızasını (CLAUDE.md) başlat: marka klasörü varsa ve dosya
# eksikse. Yapacak bir şey yokken sessiz ve tekrar güvenli çalışır.
if [ -d "$TARGET" ] && [ -n "${CLAUDE_PLUGIN_ROOT:-}" ] && [ -f "$CLAUDE_PLUGIN_ROOT/scripts/seed-claude-md.sh" ]; then
  bash "$CLAUDE_PLUGIN_ROOT/scripts/seed-claude-md.sh" >/dev/null 2>&1 || true
fi
```

Üç sonuç:

- `PROTECTED:<path>`: reddet ve kullanıcıya söyle: "Reklam Fabrikası/ klasörünü doğrudan `<path>` içinde oluşturmayacağım. Claude Code'u `~/Desktop/<markaniz>/` gibi markaya özel bir alt klasörde aç ve tekrar dene." Ardından dur.
- `FIRSTRUN:<path>`: kullanıcıya söyle: "Çıktıları `<path>/` klasörüne kaydedeceğim. Bu klasöre ilk kez kaydediliyor, doğru mu? (evet/hayır)". "Evet" bekle. Evet cevabında şunu çalıştır: `mkdir -p "<path>/02_Brand_DNA" "<path>/_meta" && date -u +%Y-%m-%dT%H:%M:%SZ > "<path>/_meta/folder-confirmed.flag"`, ardından devam et. Hayır cevabında hangi klasörü istediklerini sor ve dur.
- `READY:<path>`: sessizce devam et.

Dosyayı kullanıcıya `present_files` aracıyla sun. Sonunda şunu onayla: "Kaydedildi: `<mutlak-yol>`."

---

## Dosyayı sunduktan sonra

Marka DNA'sı belgesi teslim edildikten sonra kullanıcıya şunu söyle:

> Marka DNA'sı hazır! 40 statik reklam promptunuzu oluşturmaya hazır olduğunuzda `/40 static ads` komutunu kullanın ve bu Marka DNA'sı belgesini VOC araştırmanız ve ürün görsellerinizle birlikte yükleyin.

---

## Önemli kurallar

- **Playwright MCP yalnızca renkler için kullanılır.** Ekran görüntüsü al, birden fazla sayfada gezin, canlı CSS'den hex kodlarını çıkar. Kopya, tipografi, ses/ton veya diğer araştırma verileri için kullanma; bunlar web aramasından gelir.
- **Web araması etkin olmalıdır.** Tüm renk dışı araştırmalar (tipografi, ses, fotoğraf, marka hikayesi, ambalaj vb.) web aramasından gelir.
- **Gezin, ana sayfada kalma.** Renk paleti yalnızca ana sayfa hero'suyla değil, hover durumları, alternatif bölümler, alt bilgi uygulamaları ve ürün sayfası vurgu renkleriyle de yakalanacak şekilde Playwright ile en az 3-5 sayfayı ziyaret et.
- **Marka DNA'sı promptunu değiştirme.** Marka adını ve URL'yi gir, `references/brand-dna-prompt.md` içinde tam olarak yazıldığı gibi çalıştır.
- **Çıktı bir HTML dosyası olmalıdır.** Markdown değil, düz metin değil; stillendirilmiş, indirilebilir HTML belgesi.
- **Canlı renkler kazanır.** Playwright'tan gelen canlı renk hex kodları web aramasının döndürdüğüyle çeliştiğinde, canlı renklere güven.

---

## Çıktı Doğrulaması

Bu beceriyi tamamlandı ilan etmeden önce şunları doğrula:

1. Teslim edilebilir, beklenen yolda mevcut: `<pwd>/Reklam Fabrikası/02_Brand_DNA/brand-dna-<marka-slug>.html`.
2. Teslim edilebilir boş değil (dosya boyutu > 25000 bayt, sağlıklı bir Marka DNA'sı HTML belgesinin göstergesidir).
3. Beklenen içerik sayısı iddiaya uyuyor:
   - Canlı Site Renkleri bölümünde en az 3 hex kodu (birincil, ikincil, vurgu).
   - Tipografi yığınında en az 2 adlandırılmış yazı tipi (veya biri açık yedekli).
4. Yer tutucu dizeler kalmadı:
   - `[BRAND]`, `[Brand]`, `[TARGET URL]`, `<TODO>` veya `lorem ipsum` yok.
5. Tüm zorunlu bölümler dolu:
   - Canlı Site Renkleri (Playwright'tan hex kodları)
   - Tipografi yığını
   - Ses ve ton (5 sıfat)
   - Fotoğraf yönü
   - Marka hikayesi, misyon, konumlandırma
   - Rekabetçi farklılaşma

Doğrulama başarısız olursa:

1. Önce otomatik düzeltmeyi dene:
   - Renk sayısı azsa, Playwright ile ek sayfalara git ve hesaplanmış CSS renkleri için `browser_evaluate`'i yeniden çalıştır.
   - Bir araştırma bölümü boşsa, yalnızca o bölüm için hedefli web araması yap ve sonuçları birleştir.
   - Yer tutucular kaldıysa kullanıcının sağladığı marka adı ve hedef URL'den doldur.

2. Otomatik düzeltme başarısız olursa kullanıcıya dürüst bir rapor sun:
   "Marka DNA'sı: Belgeyi ürettim ancak doğrulama şunu gösterdi: <sorun>. <düzeltme girişimi> denedim ve bu <işe yaramadı / kısmen işe yaradı>. Eksiksiz sonuç almak için şunları yapabilirsiniz:
   - Bir yeniden yönlendirme kazdıysam markanın resmi web sitesi URL'sini onayla
   - Biliyorsanız basın kiti veya medya kiti URL'sini paylaş
   - Sahip olduğunuz resmi marka kılavuzlarını, Hakkında sayfası metnini veya renk şartnamesini yapıştır
   Veya ana sayfa ve bir ürün sayfasının ekran görüntülerini paylaş, bunlardan çalışırım."

3. Playwright sıfır kullanılabilir renk döndürdüyse:
   - Daha geniş parametrelerle BİR KEZ daha dene:
     - 3 ek sayfayı ziyaret et (alt bilgi, SSS, iletişim) ve değerlendiriciyi yeniden çalıştır
     - Açık kullanıcı onayıyla yalnızca web aramasına dayalı renk çıkarımına geri dön
   - Yine sıfırsa dürüst bir rapor sun:
     "Marka DNA'sı: Birden fazla sayfada Playwright renk çıkarımını ve web aramasını denedim. Canlı renkler yüklenmedi (büyük olasılıkla ödeme duvarı, coğrafi engel veya hesaplanmış stil sorgularını engelleyen SPA). Devam etmek için şunları yapabilirsiniz:
     - Ana sayfa ve bir ürün sayfasının ekran görüntülerini paylaş
     - Sahip olduğunuz marka stil kılavuzundan hex kodlarını yapıştır
     - Azaltılmış renk doğruluğuyla yalnızca web aramasına dayalı çalışmayı onayla
     Veya görsel kimliği yakın olan benzer bir marka isimlendirin, referans olarak işaretleyeyim."
