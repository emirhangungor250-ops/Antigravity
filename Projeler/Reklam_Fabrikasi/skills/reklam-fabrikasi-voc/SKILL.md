---
name: reklam-fabrikasi-voc
description: "Kullanıcı /voc, /voc research, /voice of customer komutlarını yazdığında veya bir ürün için VOC araştırması yapmak istediğinde bu beceriyi kullan. Statik Meta reklamları için tam Reklam Fabrikası VOC iş akışını çalıştırır: birden fazla platformda derin ürün ve marka araştırması yapar, ham araştırma raporu üretir, ardından bir reklam metni yazarının statik Meta reklamları yazmak için kullandığı profesyonel, indirilebilir bir HTML belgesine biçimlendirir. Kullanıcı VOC araştırması, müşteri sesi, müşteri dili madenciliği veya reklam yazmadan önce müşterilerin bir ürün hakkında ne dediğini araştırmak istediğinde bu beceriyi tetikle. Web aramanın etkin olması gerekir."
---

# Reklam Fabrikası, Statik Meta Reklamlar için VOC Araştırması

Bu beceri, iki aşamalı VOC araştırma iş akışının tamamını çalıştırır. Çıktı, ham ve birebir müşteri dilini ile stratejik analizi içeren profesyonel, indirilebilir bir HTML belgesidir. Bu belge statik Meta reklam metni yazmak, görsel promptları oluşturmak ve kreatif brief hazırlamak için gereken her şeyi kapsar.

---

## Başlamadan Önce

Web araması ZORUNLU olarak etkin olmalıdır. Etkin değilse dur ve kullanıcıya devam etmeden önce etkinleştirmesini söyle.

---

## Gerekli Girdiler

Herhangi bir şeye başlamadan önce kullanıcıdan şu iki bilgiyi iste:

1. **Hedef ürün URL'si**, ürünün özel sayfası (ana sayfa değil). Örnek: `marka.com/urunler/urun-adi`
2. **Hedef ürün adı**, markanın ürünü tam olarak nasıl adlandırdığı

Her ikisini de almadan devam etme.

---

## İş Akışı, İki Aşama, Sırayla Çalıştır

Atlamadan devam et. 2. Aşama, 1. Aşamanın çıktısına bağlıdır.

---

### AŞAMA 1, VOC Araştırması

Araştırma promptunu şuradan yükle:
`references/research-prompt.md`

Tam olarak takip et. Kullanıcının ürün URL'sini ve ürün adını her `{product_url}` ve `{product_name}` yer tutucusuna geçir. Promptun başka hiçbir bölümünü değiştirme.

Araştırmayı **web araması etkin** şekilde çalıştır. Prompttaki minimum alıntı eşiklerine ulaşılana kadar aramaya devam et. Aramalar yetersiz sonuç verirse farklı arama terimleri, eş anlamlılar, ilgili ürünler ve bitişik toplulukları dene; erken bırakma.

1. Aşama tamamlandığında kullanıcıya şunu söyle:
> "Araştırma tamamlandı. Belgeniz hazırlanıyor..."

Ham araştırma çıktısını kullanıcıya gösterme, doğrudan 2. Aşamaya geç.

---

### AŞAMA 2, HTML Belgesi

Biçimlendirme talimatlarını şuradan yükle:
`references/html-format.md`

Tam olarak takip et. 1. Aşama araştırmasını kaynak materyal olarak kullan. Dışa bağımlılığı olmayan, tek başına çalışan bir HTML dosyası çıktısı üret.

#### Çıktı yolunu çöz (proje başına)

Çıktılar ana klasöre değil, Claude Code'un açık olduğu çalışma klasörüne kaydedilir. Her marka veya müşteri kendi "Reklam Fabrikası" alt klasörünü alır.

Aşağıdaki İLK ÇALIŞMA KORUMA bloğunu Bash aracıyla çalıştır, ardından dosyayı şuraya kaydet:

```
<pwd>/Reklam Fabrikası/01_VOC_Research/voc-[urun-adi].html
```

Kaydederken ve kullanıcıya geri bildirirken mutlak çözümlenmiş yolu (`pwd` çıktısından) kullan.

#### İLK ÇALIŞMA KORUMA ("./Reklam Fabrikası/" oluşturmadan önce Bash aracıyla çalıştır)

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
  mkdir -p "$TARGET/01_VOC_Research" "$TARGET/_meta"
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
- `FIRSTRUN:<path>`: kullanıcıya söyle: "Çıktıları `<path>/` klasörüne kaydedeceğim. Bu klasöre ilk kez kaydediliyor, doğru mu? (evet/hayır)". "Evet" bekle. Evet cevabında şunu çalıştır: `mkdir -p "<path>/01_VOC_Research" "<path>/_meta" && date -u +%Y-%m-%dT%H:%M:%SZ > "<path>/_meta/folder-confirmed.flag"`, ardından devam et. Hayır cevabında hangi klasörü istediklerini sor ve dur.
- `READY:<path>`: sessizce devam et.

HTML'i kaydet, ardından mutlak dosya yolunu kullanıcıya `present_files` aracıyla sun. Sonunda şunu onayla: "Kaydedildi: `<mutlak-yol>`."

---

## Kurallar

- **Web araması zorunludur.** Tüm alıntılar, canlı araştırma sırasında bulunan gerçek kaynaklardan gelmelidir. Yapay dil, müşterilerin "muhtemelen söylediğinin" yeniden ifadesi olmaz.
- **Her marka büyüklüğü için çalışır.** Araştırma promptunun yerleşik bir öncelik sıralaması vardır; doğrudan ürün incelemeleri azsa otomatik olarak rakip VOC'una, ardından sorun alanı araştırmasına geçer. Sıfır incelemeye sahip bir marka bile dolu ve zengin bir belge alır.
- **Önce ürün, sonra marka.** Marka düzeyindeki verilere genişlemeden önce ürünün özel sayfasını ve ürün düzeyindeki incelemeleri araştır.
- **Yalnızca birebir alıntı.** Her müşteri alıntısı tam olarak yazıldığı gibi korunmalıdır: argo, dilbilgisi hataları, BÜYÜK HARFLER, üç nokta, duygusal noktalama dahil.
- **Hook veya başlık yok.** Bu beceri ham VOC verisi toplar ve analiz eder. Reklam metni yazmaz. Çıktı, reklam metni yazarları ve kreatif stratejistler için bir araştırma belgesidir, kopya paketi değil.
- **Yalnızca statik reklamlar.** Tüm analiz ve dil toplama, statik görsel Meta reklamlar için yararlı olanla sınırlıdır. Video senaryo notları, UGC yönlendirme veya sözlü dil rehberi dahil etme.

---

## Çıktı Doğrulaması

Bu beceriyi tamamlandı ilan etmeden önce şunları doğrula:

1. Teslim edilebilir, beklenen yolda mevcut: `<pwd>/Reklam Fabrikası/01_VOC_Research/voc-<urun-adi>.html`.
2. Teslim edilebilir boş değil (dosya boyutu > 20000 bayt, sağlıklı bir VOC HTML belgesinin göstergesidir).
3. Beklenen içerik sayısı iddiaya uyuyor:
   - HTML, `references/research-prompt.md` içinde belirtilen minimum birebir alıntı sayısını içeriyor.
   - "N alıntı buldum" dediysen dosya N alıntı içeriyor, 0 değil.
4. Yer tutucu dizeler kalmadı:
   - `{product_url}`, `{product_name}`, `[BRAND_NAME]`, `<TODO>` veya `lorem ipsum` yok.
5. Tüm zorunlu bölümler dolu:
   - Ürün incelemeleri ve müşteri alıntıları (birebir)
   - Sorun noktaları ve duygusal dil
   - Kimlik dili ve ICP sinyalleri
   - Rakip veya sorun alanı bağlamı (doğrudan VOC azsa)

Doğrulama başarısız olursa:

1. Önce otomatik düzeltmeyi dene:
   - Bir bölüm boşsa, doldurmak için hedefli aramalar yap.
   - Alıntı eşiklerine ulaşılmadıysa rakip VOC ve sorun alanı sorgularına genişlet.
   - Yer tutucular kaldıysa kullanıcının ürün URL'si ve ürün adını geçir ve yeniden oluştur.

2. Otomatik düzeltme başarısız olursa kullanıcıya dürüst bir rapor sun:
   "VOC araştırması: Bir belge ürettim ancak doğrulama şunu gösterdi: <sorun>. <düzeltme girişimi> denedim ve bu <işe yaramadı / kısmen işe yaradı>. Eksiksiz sonuç almak için şunları yapabilirsiniz:
   - Daha zengin inceleme verisi için ek ürün sayfası URL'leri veya kardeş ürün URL'leri sağla
   - Yedek kaynak olarak incelemelerini çekebilmem için 2-3 bilinen rakip ismi ver
   - Ürünün incelemelerin bulunabileceği şekilde kamuya satıldığını onayla
   Veya sahip olduğunuz incelemeleri, destek biletlerini veya sosyal medya söylemlerini yapıştır, ben de onları analiz ederim."

3. Web araması sıfır kullanılabilir alıntı döndürdüyse:
   - Daha geniş parametrelerle BİR KEZ daha dene:
     - Niş değiştiricileri bırak ve marka adını tek başına ara
     - Marka açıklamasında adı geçen bitişik ürün kategorilerini ara
     - Dolaylı VOC madenciliği için sorun alanı sorgularına geç (ürünün çözdüğü acı)
   - Yine sıfırsa dürüst bir rapor sun:
     "VOC araştırması: Ürün incelemelerini, marka söylemlerini ve sorun alanı madenciliğini denedim. Veri kaynakları alıntılanabilir dil döndürmedi. Bu genellikle ürünün çok yeni olduğu veya çevrimiçi ortamda farklı bir adla satıldığı anlamına gelir. Devam etmek için şunları yapabilirsiniz:
     - Sahip olduğunuz iç müşteri incelemelerini, destek e-postalarını veya görüşme transkriptlerini yapıştır
     - Karşılaştırılabilir bir VOC profili oluşturabileceğim daha yakın bir rakip isme ver
     Veya inceleme henüz yoksa ürünün lansman öncesi açılış sayfasını paylaş."
