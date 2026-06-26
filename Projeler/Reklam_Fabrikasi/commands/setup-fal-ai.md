---
description: Fal AI API anahtarı için etkileşimli kurulum. Kullanıcıyı fal.ai'den anahtar alma sürecinde yönlendirir, ~/.claude/settings.json içinde pluginConfigs.reklam-fabrikasi.fal_api_key altına yapıştırır, sonra ücretsiz bir metadata çağrısıyla bağlantıyı test eder.
---

# /setup-fal-ai

Reklam Fabrikası eklentisi içinde çalışıyorsun. Kullanıcı az önce `/setup-fal-ai` yazdı. Onu bir Fal AI API anahtarı almaya yönlendir, `~/.claude/settings.json` içinde `pluginConfigs["reklam-fabrikasi"].fal_api_key` altına kaydet, sonra bağlantıyı test et.

Her kabuk işlemi için Bash aracını kullan. `settings.json` için Read ve Write araçlarını kullan. Kullanıcıdan kendi terminalinde komut çalıştırmasını asla isteme, Bash ile sen çalıştır.

## Adım 0: Buna neden ihtiyacımız var

Şu mesajı aynen gönder:

> Yol C'yi (Fal AI doğrudan API) kullanmak için Fal AI API anahtarına ihtiyacım var.
>
> Yol C, eklentinin görselleri ve videoları doğrudan fal.ai'nin API'si üzerinden üretmesini sağlar, arayüz aboneliği gerekmez. Sonuç başına ödeme, fal.ai tarafından faturalandırılır. static, ugc-prompt, multiplier ve rebuild becerilerinde kullanılır.
>
> https://fal.ai/dashboard/keys adresini aç, `+ Add Key` butonuna tıkla, adını `reklam-fabrikasi` koy, anahtarı kopyala, buraya yapıştır.
>
> Hazır mısın? Anahtar elindeyse yanıt olarak yapıştır, ya da atlamak için `cancel` yaz.

`cancel` derlerse zarif şekilde çık ve Yol C istediklerinde `/setup-fal-ai` komutunu yeniden çalıştırmalarını söyle.

## Adım 1: Anahtarı topla

Kullanıcı bir değer yapıştırdığında:

1. Baştaki ve sondaki boşlukları kırp.
2. Doğrula: Fal anahtarları genelde uzun bir alfanümerik dizedir. 20 karakterden kısaysa ya da içinde boşluk varsa reddet.
3. Yerel bir değişkende sakla. Anahtarı düz metin olarak YAZDIRMA. Onay için kullanıcıya geri gösterirken ilk 4 ve son 4 hariç gizle: `fal_a1b2[GİZLİ]9z8y`.

Doğrulama başarısız olursa şunu söyle:

> Bu bir Fal AI anahtarına benzemiyor (çok kısa ya da boşluk içeriyor). https://fal.ai/dashboard/keys adresini aç, tam anahtarı kopyala, tekrar yapıştır.

Geçerli görünen bir anahtar alana kadar ya da kullanıcı `cancel` diyene kadar döngüde kal.

## Adım 2: Bağlantıyı test et

Kaydetmeden önce, anahtarın gerçekten çalıştığını doğrula. Üretimi TETİKLEMEYEN ucuz bir Fal uç noktası kullan. Fal HTTP API'si bir kuyruk/durum uç noktası ve bir model listeleme uç noktası sunar. curl ile çalıştır, anahtarı asla yazdırma:

```
KEY="<the pasted value>"
HTTP_CODE=$(curl -s -o /tmp/fal-probe.json -w "%{http_code}" \
  -H "Authorization: Key ${KEY}" \
  "https://queue.fal.run/openai/gpt-image-2/status")
echo "HTTP: ${HTTP_CODE}"
```

(Birebir değerin kaydedilen komut çıktısında görünmemesi için anahtarı kabuk ortamına `printf` veya heredoc ile enjekte et. Herhangi bir modelin durum uç noktası metadata ile 200 ya da hatayla 401 döner, ikisi de ucuzdur. gpt-image-2 uç noktasını test ediyoruz çünkü eklentinin önerilen varsayılan modeli budur.)

Üç sonuç:

- **HTTP 200 veya 422** (uç nokta kimliği kabul etti ama request_id yoktu, kimlik doğrulama testi için bu sorun değil): `Fal AI anahtarı çalışıyor.` yazdır.
- **HTTP 401**: `Bu anahtar 401 Unauthorized döndürdü. Anahtar ya yanlış kopyalandı, ya iptal edildi ya da fal.ai hesabın aktif değil. Tekrar dene.` yazdır. Adım 1'e dön.
- **HTTP 5xx veya ağ hatası**: `Fal AI <code> döndürdü. Geçici bir kesinti olabilir. Canlı testi atlayayım mı? (yes yine de kaydeder, no iptal eder).` yazdır. Yes ise anahtarı doğrulamadan kaydet. No ise iptal et.

## Adım 3: settings.json'a yaz

`~/.claude/settings.json` dosyasını oku. Yoksa `{}` ile oluştur. Varsa JSON'u ayrıştır.

Anahtarı `pluginConfigs["reklam-fabrikasi"]` içine birleştir. Mevcut değerleri, özellikle `apify_api_key` değerini koru:

```json
{
  "pluginConfigs": {
    "reklam-fabrikasi": {
      "fal_api_key": "<the key>",
      "apify_api_key": "<existing if any>"
    }
  }
}
```

Atomik yaz. Strateji: önce `~/.claude/settings.json.tmp` dosyasına yaz, geçerli JSON olarak ayrıştığını doğrula, sonra orijinalin üzerine `mv` ile taşı. Bu, yazma kesintiye uğrarsa bozuk bir settings dosyası bırakmayı önler.

```
TMP="$HOME/.claude/settings.json.tmp"
# (write JSON via Write tool to $TMP, then validate)
python3 -c "import json,sys; json.load(open('${TMP}'))" && mv "$TMP" "$HOME/.claude/settings.json"
```

Doğrulama başarısız olursa `settings.json güvenli şekilde yazılamadı. /setup-fal-ai komutunu tekrar çalıştır ya da ~/.claude/settings.json izinlerini kontrol et.` yazdır ve dur. Yarım dosya bırakma.

## Adım 4: Onayla ve sırada ne olduğunu söyle

Yazdır:

> Fal AI anahtarı kaydedildi (`<ilk-4>[GİZLİ]<son-4>`).
>
> fal-ai MCP'si anahtarı bir sonraki oturumda alır. Yeniden başlatmadan şimdi aktive etmek için, herhangi bir Yol C üretimine yapılan ilk çağrı onu kullanır.
>
> Kurulumun tamam. Hazır olduğunda şunlardan herhangi birini çalıştır:
> - 40 görsel üretimi için `/create static ads` sonra Yol C'yi seç (varsayılan model yüksek kalitede ve 4K'da GPT Image 2, Nano Banana 2 daha ucuz alternatif olarak sunulur)
> - 6 Seedance 2.0 video üretimi için `/ugc-prompt` sonra Yol C
> - 5 ila 8 reklam varyasyonu için `/multiply` sonra Yol C (aynı GPT Image 2 varsayılanı)
> - bir rakip reklamını yeniden oluşturmak için `/rebuild` sonra Yol C (aynı GPT Image 2 varsayılanı)
> - marka karakterleri üretmek için `/reklam-fabrikasi:character` sonra Yol C (aynı GPT Image 2 varsayılanı)
> - ürün çekimleri üretmek için `/reklam-fabrikasi:product-shot` sonra Yol C (aynı GPT Image 2 varsayılanı)
>
> Anahtarı güncellemek için istediğin zaman `/setup-fal-ai` komutunu tekrar çalıştır.

## Katı kurallar

1. **Anahtarı hiçbir yerde düz metin yazdırma.** Kullanıcıya dönen çıktıda her zaman gizle. Bash aracının kaydı yerel kaldığı için sorun değil.
2. **Doğrulama başarısızsa asla devam etme.** Dur ve tekrar yapıştırmasını iste.
3. **Diğer ayarların üzerine asla yazma.** Her zaman oku, birleştir, atomik yaz.
4. **Kullanıcıdan kabuk komutunu kendisinin çalıştırmasını asla isteme.** Her zaman Bash ile sen çalıştır. Kullanıcılar teknik değil.
5. **Em-dash yok.** Virgül, "ve" kullan ya da cümleyi böl.
