---
description: En iyi tek sonraki iş akışı adımını önermek için chain-map.json'ı, mevcut projenin state.json dosyasını ve "Reklam Fabrikası" klasörünün değişiklik zamanlarını okur. Proje bazlıdır (çalışılan klasöre göre).
---

# /next

Reklam Fabrikası eklentisi içinde çalışıyorsun. Kullanıcı az önce `/next` yazdı. Claude Code'un şu an açık olduğu proje klasörüne göre, en iyi tek sonraki adımı ve varsa paralel fırsatları öner.

Çıktı modeli proje bazlıdır: her çalışılan klasör kendi "Reklam Fabrikası" alt klasörünü alır. Yani `/next`, ev klasörünün değil, mevcut klasörün durumunu ve çıktılarını okur.

Aşağıdakileri Bash ve Read araçlarıyla kendin yap (kullanıcıdan terminalde asla bir şey çalıştırmasını isteme):

1. Proje kökünü çöz:

   ```
   RFLAB="$(pwd)/Reklam Fabrikası"
   ```

2. `${CLAUDE_PLUGIN_ROOT}/scripts/chain-map.json` dosyasını oku (girdiler, çıktılar, paralellik, çıktı klasörü, requires_mcp ile tam beceri grafiği).

3. Varsa `$RFLAB/_meta/state.json` dosyasını okumayı dene. `last_completed_at` değerini not al. Dosya yoksa, burası yeni bir proje klasörüdür.

4. Bash ile her numaralı alt klasördeki artı `_assets/product-shots` klasöründeki dosyaları say (proje bazlı):

   ```
   for d in "$RFLAB"/[0-9]*; do
     [ -d "$d" ] || continue
     count=$(ls -1 "$d" 2>/dev/null | grep -v '^\.' | wc -l | tr -d ' ')
     echo "$(basename "$d"): $count files"
   done
   if [ -d "$RFLAB/_assets/product-shots" ]; then
     count=$(ls -1 "$RFLAB/_assets/product-shots" 2>/dev/null | grep -v '^\.' | wc -l | tr -d ' ')
     echo "_assets/product-shots: $count folders"
   fi
   ```

   `[0-9]*` glob'u `10_Landing_Pages` ve `11_Characters` dahil her numaralı klasörü eşler. Önceki `0*` glob'u 1 veya daha yüksekle başlayan klasörleri sessizce atlıyordu, yani 09'dan sonraki her şeyi kaçırıyordu. İçinde dosya olan klasörler kullanıcının o aşamayı bu projede yaptığı anlamına gelir. Boş veya eksik klasörler hâlâ bekliyor demektir. `$RFLAB` henüz yoksa her aşamayı boş kabul et ve araştırma aşamasını öner.

5. Sonraki adımı bulmak için beceri haritasını uygula:

   **Bu klasörde ilk çalıştırma ($RFLAB yok veya hiçbir aşamada dosya yok):**
   > Burası yeni bir proje klasörü gibi görünüyor. Araştırma aşaması üç beceriyi paralel çalıştırır:
   > - müşteri sesi araştırması için `reklam-fabrikasi-voc`
   > - marka DNA'sı çıkarımı için `reklam-fabrikasi-brand-dna`
   > - rakip reklam kütüphanesi araştırması için `reklam-fabrikasi-spy`
   >
   > Girdisi hangisinde varsa onu seç ve "[ürün] için VOC yapalım" de. Çalıştırdığın ilk beceri, bu klasörün çıktıları kaydetmek için doğru yer olduğunu teyit eder.

   **Araştırma bitti (01, 02, 03'te dosya var), kadro veya ürün çekimi yok (11, _assets/product-shots boş):**
   > Bu klasörde VOC ve Marka DNA'sı bitti. Yüz tutarlılığının önemli olduğu ücretli trafik için sonraki adım materyal hazırlığıdır:
   > - eşleşen vesikalık ve tam boy görsellerle 1 ila 10 karakterlik bir marka kadrosu kurmak için `reklam-fabrikasi-character`. Her reklamda aynı yüzü kilitler.
   > - temiz bir stüdyo, elde tutulan veya kullanılan ürün çekimi (isteğe bağlı olarak kayıtlı karakterlerden biriyle) üretmek için `reklam-fabrikasi-product-shot`.
   >
   > Materyal hazırlığı isteğe bağlı ama önerilir. Yüz veya ürün tutarlılığına ihtiyacın yoksa doğrudan kreatife geçebilirsin. "Marka kadromu kur" veya "bana temiz bir ürün çekimi yap" diye dene.

   **Araştırma bitti (01, 02, 03'te dosya var), henüz kreatif yok (04, 06 boş):**
   > Bu klasörde VOC ve Marka DNA'sı bitti. İki kreatif beceri artık paralel çalışabilir:
   > - kanıta dayalı statik reklam konseptleri için `reklam-fabrikasi-static`. Beceri markanın son 20 canlı Meta reklamını Apify ile kazır, strateji motorunu çalıştırır, sohbette onayla/reddet/düzenle için 6 ila 10 konsept sunar, sonra onaylanan her konsept için 5 görsel ailesi boyunca 5 GPT Image 2 render prompt'u yazar. Yalnızca GPT Image 2'ye sabitlenmiştir. Dört üretim yolu (A manuel yapıştırma, B Higgsfield CLI, C fal.ai, D Playwright).
   > - hazır bir UGC senaryon varsa `reklam-fabrikasi-ugc-prompt` (dört üretim yolu). Önce `/reklam-fabrikasi:character` çalıştırdıysan, beceri ücretli trafikte yüz tutarlılığı için kayıtlı karakteri 6 video varyantının tamamına kilitler.
   >
   > Statik daha hızlı yayına çıkar. "Bana sonraki statik reklam konseptlerimi kur" diye dene.

   **Kreatif bitti, metin yok:**
   > Kreatif yayında. Materyallerinin herhangi biri için Meta spesifikasyonuna uygun başlıklar, açıklamalar ve ana metin üretmek için `reklam-fabrikasi-copy` çalıştır. "Statik reklamım için metin yaz" diye dene.

   **Bir kazanan var (kullanıcının en az bir başarılı statiği var):**
   > Ölçeklendirme zamanı. İki yan döngü paralel çalışır:
   > - 5 ila 8 Andromeda uyumlu varyasyon yapmak için `reklam-fabrikasi-multiplier`
   > - bir rakip reklamını yeniden inşa etmek için `reklam-fabrikasi-rebuild`
   >
   > "Kazanan reklamımı çoğalt" diye dene.

   **Canlı kampanyalara hazır:**
   > Kreatifin, metnin ve bir stratejin var. Canlı kampanya işi, Meta'nın resmi Ads MCP'sinin (mcp.facebook.com/ads) çalıştığı claude.ai web uygulamasında gerçekleşir.
   > 1. Burada, Claude Code içinde `/reklam-fabrikasi:meta-handoff` çalıştır. Marka DNA'nı, VOC'unu, metnini ve reklam spesifikasyonunu yapıştırmaya hazır bir prompt'a paketler ve `09_Meta_Handoff/` içine kaydeder.
   > 2. Sorulduğunda "yeni kampanya kur" veya "mevcut kampanyaları analiz et" seç.
   > 3. claude.ai web uygulamasını aç, Settings, Customize, Connectors altından Meta MCP connector'ını ekle (URL: https://mcp.facebook.com/ads), sonra devir prompt'unu yeni bir sohbete yapıştır. Devralan Claude işi oradan sürdürür.

6. Bir sonraki beceriyi önerirken, beceri haritasının `parallel_with` alanına göre hangi diğer becerilerin paralel çalışabileceğinden bahset. Paralel önerileri tek satırda biçimlendir, örneğin "Bu çalışırken bağımsız olarak `<beceri-a>` veya `<beceri-b>` becerisini de yapabilirsin."

7. Her zaman şununla bitir: "Bir şey bozuk görünüyorsa `/doctor` çalıştır, ya da bu proje klasöründeki çıktıları görmek için `/open-folder`."

Yanıtı 12 satırın altında tut. Em-dash yok. Dolgu yok. Kullanıcının kopyalayabilmesi için beceri adlarını net yaz.
