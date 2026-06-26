# Marka DNA'sı Ayrıştırma

`reklam-fabrikasi-brand-dna` becerisi tarafından üretilen bir Marka DNA belgesinden tasarım tokenlarının nasıl çıkarılacağı ve bunların açılış sayfası HTML'ine nasıl enjekte edileceği.

## Marka DNA'sından çekilecekler

| Marka DNA'sı alanı | Ne çıkarılacak | HTML'de nereye gider |
|---|---|---|
| `colors.primary` | Hex kodu | `:root` konumunda `--brand-primary` CSS değişkeni |
| `colors.accent` | Hex kodu | `--brand-accent` CSS değişkeni |
| `colors.text` veya `colors.ink` | Hex kodu | `--brand-ink` CSS değişkeni |
| `colors.background` veya `colors.paper` | Hex kodu | `--brand-paper` CSS değişkeni |
| `colors.muted` veya `colors.subtle` | Hex kodu | `--brand-muted` CSS değişkeni |
| `typography.display` | Yazı tipi adı | Google Fonts `<link>` + Tailwind keyfi değeri |
| `typography.body` | Yazı tipi adı | Google Fonts `<link>` + Tailwind keyfi değeri |
| `voice.tone` | Açıklama | Dosya başı HTML yorumu + kopya üretimini şekillendirir |
| `voice.avoid` | Kelime listesi | Yasak listeye eklenir |
| `voice.use` | Kelime listesi | Kopya oluştururken tercih edilir |
| `positioning` | Tek satırlık | Kahraman alt başlık yönünü belirler |
| `business_model` | `ecom` veya `lead_gen` | Adım 3 rota geçersiz kılma |

## Marka DNA'sı belge formatı

`reklam-fabrikasi-brand-dna` becerisi, bu tokenları yapılandırılmış bölümler içinde görünür şekilde içeren HTML belgeleri üretir. Bunları çıkar. Marka DNA'sı ham metin veya markdown olarak sağlanmışsa şu etiketli bölümleri ara:

- "Renk paleti" veya "Marka renkleri"
- "Tipografi" veya "Tip sistemi"
- "Ses ve ton"
- "Konumlandırma"
- "İş modeli"

Dosya HTML ise tokenlar genellikle `<dl>` tanım listelerinde, `<table>` satırlarında veya `<code>` etiketleri içindeki hex kodlarında bulunur. Toleranslı bir şekilde ayrıştır; amaç değerleri ortaya çıkarmak, şemayı zorla uygulamak değil.

Gerekli bir alan eksikse (birincil renk hex'i, ekran yazı tipi, gövde yazı tipi) devam etmeyi reddet. Hangi alanın eksik olduğunu yazdır ve kullanıcıdan bunu Marka DNA'sı belgesine eklemesini ya da `/reklam-fabrikasi:brand-dna` becerisini yeniden çalıştırmasını iste.

## Ayrıştırma kilitlenmeden önce onay adımı

Çıkarımın ardından ayrıştırılan değerleri kullanıcıya şu formatta yazdır:

```
Marka DNA'sından ayrıştırıldı:
  Renkler: birincil <#XXXXXX>, vurgu <#XXXXXX>, mürekkep <#XXXXXX>, kağıt <#XXXXXX>, soluk <#XXXXXX>
  Yazı tipleri: ekran <Ad>, gövde <Ad>
  Ses tonu: <tek satır>
  Ses kaçın listesi: <virgülle ayrılmış veya "yok">
  İş modeli: <ecom / lead_gen / bildirilmemiş>
```

Tek soru sor: "Doğru görünüyor mu? `evet` ya da düzeltilecek şeyi yaz." `evet` cevabında devam et. Başka bir cevap aldığında düzeltmeyi kabul et ve yeniden ayrıştır.

## Renk tokeni enjeksiyonu

Tokenları `<head>` içinde bir `<style>` bloğunun üst kısmına yerleştir:

```html
<style>
  :root {
    --brand-primary: #1E40AF;
    --brand-accent: #F59E0B;
    --brand-ink: #0F172A;
    --brand-paper: #FAFAF7;
    --brand-muted: #94A3B8;
  }
</style>
```

Tokenları sayfa genelinde Tailwind keyfi değerleri aracılığıyla kullan:

- Bölüm arka planları için `bg-[var(--brand-paper)]`
- Gövde metni için `text-[var(--brand-ink)]`
- Vurgu metni için `text-[var(--brand-primary)]`
- Birincil CTA butonları için `bg-[var(--brand-accent)]`
- Hafif ayırıcılar için `border-[var(--brand-muted)]/20`

Tailwind 3.4 Play CDN, CSS değişkenleriyle keyfi değerleri yerel olarak destekler. Yapılandırma uzantısı gerekmez.

## Yazı tipi tokeni enjeksiyonu

Adım 1: `<head>` içine Google Fonts `<link>` ekle:

```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=DISPLAY_NAME:wght@600;700;800&family=BODY_NAME:wght@400;500;600&display=swap" rel="stylesheet">
```

`DISPLAY_NAME` ve `BODY_NAME` yerlerini Marka DNA'sının yazı tipleriyle değiştir; boşluklar için URL kodlaması olarak `+` kullan.

Adım 2: Tailwind keyfi değerleri aracılığıyla uygula:

```html
<h1 class="font-['Display_Name'] text-5xl md:text-7xl font-bold">...</h1>
<p class="font-['Body_Name'] text-base leading-relaxed">...</p>
```

## Yazı tipi yedek stratejisi

Marka DNA'sı Google Fonts'ın sunmadığı bir yazı tipi adlandırıyorsa şu sırayla yedekleme yap:

1. En yakın Google Fonts eşdeğerine bak. "Proxima Nova" için "Mulish", "Calibre" için "Inter", "Brown" için "Manrope".
2. Google Fonts eşdeğeri yoksa yazı tipi kategorisiyle eşleşen sistem yığınını kullan:
   - Editoryal serif: `Georgia, "Times New Roman", serif`
   - Modern sans: `system-ui, -apple-system, "Segoe UI", sans-serif`
   - Geometrik sans: `Manrope, system-ui, sans-serif`
   - Monospace: `ui-monospace, "Courier New", monospace`
3. Kullanıcının bunu görmesi için dosyanın başına bir HTML yorumuna ikame kaydı düş:

   ```html
   <!-- Yazı tipi notu: Marka DNA'sı Google Fonts'ta bulunmayan "Calibre" belirtti. En yakın eşleşme olarak Inter ile ikame edildi. Calibre lisanslanıyorsa <link> etiketini ve font-['Inter'] sınıflarını değiştir. -->
   ```

## Ses bloğu uygulaması

Marka DNA'sındaki ses bloğu kopya üretimini şekillendirir. Uygula:

1. **Ton tanımlayıcı.** Tüm kopya için yazı tonunu belirle. Ses "direkt, jargon yok, ikinci şahıs, esprili" diyorsa her cümle bunu yansıtır.
2. **Kaçın listesi.** Genel yasak listeye ekle. Varsayılan yasak liste ve marka yasak listesinin her ikisi de uygulanır.
3. **Kullan listesi.** Kopya üretimini bu kelimelere doğru yönlendir. Zorla değil, ama doğal bir uyum olduğunda tercih edilir.
4. **Marka DNA'sından örnek cümleler.** Marka DNA'sı 3 örnek cümle gösteriyorsa kopya onlara benzer duyulmalıdır.

## Yapay zeka klişesi kurallarında marka geçersiz kılma

Bu, 34 klişe için kritik sarmalayıcı kuraldır.

**Marka DNA'sı her zaman 34 klişeyi geçersiz kılar.** Marka DNA'sı açıkça şunları bildiriyorsa:

- Gövde yazı tipi olarak Inter: Tell 9 işaretlese de Inter kullan.
- Kahraman işlemi olarak mor gradyan: Tell 1 işaretlese de kullan.
- Ortalanmış kahraman hizalaması: Tell 18 asimetriği tercih etse de kullan.

34 klişe YALNIZCA beyan edilmemiş tercihler için geçerlidir. Marka, beyan edilen tercihler için doğruluğun kaynağıdır.

**Uygulama.** `references/34-tells.md` dosyasından herhangi bir klişeyi uygulamadan önce Marka DNA'sının bu tercihi açıkça beyan edip etmediğini kontrol et. Evet ise marka kazanır. Hayır ise klişeyi uygula.

## Token limitleri

Sayfadaki maksimum tokenlar:

- 5 renk tokeni (birincil, vurgu, mürekkep, kağıt, soluk)
- 2 yazı tipi ailesi (1 ekran + 1 gövde)
- 1 tutarlı boşluk ölçeği (Tailwind varsayılanları, 4 / 8 / 16 / 24 / 32 / 48 / 64 / 96 / 128)

Bu sınırları aşmak görsel sapmaya yol açar. Açık bir beyan olmadan daha fazlasını talep eden Marka DNA'sını reddet. Marka meşru olarak daha fazlasına sahipse (premium lüks bir marka 7 renge sahip olabilir), temel olmayan marka renklerini mevcut tokenlara eşleyerek 5'e indir.

## Değişmez kurallar

1. Sayfada kullanılan her renk 5 tokenden birinden gelmek zorundadır. Tek seferlik hex kodları yok.
2. Her metin elemanı 2 yazı tipi ailesinden birini kullanır. Üçüncü yazı tipi yok.
3. Boşluk Tailwind varsayılan ölçeğini izler. Keyfi `mt-7` sonra `mt-11` kullanımı yok.
4. Marka DNA'sında gerekli bir token eksikse (birincil renk veya herhangi bir yazı tipi), devam etmeyi reddet ve kullanıcıdan bunu eklemesini iste.
5. Marka DNA'sı 34 klişeyle çelişiyorsa marka kazanır. Geçersiz kılmayı dosyanın başındaki bir HTML yorumuna belgele.
