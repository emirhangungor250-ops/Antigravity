---
description: Apify API anahtarı için etkileşimli kurulum. Kullanıcıyı console.apify.com'dan Personal API token alma sürecinde yönlendirir, canlı olarak doğrular, sonra ~/.claude/settings.json içinde pluginConfigs.reklam-fabrikasi.apify_api_key altına kaydeder. ugc-scraper ve spy becerileri kullanır.
---

# /setup-apify

Reklam Fabrikası eklentisi içinde çalışıyorsun. Kullanıcı az önce `/setup-apify` yazdı. Onu bir Apify Personal API token almaya yönlendir, canlı doğrula, `~/.claude/settings.json` içinde `pluginConfigs["reklam-fabrikasi"].apify_api_key` altına kaydet, sonra Claude'u yeniden başlatmasını söyle.

Her kabuk işlemi için Bash aracını kullan. `settings.json` için Read ve Write araçlarını kullan. Kullanıcıdan kendi terminalinde komut çalıştırmasını asla isteme, Bash ile sen çalıştır.

## Adım 0: Buna neden ihtiyacımız var

Şu mesajı aynen gönder:

> UGC kazıyıcısını veya reklam casusu becerilerini kullanmak için Apify API token'ına ihtiyacım var.
>
> Apify, viral TikTok UGC'lerini ve Meta Ad Library'den rakip reklamlarını çekmek için kullandığımız kazıma platformu. Ücretsiz katman ayda 5 dolarlık kredi içeriyor, yani yaklaşık 90 /ugc-scrape çalıştırması ve bolca /spy çalıştırması.
>
> https://console.apify.com/account/integrations adresini aç, gerekirse ücretsiz kaydol, Personal API token'ını kopyala. Token `apify_api_` ile başlar.
>
> Hazır mısın? Token elindeyse yanıt olarak yapıştır, ya da atlamak için `cancel` yaz.

`cancel` derlerse zarif şekilde çık ve UGC kazıma veya reklam casusu istediklerinde `/setup-apify` komutunu yeniden çalıştırmalarını söyle.

## Adım 1: Token'ı topla

Kullanıcı bir değer yapıştırdığında:

1. Baştaki ve sondaki boşlukları kırp.
2. Ön eki doğrula: bir Apify Personal API token her zaman birebir `apify_api_` dizesiyle başlar. Başlamayanı reddet.
3. Uzunluğu doğrula: en az 20 karakter olmalı ve içinde boşluk olmamalı.
4. Yerel bir kabuk değişkeninde sakla. Token'ı düz metin olarak YAZDIRMA. Onay için kullanıcıya geri gösterirken ilk 4 ve son 4 hariç gizle: `apif[GİZLİ]9z8y`.

Doğrulama başarısız olursa şunu söyle:

> Bu bir Apify Personal API token'ına benzemiyor. Token'lar `apify_api_` ile başlar, boşluksuz ve en az 20 karakterdir. https://console.apify.com/account/integrations adresini aç, tam Personal API token'ı kopyala, tekrar yapıştır.

Geçerli görünen bir token alana kadar ya da kullanıcı `cancel` diyene kadar döngüde kal.

## Adım 2: Token'ı canlı doğrula

Bir şey kaydetmeden önce, token'ın Apify REST API'sine karşı gerçekten çalıştığını doğrula. Kimliği doğrulanmış kullanıcının hesap profilini döndüren ve hiçbir maliyeti olmayan ucuz `/v2/users/me` uç noktasını kullan. Apify MCP HTTP sunucusu aynı `Authorization: Bearer <token>` başlık biçimini beklediği için, burada 200 dönmesi MCP'nin de kabul edeceği anlamına gelir.

curl ile çalıştır, anahtarı asla yazdırma:

```
KEY="<the pasted value>"
HTTP_CODE=$(curl -s -o /tmp/apify-probe.json -w "%{http_code}" \
  -H "Authorization: Bearer ${KEY}" \
  "https://api.apify.com/v2/users/me")
echo "HTTP: ${HTTP_CODE}"
```

(Birebir değerin kaydedilen komut satırına düşmemesi için heredoc veya pipe kullan. `users/me` uç noktası profil JSON'u ile 200 ya da yapılandırılmış bir hatayla 401 döner.)

Üç sonuç:

- **HTTP 200**: `/tmp/apify-probe.json` içinden `data.username` ve `data.plan` değerlerini ayrıştır. `Apify token çalışıyor. Hesap: <username>, plan: <plan>.` yazdır. Adım 3'e geç.
- **HTTP 401**: `Bu token 401 Unauthorized döndürdü. Token ya yanlış kopyalandı, ya iptal edildi ya da Apify hesabın aktif değil. Tekrar dene.` yazdır. Adım 1'e dön.
- **HTTP 5xx veya ağ hatası**: `Apify <code> döndürdü. Geçici bir kesinti olabilir. Canlı testi atlayayım mı? (yes yine de kaydeder, no iptal eder).` yazdır. Yes ise anahtarı doğrulamadan kaydet. No ise iptal et.

## Adım 3: settings.json'a yaz

`~/.claude/settings.json` dosyasını oku. Yoksa `{}` ile oluştur. Varsa JSON'u ayrıştır.

Anahtarı `pluginConfigs["reklam-fabrikasi"]` içine birleştir. Mevcut değerleri, özellikle `fal_api_key` değerini koru:

```json
{
  "pluginConfigs": {
    "reklam-fabrikasi": {
      "apify_api_key": "<the token>",
      "fal_api_key": "<existing if any>"
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

Doğrulama başarısız olursa `settings.json güvenli şekilde yazılamadı. /setup-apify komutunu tekrar çalıştır ya da ~/.claude/settings.json izinlerini kontrol et.` yazdır ve dur. Yarım dosya bırakma.

Claude Code çalışma zamanı `sensitive: true` olarak işaretli alanları macOS ve Windows'ta OS keychain'inde, keychain'in olmadığı Linux'ta ise `~/.claude/.credentials.json` içinde saklar. Düz metin token asla `~/.claude.json` içine düşmez ve bu eklenti dışında hiçbir şey tarafından görülmez.

## Adım 4: Onayla ve sırada ne olduğunu söyle

Yazdır:

> Apify token kaydedildi (`<ilk-4>[GİZLİ]<son-4>`).
>
> apify MCP'sinin token'ı alması için Claude'u tamamen kapat (Mac'te Cmd+Q, sonra yeniden aç, ya da IDE'ni yeniden başlat). MCP, değeri başlangıçta `Authorization: Bearer` başlığı olarak yükler.
>
> Yeniden yükledikten sonra şunlardan herhangi birini çalıştırabilirsin:
> - /ugc senaryo yazarı için 25 viral TikTok UGC transkripti çekmek üzere `/ugc-scrape`
> - Meta Ad Library'den rakip statik reklamları çekmek üzere `/spy`
>
> Token'ı güncellemek için istediğin zaman `/setup-apify` komutunu tekrar çalıştır.

## Katı kurallar

1. **Token'ı hiçbir yerde düz metin yazdırma.** Kullanıcıya dönen çıktıda her zaman gizle. Bash aracının kaydı yerel kalır.
2. **Doğrulama başarısızsa asla devam etme.** Dur ve tekrar yapıştırmasını iste.
3. **Diğer ayarların üzerine asla yazma.** Her zaman oku, birleştir, atomik yaz.
4. **Kullanıcıdan kabuk komutunu kendisinin çalıştırmasını asla isteme.** Her zaman Bash ile sen çalıştır. Kullanıcılar teknik değil.
5. **Token'ı asla URL sorgu dizesine koyma.** Apify MCP'si aynı uç noktada `Authorization: Bearer` başlık kimlik doğrulamasını destekler, ki bu MCP yetkilendirme spesifikasyonunun önerdiği biçimdir. URL'ye gömülü token'lar kabuk geçmişine, log dosyalarına ve diskteki `~/.claude.json` dosyasına sızar.
6. **Em-dash yok.** Virgül, "ve" kullan ya da cümleyi böl.
