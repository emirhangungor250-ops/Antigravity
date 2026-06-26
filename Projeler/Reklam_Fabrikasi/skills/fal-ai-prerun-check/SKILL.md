---
name: fal-ai-prerun-check
description: Yol C (Fal AI direkt API üretimi) kullanan herhangi bir iş akışından ÖNCE bu beceriyi HER ZAMAN kullan. Bu şunları kapsar: reklam-fabrikasi-static Yol C, reklam-fabrikasi-ugc-prompt Yol C, reklam-fabrikasi-multiplier Yol C, reklam-fabrikasi-rebuild Yol C veya herhangi bir açık Fal AI görsel/video üretim isteği. fal_api_key değerinin pluginConfigs.reklam-fabrikasi içinde mevcut olup olmadığını doğrula. Eksikse kullanıcıya önce /reklam-fabrikasi:setup-fal-ai çalıştırmasını söyle. Bu koruma olmadan Yol C, net bir başlangıç mesajı yerine kafa karıştırıcı 401 hatalarıyla karşılaşır.
---

# Fal AI ön çalışma kontrolü

Bu beceri bir korumadır. Statik, UGC prompt, çarpan ve yeniden oluşturma becerilerindeki Yol C üretiminden (Fal AI direkt API) önce çalışır. Eksik veya geçersiz Fal API anahtarlarını, kullanıcının akış ortasında 401 hatasıyla karşılaşması yerine net bir mesajla yakalar.

## Ne zaman çalıştırılır

Şunlardan önce otomatik olarak tetikle:
- `reklam-fabrikasi-static` Yol C (40 görsel üretimi, varsayılan model GPT Image 2, isteğe bağlı Nano Banana 2)
- `reklam-fabrikasi-ugc-prompt` Yol C (6 Seedance 2.0 video üretimi)
- `reklam-fabrikasi-multiplier` Yol C (5-8 Andromeda varyasyonu, varsayılan GPT Image 2)
- `reklam-fabrikasi-rebuild` Yol C (1 yeniden oluşturma artı isteğe bağlı 5 persona varyasyonu, varsayılan GPT Image 2)
- `reklam-fabrikasi-character` Yol C (vesikalık artı tam boy için N çarpı 2 üretim, varsayılan GPT Image 2)
- `reklam-fabrikasi-product-shot` Yol C (1 temel çekim artı döngü yinelemeleri, varsayılan GPT Image 2)
- "fal ile üret", "fal API kullan", "arayüzü atla", "görsel başı ödeme üretimi" gibi doğal dil istekleri

Kullanıcı bu oturumda zaten başarılı bir Yol C çağrısı yaptıysa kontrolü atlayabilirsin (oturumun geri kalanı için yeşil kabul et).

## Ne kontrol edilir

### 1. Anahtarın pluginConfigs içinde mevcut olması

`~/.claude/settings.json` dosyasını oku ve `pluginConfigs["reklam-fabrikasi"].fal_api_key` alanına bak. Boş olmayan bir string olmalıdır.

Eksik veya boşsa dur ve şu yanıtı ver:

> Yol C, direkt API üretimi için fal.ai kullanır ve Fal AI anahtarınız henüz ayarlanmamış. Eklemek için `/reklam-fabrikasi:setup-fal-ai` çalıştırın. Yaklaşık 30 saniye sürer. Kurulumdan sonra tekrar sorun, Yol C ile devam ederim.

İstenen iş akışına devam etme. Kullanıcı kurulumu çalıştırır, ardından tekrar sorar.

### 2. fal-ai MCP'nin listelenmiş ve erişilebilir olması

`claude mcp list` komutunu çalıştır (Bash üzerinden). `fal-ai`'nin bağlı durumuyla göründüğünü kontrol et.

`fal-ai` listede yoksa:

> fal-ai MCP sunucusu kayıtlı değil. Bu genellikle eklenti kurulumunun tamamlanmadığı anlamına gelir. Teşhis için `/reklam-fabrikasi:doctor` çalıştırın, ardından Claude Code'u yeniden yükleyin.

`fal-ai` listelenmiş ama bağlanmayı başaramamışsa:

> fal-ai MCP sunucusu başlatılamadı. En yaygın neden: `~/.claude/settings.json` dosyasındaki fal_api_key hatalı biçimlendirilmiş veya süresi dolmuş. Taze bir anahtar yapıştırmak için `/reklam-fabrikasi:setup-fal-ai` çalıştırın.

### 3. Anahtarın hâlâ çalışması (isteğe bağlı, yalnızca oturumun ilk Yol C çağrısında yap)

1. ve 2. adımlar geçerse, üretimi tetiklemeyen ucuz bir Fal endpoint'i çağırarak tek bir sağlık kontrolü yap. MCP bir model listeleme aracı sunar. Şunu çağır:

```
mcp__fal-ai__list_models
```

(veya fal-ai MCP'nin sunduğu herhangi bir yalnızca meta veri çağrısı). Fiyat listesi, kuyruk durumu veya model şeması getirme işlemleri ücretsizdir.

401 veya "Invalid API key" dönerse temiz bir şekilde göster:

> Fal AI anahtarınız şu yanıtı döndürdü: `Invalid API key`. `~/.claude/settings.json` dosyasındaki anahtar yanlış veya iptal edilmiş. https://fal.ai/dashboard/keys adresinden taze bir anahtar yapıştırmak için `/reklam-fabrikasi:setup-fal-ai` çalıştırın.

429 (hız sınırı) ise: fal hesabının hız sınırına ulaştığını söyle, bir dakika bekle, tekrar dene.

Kontrol başarılı olursa sonucu kullanıcıya gösterme (yalnızca sağlık kontrolü). İstenen iş akışına sessizce devam et.

## Kontrol sonrası

Üç adımın tümü geçerse istenen becerinin Yol C bölümüne aktar. "Ön çalışma kontrolü geçti" diye anlatma. Devam et.

## Katı kurallar

1. **Asla atlatma.** Kullanıcı ne derse desin, anahtar eksikken Yol C'nin çalışmasına izin verme. Önce kurulumu çalıştırmalarını iste.
2. **Anahtarı hiçbir zaman tam olarak gösterme.** Teşhis için settings.json içeriğini gösterirken anahtarı ilk-4 + son-4 şeklinde `[ORTA KISIM GİZLİ]` ile gizle. Örnek: `fal_a1b2[ORTA KISIM GİZLİ]9z8y`.
3. **Anahtarları asla otomatik düzeltme.** Kullanıcı adına anahtar yapıştırma, kopyalama veya yazma. Kendi anahtarlarını `/setup-fal-ai`'ye yapıştırırlar, biz de bunu harness üzerinden saklarız.
4. **Kısa ol.** Bu beceri bir kapıdır, rehber değil. Bir şey başarısız olursa tek satır kök neden ve tek satır düzeltme komutu ver. Tam kurulum rehberi `/reklam-fabrikasi:setup-fal-ai` içindedir.
