# YT Kopya Sayfası

Bir **YouTube Yorum Cevaplayıcı** otomasyonunun günlük mailindeki **"Cevabı kopyala"** butonunun açtığı tek statik sayfayı barındıran minik servis. Eşli proje (yorumları okuyup cevap önerisi üreten cron) bu sayfaya bir link gönderir; sayfa o cevabı gösterir ve panoya kopyalar.

**Neden ayrı bir servis var:** HTML e-postalar JavaScript çalıştıramaz (Gmail/Apple Mail siler), yani çalışan bir "kopyala" butonu doğrudan mailin içine konamaz. Buton bir web sayfasında olmak zorunda. Bu servis o tek sayfayı (`cevap_kopyala.html`) doğru `text/html` mime ile servis eder. (Not: bazı statik dosya host'ları HTML'i güvenlik için `text/plain` döndürür ve sayfa render olmaz; bu yüzden mime'ı doğru veren küçük bir host gerekir.)

## Çalışma Şekli

Sunucusuz veri akışı: cevap metni + YouTube derin linki, mail butonundaki linkin `#d=<base64>` hash'inde taşınır. Hash istemci tarafıdır; sunucuya hiç ulaşmaz. Sayfa hash'i çözer, cevabı gösterir, "Kopyala ve YouTube'da aç" ile cevabı panoya alıp YouTube'u açar. Sunucu hiçbir veri görmez/saklamaz.

Sonuç: servisin hiçbir anahtara, DB'ye ya da env var'a ihtiyacı yok. Yanlış config'le çökemez; app-sleep (boştayken ≈$0) güvenli.

**Eşli proje (YouTube Yorum Cevaplayıcı):** Linki üreten taraf, yorum + önerilen cevabı + YouTube derin linkini bir JSON'a koyar, base64 ile kodlar ve bu sayfanın adresine `#d=<base64>` hash'i olarak ekler. Eşli projenin o servise tek bir ortam değişkeni (`YT_COPY_PAGE_URL = <bu servisin adresi>`) ile bu sayfayı tanıtması yeterlidir.

## Stack

- Python stdlib `http.server` (bağımlılık yok).

## Environment Setup

Env var YOK. `python server.py` (PORT'u Railway verir, lokalde 8080).

## Deploy

Railway RAILPACK web servisi, `rootDirectory = Projeler/YT_Kopya_Sayfa`, `sleepApplication: true`. `railway.json` hazır. Sayfa değişince `cevap_kopyala.html`'i güncelle + push (auto-deploy).
