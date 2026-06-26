---
description: Bir marka kuralını, tercihini veya kısıtını markanın CLAUDE.md dosyasına kaydeder, böylece Claude bunu her gelecekteki oturumda ve her gelecekteki beceri çalıştırmasında hatırlar. Kullanıcı bir kuralı açıkça kaydetmek istediğinde kullan, örneğin "devrim niteliğinde kelimesini asla kullanmadığımızı hatırla" ya da "marka rengimizin teal, hex 008080 olduğunu hatırla". Kuralı mevcut olanlara göre otomatik sınıflandırır (çelişir, örtüşür, inceltir, yeni).
---

# /reklam-fabrikasi:remember

Reklam Fabrikası eklentisi içinde çalışıyorsun. Kullanıcı az önce
`/reklam-fabrikasi:remember <bir şey>` (ya da `/remember <bir şey>`) yazdı.
Görevin, o marka kuralını markanın CLAUDE.md dosyasına kaydetmek, böylece
her gelecekteki oturum onu hatırlasın.

## Adım 0: Kural girdisini çöz

Kullanıcının girdisi ya komuttan sonra satır içinde gelir, örneğin
`/reklam-fabrikasi:remember devrim niteliğinde kelimesini asla kullanmayız`,
ya da sohbette mesajının geri kalanı olarak. Kural metni boş veya belirsizse,
kullanıcıdan tek kısa cümleyle yeniden ifade etmesini iste ve yanıtını bekle.

Kullanıcı kural olmadan sadece `/reklam-fabrikasi:remember` yazdıysa, sor:

> Hangi marka kuralını hatırlamamı istiyorsun? Tek kısa cümle yeterli.
> Örneğin: "devrim niteliğinde kelimesini asla kullanmayız", "marka
> rengimiz teal, hex 008080", "müşterilerimize müşteri değil her zaman
> alıcı de".

## Adım 1: Marka klasörünü ve CLAUDE.md yolunu çöz

Marka klasörünü bulmak ve henüz yoksa CLAUDE.md'yi yerleştirmek için bunu
Bash aracıyla çalıştır:

```
PWD_ABS="$(pwd)"
TARGET="${PWD_ABS}/Reklam Fabrikası"
CLAUDE_MD="$TARGET/CLAUDE.md"

if [ ! -d "$TARGET" ]; then
  echo "NO_BRAND_FOLDER:$PWD_ABS"
  exit 0
fi

# Marka hafıza dosyası eksikse yerleştir.
if [ ! -f "$CLAUDE_MD" ] && [ -n "${CLAUDE_PLUGIN_ROOT:-}" ] && [ -f "$CLAUDE_PLUGIN_ROOT/scripts/seed-claude-md.sh" ]; then
  bash "$CLAUDE_PLUGIN_ROOT/scripts/seed-claude-md.sh" >/dev/null 2>&1 || true
fi

if [ -f "$CLAUDE_MD" ]; then
  echo "READY:$CLAUDE_MD"
else
  echo "SEED_FAILED:$TARGET"
fi
```

Üç sonuç:

- `NO_BRAND_FOLDER:<yol>`: kullanıcı bu proje için henüz bir marka klasörü
  onaylamamış. Şunu söyle: "`<yol>` içinde henüz bir marka klasörü görmüyorum.
  Önce bir beceri çalıştır (örneğin `/reklam-fabrikasi:voc` veya
  `/reklam-fabrikasi:brand-dna`), marka klasörünü kursun, sonra
  `/reklam-fabrikasi:remember` kuralları oraya kaydeder." Sonra dur.
- `SEED_FAILED:<yol>`: marka klasörü var ama yerleştirme scripti eksik.
  Şunu söyle: "Eklenti kurulumunda bir terslik var. Tanılamak için
  `/reklam-fabrikasi:doctor` çalıştır." Sonra dur.
- `READY:<yol>`: Adım 2'ye geç.

## Adım 2: Mevcut CLAUDE.md'yi oku

Adım 1'deki yoldan CLAUDE.md'nin mevcut içeriğini Read aracıyla yükle. Yeni
kuralı mevcut olanlara göre sınıflandırmak için buna ihtiyacın var.

## Adım 3: Yeni kuralı sınıflandır

Kullanıcının kuralını dosyadaki her mevcut kurala karşı tüm bölümlerde
karşılaştır (Marka Kuralları, Ses ve Ton, Yasak Kelimeler ve İfadeler,
Görsel Kurallar, İsimlendirme ve Terimler, Teklifler ve İddialar). Şu
dördünden biri geçerlidir:

1. Mevcut bir kuralla **çelişir**. Kullanıcı fikrini değiştirdi.
   Eski kuralı yenisiyle değiştir. İkisini birden bırakma.
2. Mevcut bir kuralla **örtüşür**. İkisinin tam niyetini kapsayan tek
   bir temiz kuralda birleştir.
3. Mevcut bir kuralı **inceltir**. Eski kuralı yerinde düzenleyip yeni
   detayı ekle. Tarihini güncelle.
4. **Gerçekten yeni**. Kuralı en uygun bölüme ekle. Hangi bölüm olduğundan
   emin değilsen Marka Kuralları'na koy.

Yeni kurallar için bölüm yönlendirmesi:

- "X kelimesini asla kullanma", "Y ifadesinden kaçın", "Z deme" →
  Yasak Kelimeler ve İfadeler
- "sesimiz X", "Y gibi konuşuruz", "ton Z olmalı" →
  Ses ve Ton
- "marka rengimiz X", "yeşili asla kullanma", "stok fotoğraf
  insanları olmaz" → Görsel Kurallar
- "müşterilerimize X denir", "ürünümüze Y deriz" →
  İsimlendirme ve Terimler
- "her zaman X feragatnamesini ekle", "Z olmadan Y iddia etme" →
  Teklifler ve İddialar
- Başka her şey → Marka Kuralları

## Adım 4: Güncellemeyi yaz

CLAUDE.md'yi güncellemek için Edit aracını kullan.

Her yeni veya güncellenen kuralı, sonunda parantez içinde bugünün tarihiyle
tek bir madde olarak biçimlendir:

```
- Başlıklarda asla "devrim niteliğinde" kelimesini kullanmayız. (2026-05-19)
```

Bugünün UTC tarihini Bash aracıyla al:

```
date -u +%Y-%m-%d
```

Düzenledikten sonra, dosyanın altındaki "Son gözden geçirme" tarihini de
bugüne güncelle.

## Adım 5: Kullanıcıya onayla

Kullanıcının doğrulayabilmesi için tek kısa satır yazdır. Satırı
sınıflandırmaya göre eşle:

- **Eklendi**: "<bölüm> bölümüne marka kuralı eklendi: <tek satır kural>."
- **Güncellendi**: "<bölüm> bölümünde marka kuralı güncellendi: <eski> yerine <yeni> konuldu."
- **Birleştirildi**: "<bölüm> bölümünde marka kuralı birleştirildi: <birleşik kural>."

Örnek:

> Yasak Kelimeler ve İfadeler bölümüne marka kuralı eklendi: başlıklarda
> asla "devrim niteliğinde" kelimesini kullanma.

Tüm çıktı budur. CLAUDE.md'nin tamamını geri yapıştırma.

## Katı kurallar

1. **CLAUDE.md'ye önce sınıflandırmadan asla yazma.** Her zaman oku,
   sınıflandır, sonra yaz. Sınıflandırmayı atlamak, dosyada yinelenen
   veya çelişen kuralların oluşma yoludur.
2. **Bir kuralı asla sessizce silme.** Çelişiyorsa, eski kuralın
   değiştirildiğini kullanıcıya söyle.
3. **Her zaman tarih damgala.** Her yeni veya güncellenen madde
   `(YYYY-MM-DD)` ile biter. Alttaki Son gözden geçirme satırını da güncelle.
4. **Kuralları kısa tut.** Her biri tek satır, ideal olarak 100 karakterin
   altında. Kullanıcının girdisi uzunsa, tek satıra özetle ve onayla.
5. **Em-dash yok.** Virgül, "ve" kullan ya da cümleyi böl.
