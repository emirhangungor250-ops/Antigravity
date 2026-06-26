# Reklam Fabrikası için marka hafızası

Bu dosya markanın yaşayan kural kitabıdır. Bu klasör bağlamda olduğunda Claude Code onu otomatik yükler, yani buraya yazılan her şey bu marka klasöründeki her beceri çalıştırmasına uygulanır. Dosya markaya özeldir çünkü bu markanın `Reklam Fabrikası/` klasörünün içinde yaşar. Diğer marka klasörlerinin kendi kopyası vardır.

Dosya, kullanıcı eklentiyi kullandıkça büyümek üzere tasarlanmıştır. Kullanıcı her marka tercihi belirttiğinde, kural aşağıya kaydedilir, böylece Claude onu her gelecekteki oturumda ve her gelecekteki beceri çalıştırmasında hatırlar.

---

## Bu dosya nasıl güncellenir (Claude'a talimatlar)

Kullanıcı herhangi bir oturumda marka tercihi, kısıtı veya düzeltmesi belirttiğinde, bu dosyayı sadece-ekleme yapılan bir kayıt değil, YAŞAYAN bir belge olarak ele al. Edit aracıyla doğrudan güncelle. Önce izin isteme, sadece yap ve değişikliği tek satırla belirt.

İzlenecek tetikleyiciler:

- Olumsuzlar: "X kullanma", "Y'den kaçın", "asla Z deme", "Q göstermeyi bırak"
- Olumlular: "her zaman X de", "Y'yi tercih et", "Z yaptığında çok seviyorum"
- Düzeltmeler: "aslında Y değil X diyoruz", "Z konusunda fikrimizi değiştirdik"
- Ses veya ton: "bu çok kurumsal geliyor", "daha samimi yap"
- Görsel: "yeşil rengi asla kullanmayız", "stok fotoğraf insanları olmaz"
- İsimlendirme: "müşterilerimize müşteri değil alıcı denir"
- Teklifler, iddialar, düzenlemeye tabi dil: "X'i bir feragatname olmadan iddia etme"

Yazmadan önce, yeni girdiyi mevcut kurallara göre sınıflandır:

1. Mevcut bir kuralla ÇELİŞİR. Kullanıcı fikrini değiştirdi. Eski kuralı yenisiyle değiştir. İkisini birden bırakma. Tarihi güncelle.
2. Mevcut bir kuralla ÖRTÜŞÜR. İkisini de kapsayan tek bir temiz kuralda birleştir. Tarihi güncelle.
3. Mevcut bir kuralı İNCELTİR. Kuralı yerinde düzenle. Tarihi güncelle.
4. GERÇEKTEN YENİ. Aşağıdaki doğru bölüme bugünün tarihiyle ekle.

Her değişiklikten sonra, dosyayı yinelenen veya eskimiş kurallar için tara ve temizle. Dosya asla ~30 aktif kuralı geçmemeli. Geçerse, hangilerinin atılabileceğini kullanıcıya sor.

Bir değişiklik yaptığında, kullanıcının doğrulayabilmesi için tek satır söyle:

> Marka kuralı güncellendi: "yeşilden kaçın" yerine "küçük vurgu metinleri dışında yeşilden kaçın" konuldu.

Ya da:

> Marka kuralı eklendi: başlıklarda asla "devrim niteliğinde" kelimesini kullanma.

Bu dosyayı kullanıcıya söylemeden asla sessizce düzenleme.

Kullanıcı bir kuralı "unut" veya "kaldır" derse, ilgili bölümden sil. Mezarlık tutma.

---

## Marka Kuralları

Bu marka için aktif kurallar. Madde başına bir kural. Tarih biçimi YYYY-MM-DD.

(boş, kullanıcı eklentiyi kullandıkça dolacak)

---

## Ses ve Ton

Bu marka için metin ve reklam senaryolarının nasıl duyulması gerektiği. Ton, enerji, bakış açısı, cümle uzunluğu, argo kullanımı, resmiyet.

(boş, Marka DNA'sı becerisi çalıştığında ondan beslenebilir)

---

## Yasak Kelimeler ve İfadeler

Bu markanın reklam metninde, video senaryolarında veya açılış sayfalarında asla geçmemesi gereken kelimeler veya ifadeler.

(boş)

---

## Görsel Kurallar

Kaçınılacak renkler, kaçınılacak düzenler, kaçınılacak fotoğraf stilleri, karakter veya ürün çerçeveleme kuralları.

(boş, Marka DNA'sı becerisi çalıştığında ondan beslenebilir)

---

## İsimlendirme ve Terimler

Bu markanın müşterileri, ürünü, kategorisi ve yaygın kavramlar için kullandığı tam terimler. Jenerik alternatifi değil, bunları kullan.

(boş)

---

## Teklifler ve İddialar

Onaylı teklifler, onaylı iddialar, gerekli feragatnameler, düzenlemeye tabi dil kısıtları.

(boş)

---

## Son gözden geçirme

(bu dosya değiştiğinde otomatik güncellenir, biçim YYYY-MM-DD)

---

## Kullanıcı için notlar

Bu dosyayı doğrudan düzenlemene gerek yok. Herhangi bir oturumda Claude ile konuş, belirttiğin her tercih buraya otomatik kaydedilir. Bir kuralı açıkça eklemek istersen, `/reklam-fabrikasi:remember <kuralın>` çalıştır, doğrudan doğru bölüme gider.

Bir kural yanlış veya eskiyse, herhangi bir oturumda Claude'a söyle, kural güncellenir veya kaldırılır.
