---
description: Kullanıcıyı karşılar, entegre becerileri aşamalara göre gruplayıp listeler ve her zaman açık rehber olarak /next komutuna yönlendirir. İlk çalıştırma tespiti proje bazlıdır (çalışılan klasöre göre), bu yüzden yeni bir müşteri klasörü açmak her zaman yeni proje karşılamasını tetikler.
---

# /welcome

Reklam Fabrikası eklentisi içinde çalışıyorsun. Kullanıcı az önce `/welcome` yazdı. Aşağıdakileri Bash ve Read araçlarıyla kendin yap.

1. İlk çalıştırma tespiti proje bazlıdır. Read aracıyla `$(pwd)/Reklam Fabrikası/_meta/state.json` dosyasını okumayı dene.

   - Dosya yoksa, burası yeni bir proje klasörüdür.
   - Varsa, burası daha önce çalışılmış bir proje klasörüdür. `last_completed_at` değerini not al.

2. Kullanıcıyı karşıla:

   - **Yeni proje klasörü:** "Reklam Fabrikası'na hoş geldin. Burası yeni bir proje klasörü gibi görünüyor. Hangi marka üzerinde çalışıyoruz?" Ardından VOC ve Marka DNA'sını paralel başlatmayı öner: "Marka adını ve ürün URL'sini verir vermez `reklam-fabrikasi-voc` ile `reklam-fabrikasi-brand-dna` becerilerini birlikte başlatabilirim."
   - **Mevcut proje klasörü:** Marka adını `$(pwd)/Reklam Fabrikası/02_Brand_DNA/` içindeki en yeni dosyadan çıkarmayı dene (varsa, dosya adı genelde marka slug'ını içerir), yoksa çalışılan klasör adına geri düş. Sonra şunu söyle: "Tekrar hoş geldin. Bu proje klasöründeki son işlem `<last_completed_at>` tarihindeydi. Kaldığın yerden devam etmek mi istersin, yoksa yeni bir şey mi başlatalım?"

3. Becerileri iş akışı aşamasına göre gruplayarak listele. Her beceri için bir cümlelik kısa madde işaretli liste kullan.

   **Araştırma, paralel çalıştır:**
   - `reklam-fabrikasi-voc`, incelemelerden, forumlardan ve sosyal medyadan müşteri sesi araştırması
   - `reklam-fabrikasi-brand-dna`, Playwright renk örneklemesiyle canlı marka DNA'sı
   - `reklam-fabrikasi-spy`, statik reklam swipe dosyaları için Meta Ad Library kazıyıcısı
   - `reklam-fabrikasi-ugc-scraper`, viral TikTok UGC kazıyıcısı

   **Kadro ve materyal hazırlığı, marka DNA'sından sonra:**
   - `reklam-fabrikasi-character`, çalıştırma başına 1 ila 10 marka karakteri, eşleşen vesikalık artı tam boy kadro görseli, her reklamda yüz tutarlılığı için karakter başına `11_Characters/` altında kaydedilir
   - `reklam-fabrikasi-product-shot`, tek bir ana çekimden hareketle açı, karakter, arka plan ve etkileşim değişimleri için v1 sonrası döngüyle stüdyo, elde tutulan veya kullanılan ürün çekimleri

   **Kreatif üretim, araştırmadan sonra:**
   - `reklam-fabrikasi-static`, kanıta dayalı statik reklam konsept sistemi. Markanın son 20 canlı Meta reklamını Apify ile kazır, Marka DNA'sı ve VOC verisini işler, strateji motorunu web aramasıyla çalıştırır, onayla/reddet/düzenle için sohbette 6 ila 10 konsept sunar, sonra onaylanan her konsept için 5 görsel ailesi boyunca 5 GPT Image 2 render prompt'u yazar. Yalnızca GPT Image 2. Dört üretim yolu.
   - `reklam-fabrikasi-ugc-prompt`, bir UGC senaryosundan dört üretim yollu 6 Seedance 2.0 video prompt'u, kayıtlı bir karakter varsa onu 6 varyantın tamamına kilitler

   **Optimizasyon yan döngüleri:**
   - `reklam-fabrikasi-multiplier`, kazanan bir statik reklamın dört yollu 5 ila 8 varyasyonu
   - `reklam-fabrikasi-rebuild`, bir rakip reklamını dört yolla yeniden inşa et

   **Dağıtım:**
   - `reklam-fabrikasi-copy`, Meta reklam başlıkları, açıklamaları, ana metni

   **Hedef:**
   - `reklam-fabrikasi-landing-page`, kazanan reklamından, Marka DNA'sından ve VOC verisinden tek dosyalık HTML açılış sayfası, mesaj uyumu zorlaması ve 34 maddelik yapay zeka klişesi karşıtı öz denetim ile

   **Canlı Meta Reklamları:**
   - `reklam-fabrikasi-meta-handoff`, proje bağlamını (Marka DNA'sı, VOC, metin, reklam spesifikasyonu) Meta'nın resmi Ads MCP'si için (claude.ai web uygulamasında çalışan, mcp.facebook.com/ads adresindeki) yapıştırmaya hazır bir prompt'a paketler

4. Kısayol komutlarından ve çoklu marka projelerinin nasıl çalıştığından bahset:
   - `/next` bu proje klasöründe tamamladıklarına göre en iyi tek sonraki adımı önerir
   - `/doctor` bir şey ters görünüyorsa tanılama çalıştırır
   - `/setup` bir kerelik makine kurulumunu yeniden çalıştırır (tekrar çalıştırması güvenli)
   - `/setup-fal-ai` Yol C'ye ilk ulaştığında Fal AI anahtarını adım adım ekler
   - `/reklam-fabrikasi:meta-handoff` canlı kampanyaları analiz etmeye veya başlatmaya hazır olduğunda devir prompt'unu hazırlar
   - `/reklam-fabrikasi:landing-page` VOC ve Marka DNA'sı hazır olduğunda kazanan reklamından tek dosyalık HTML açılış sayfası kurar
   - `/reklam-fabrikasi:character` her reklamda yüz tutarlılığı için eşleşen vesikalık artı tam boy görsellerle 1 ila 10 karakterlik bir marka kadrosu kurar
   - `/reklam-fabrikasi:product-shot` hızlı açı ve sahne değişimleri için v1 sonrası döngüyle stüdyo, elde tutulan veya kullanılan ürün çekimleri üretir
   - `/open-folder` bu projenin `Reklam Fabrikası` alt klasörünü Finder veya Explorer'da açar

   static, ugc-prompt, multiplier, rebuild, character ve product-shot becerilerinin sunduğu dört üretim yolundan bahset: "Yol A manuel yapıştırmadır (ücretsiz), Yol B bir Higgsfield aboneliğin varsa Higgsfield MCP'sini kullanır (ilk kullanımda `/mcp` üzerinden tek seferlik OAuth girişi, yapıştırılacak anahtar yok), Yol C fal.ai sonuç başına ödemedir (abonelik gerekmez, `fal_api_key` ister), Yol D görsel modelin web arayüzünü Playwright ile sürer (GPT Image 2 için chatgpt.com, Nano Banana 2 için aistudio.google.com, Seedance 2.0 için higgsfield.ai)."

   Önerilen görsel modelden bahset: "GPT Image 2, yüksek kalitede ve 4K'da multiplier, rebuild, character ve product-shot genelinde önerilen görsel modeldir. static becerisi yalnızca GPT Image 2'ye sabitlenmiştir (model seçici yok). Ürün detayı, metin işleme, yüz tutarlılığı ve karmaşık prompt'larda Nano Banana 2 ve Nano Banana Pro'dan daha iyidir. Nano Banana 2, üretim başına daha düşük maliyet isteyen kullanıcılar için diğer becerilerde daha ucuz bir alternatif olarak kalır."

   Çoklu marka modelinin net olması için şu satırı ekle: "Her marka veya müşteri kendi klasörünü alır. Claude Code'u `~/Desktop/<marka>/` (veya seçtiğin herhangi bir klasör) içinde aç, eklenti ilk beceri çalıştırmasında oraya markaya özel bir `Reklam Fabrikası/` alt klasörü oluşturur."

5. Bitir:
   - **Yeni proje klasörü:** "Başlamak için `/next` yaz, ya da ne yapmak istediğini anlat."
   - **Mevcut proje klasörü:** "Bu projede şimdi ne yapacağını görmek için `/next` yaz."

Mesajı kısa tut. Emoji yok. Em-dash yok. Dolgu yok.
