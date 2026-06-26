# Yol B uygulaması, Higgsfield CLI

Bu referans, üretim becerilerindeki (rebuild, multiplier, static, product-shot, character, ugc-prompt) her Yol B bölümü tarafından yüklenir. Her becerinin kullanıcıya görünen etiketi `Yol B, Higgsfield MCP` olarak kalır. Altta, Yol B resmi Higgsfield CLI'sı (`@higgsfield/cli@^0.1` npm'de) üzerinden çalışır, MCP sunucusu üzerinden değil. CLI, çoğu kullanıcının Claude Code içinden tetikleyemediği Clerk OAuth yolunu gerektiren MCP'nin drop-in yedeğidir.

CLI, resmi Higgsfield CLI'sıdır; MIT lisanslı ve `*.@higgsfield.ai` tarafından bakımı yapılır. MCP ve web arayüzüyle aynı Higgsfield hesabını, aynı kredileri ve aynı modelleri sunar.

---

## Her becerinin bu dosyayı nasıl kullandığı

Her becerinin Yol B bölümü kendine özgü şunları saklar:

1. Alt küme seçici prompt (beceri kaç promptun mevcut olduğunu ve hangi sayıların geçerli olduğunu bilir)
2. Çıktı dizini ve dosyaadı kalıbı (örn. `path_b_outputs/rebuild_<N>.png`)
3. Referans varlık listesi (hangi yerel dosyaların `--image` olarak geçirileceği)
4. Onay özeti ifadesi (beceriye özgü maliyet çerçevesi)
5. Manifest şeması (becerinin mevcut sözleşmesine göre)

Beceri, genel CLI iş akışı için aşağıdaki adımlara çağrı yapar. `{{çift-parantez}}` içindeki değişken adları, komut çalışmadan önce çağıran beceri tarafından doldurulur.

---

## Adım B.0, CLI'nın kurulu olduğundan emin ol

İkili dosyayı kontrol et:

```
command -v higgsfield 2>/dev/null || command -v ~/.local/bin/higgsfield 2>/dev/null
```

Hiçbiri çözümlenmiyorsa npm ile kur. Önce global kurulumu dene; global reddedilirse kullanıcı-prefix kurulumuna dön:

```
npm install -g @higgsfield/cli@^0.1 2>/dev/null || (mkdir -p ~/.local/lib/node_modules ~/.local/bin && npm config set prefix ~/.local && npm install -g @higgsfield/cli@^0.1)
```

Kurulumdan sonra ikili dosya şu konumlardan birindedir:

- `/usr/local/bin/higgsfield` (macOS veya Linux'ta global kurulum)
- `~/.local/bin/higgsfield` (kullanıcı-prefix yedek)
- `%APPDATA%\npm\higgsfield.cmd` (Windows global kurulum, `where higgsfield` ile çalıştır)

Çalışan yolu bir kez çözümle ve yeniden kullan:

```
HIGGS_BIN="$(command -v higgsfield 2>/dev/null || echo ~/.local/bin/higgsfield)"
```

Kurulumu asla `sudo` ile çalıştırma. npm yükseltme olmadan global kurulumu reddederse kullanıcı-prefix yoluna geç.

Kurulum tamamen başarısız olursa (ağ yok, npm eksik, Node eksik) dur ve kullanıcıya şunu söyle:

> Higgsfield CLI kurulumu başarısız oldu. CLI, Node 20 veya daha yüksek sürüm ve erişilebilir npm gerektirir. Doğrulamak için `node --version` ve `npm --version` komutlarını çalıştırın, ardından bu beceriyi yeniden çalıştırıp Yol B'yi seçin. Node kurulu değilse önce `/reklam-fabrikasi:setup` çalıştırın.

---

## Adım B.1, Kimlik doğrulamasının yapıldığından emin ol

Kimlik doğrulama durumunu sessizce kontrol et:

```
"$HIGGS_BIN" auth token >/dev/null 2>&1
```

Çıkış kodu 0 ise kullanıcı kimliği doğrulanmış. Devam et.

Çıkış kodu sıfır değilse cihaz akışı girişini çalıştır. CLI bir URL artı tek kullanımlık kod yazdırır; kullanıcı tarayıcıda Yetkilendir'e tıklar, CLI tarayıcı akışı tamamlanana kadar bekler. URL'yi terminal bekletmeden gösterebilmek için arka planda çalıştır:

```
"$HIGGS_BIN" auth login > /tmp/higgs-auth-$$.log 2>&1 &
LOGIN_PID=$!
```

Ardından log dosyasında cihaz URL'sini ara ve kullanıcıya CLI'nın yaydığı şekliyle göster:

> Bu URL'yi tarayıcınızda açın ve Yetkilendir'e tıklayın:
>
> `<URL from /tmp/higgs-auth-*.log>`
>
> Kod: `<log'dan kod>`
>
> Tarayıcı başarıyı gösterdiğinde `tamam` yazın.

Arka plandaki `auth login`'in çıkmasını 5 dakika (300 sn) bekle. Çıkış kodu 0 ise kimlik doğrulama başarılı. Zaman aşımına uğrarsa veya başarısız olursa işlemi sonlandır ve hatayı göster:

> Higgsfield girişi tamamlanamadı. Yeniden dene veya ayrı bir terminalde `~/.local/bin/higgsfield auth login` çalıştır ve bu beceriyi yeniden çalıştır.

Başarısızlıkta dur. Sessizce yeniden deneme.

---

## Adım B.2, Çalışma alanı seçimi (birden fazla varsa)

Kullanıcının Higgsfield hesabında birden fazla çalışma alanı varsa, bir çalışma alanı ayarlanana kadar CLI'nın `account status` komutu belirsiz kredi verisi döndürebilir. Kontrol et:

```
"$HIGGS_BIN" workspace list --json
```

Liste birden fazla giriş içeriyorsa kullanıcıya sor:

> Birden fazla Higgsfield çalışma alanınız var: `<virgülle ayrılmış adlar>`. Bu çalışma için hangisini kullanayım? Adıyla yanıtlayın.

Ardından ayarla:

```
"$HIGGS_BIN" workspace set "<çalışma-alanı-adı>"
```

Yalnızca bir çalışma alanı döndürülürse bu adımı sessizce atla.

---

## Adım B.3, Kredi bakiyesini kontrol et

Çalıştır:

```
"$HIGGS_BIN" account status
```

Çıktıyı kullanıcıya olduğu gibi göster. Standart alanlar mevcut kredi toplamı, plan katmanı ve çalışma alanı adını içerir. Maliyet kapısı için kredi toplamını yakala.

---

## Adım B.4, Üretim başı kuru çalışma maliyeti

Toplu işten önce, seçilen model ve en-boy oranı için tek bir maliyet sorgusu çalıştır. Bu, herhangi bir şey harcamadan üretim başı kredi maliyetini döndürür:

```
"$HIGGS_BIN" generate cost "{{MODEL_ID}}" \
  --prompt "cost-check" \
  --aspect_ratio "{{ASPECT}}" \
  --quality "{{QUALITY}}" \
  --resolution "{{RESOLUTION}}"
```

Çağıran beceri tarafından doldurulan değişkenler:

- `{{MODEL_ID}}`: CLI model kimliği (aşağıdaki Model Kimliği Eşlemesi bölümüne bak)
- `{{ASPECT}}`: beceriye bağlı olarak `1:1`, `9:16`, `4:5`, `16:9`, `3:4`
- `{{QUALITY}}`: genellikle GPT Image 2 için `high`, Nano Banana 2 için çıkarılır (CLI sessizce yoksayar)
- `{{RESOLUTION}}`: GPT Image 2 için `4k`, Nano Banana 2 için `2k` (CLI her ikisini de küçük harfle kabul eder)

Döndürülen üretim başı maliyeti yakala. Toplam elde etmek için alt küme adımında kullanıcının seçtiği prompt sayısıyla çarp.

Test referansı: İki `--image` referansıyla `4k`, `9:16`, `quality=high`'da GPT Image 2 üretim başı 12 kredi.

---

## Adım B.5, Onay kapısı

Çağıran beceri, B.3 ve B.4'ten gerçek değerleri doldurarak kendi onay özetini yazdırır. Standart şekil:

> `K` görsel oluşturmak üzereyim, prompt numaraları `<liste>`, Higgsfield CLI üzerinden.
> Üretim başı maliyet: `<B.4'ten kredi>` kredi.
> Toplam: `<K çarpı üretim başı>` kredi.
> Mevcut bakiye: `<B.3'ten kredi>`.
> Devam etmek için `evet` onaylayın.

Açık `evet` (büyük/küçük harf duyarsız) bekle. Diğer tüm yanıtlar çalıştırmayı iptal eder. İptali onayla ve dur.

---

## Adım B.6, Referans varlıklar

CLI, `--image` üzerinden geçirilen yerel dosya yollarını otomatik olarak yükler. Ayrı bir yükle ve onayla adımı yoktur. Becerinin alım aşamasından yerel dosya yollarını topla (kullanıcı onları daha önce sağladı), diskte var olduklarını doğrula ve üretme komutunda her biri için bir `--image` bayrağı geçir.

Bazı modeller için sıra önemlidir. Genel kural olarak, promptun beklediği sırayla referansları geçir:

- Rebuild: önce rakip reklam görseli, sonra kullanıcının ürün görseli
- Multiplier: önce kazanan reklam görseli, ardından 1-3 ürün görseli
- Static: yalnızca ürün görseli (isteğe bağlı)
- Product-shot: önce ürün görseli, uygulanabilirse ikinci olarak karakter `fullbody.png`
- Character (vesikalık): referans yok (metinden görsel)
- Character (tam boy): vesikalık üretiminden yakalanan vesikalık URL'si
- UGC-prompt: `$CHARACTER_REF` ayarlıysa önce karakter, ardından ürün, ardından ses klibi

Referans dosyası eksik veya okunamıyorsa çalışmayı durdur ve başarısız olan yolu bildir. Sessizce atlama.

---

## Adım B.7, Her promptu üret

Her promptu önce geçici bir dosyaya yaz. Kabuk argümanları üzerinden çok satırlı promptlar, özellikle diyalog için çift tırnak içerdiğinde alıntılama sorunuyla boğulur:

```
PROMPT_FILE="/tmp/{{SKILL_SLUG}}-prompt-{{N}}-$$.txt"
cat > "$PROMPT_FILE" <<'PROMPT_EOF'
<tam prompt metni, aynen>
PROMPT_EOF
```

Ardından üretme komutunu çalıştır:

```
"$HIGGS_BIN" generate create "{{MODEL_ID}}" \
  --prompt "$(cat "$PROMPT_FILE")" \
  --aspect_ratio "{{ASPECT}}" \
  --quality "{{QUALITY}}" \
  --resolution "{{RESOLUTION}}" \
  --image "<ref1_yolu>" \
  --image "<ref2_yolu>" \
  --wait \
  --wait-timeout 5m \
  --json \
  > "/tmp/{{SKILL_SLUG}}-result-{{N}}-$$.json" 2>&1
```

Notlar:

- `--wait` iş tamamlanana kadar bekler. Ayrı bir polling adımı yoktur.
- `--wait-timeout 5m` üst sınırdır. 4K'da GPT Image 2 genellikle 30-90 saniyede tamamlanır.
- `--json` üretilen görsel başına bir giriş içeren JSON dizisi döndürür. Çözümleme için zorunludur.
- Referans başına `--image`'ı tekrarla. Referans yoksa çıkar.
- Nano Banana 2 için `--quality` bayrağı CLI tarafından sessizce yoksayılır. Tutarlılık için yine de geçir.
- Seedance 2.0 ve diğer video modelleri için CLI aynı `generate create` arayüzünü kabul eder. Model şeması destekliyorsa `--duration "15"` ve `--generate_audio true` geçir. Emin değilsen kesin bayrak adlarını `higgsfield model get <model_id>` ile doğrula.

### 5 veya daha fazla iş için paralel toplu işler

5 veya daha fazlası için her üretme komutunu arka planda çalıştırarak paralelleştir. Test edildi: paralel çalıştırıldığında 5 adet 4K GPT Image 2 üretimi yaklaşık 90 saniyede tamamlanır; sıralı çalıştırıldığında 5 dakika sürer.

Bash aracının `run_in_background` parametresini kullan; her PID'i yakala ve parse adımından önce hepsini bekle. Aynı anda 8'den fazla paralel üretim çalıştırma; Higgsfield, API'yi çalışma alanı katmanında hız sınırlar.

1-4 toplu iş için sıralı yeterlidir. Her üretim sıradan bağımsız olarak aynı maliyete sahiptir.

---

## Adım B.8, Sonucu çözümle ve indir

`--json` çıktısı bir JSON dizisidir. Mevcutsa `jq` ile çözümle, yoksa Python'a dön:

```
RESULT_FILE="/tmp/{{SKILL_SLUG}}-result-{{N}}-$$.json"

if command -v jq >/dev/null 2>&1; then
  JOB_ID="$(jq -r '.[0].id // empty' "$RESULT_FILE")"
  JOB_STATUS="$(jq -r '.[0].status // empty' "$RESULT_FILE")"
  RESULT_URL="$(jq -r '.[0].result_url // empty' "$RESULT_FILE")"
else
  JOB_ID="$(python3 -c "import json,sys; d=json.load(open('$RESULT_FILE')); print(d[0].get('id',''))")"
  JOB_STATUS="$(python3 -c "import json,sys; d=json.load(open('$RESULT_FILE')); print(d[0].get('status',''))")"
  RESULT_URL="$(python3 -c "import json,sys; d=json.load(open('$RESULT_FILE')); print(d[0].get('result_url',''))")"
fi
```

`jq` artı Python yedeği neden: `jq` her kullanıcının makinesinde bulunmaz (özellikle yeni Windows veya WSL kurulumlarında). Python 3, eklentinin zorunlu bir ön koşuludur (`/reklam-fabrikasi:setup`'a bak), bu nedenle yedek her zaman kullanılabilir. Kabukta JSON'a regex uygulamak, CLI'nın yaydığı anahtarlarla alıntılanmış biçimde bozulur; URL'yi grep veya sed ile çıkarmaya çalışma.

`JOB_STATUS` `completed` dışında bir şeyse hatayı olduğu gibi göster ve toplu işteki kalan işlere devam et. CLI, insan tarafından okunabilir bir gerekçeyle birlikte `failed`, `cancelled` veya `timeout` yayar.

Sonuç görselini curl ile indir:

```
curl -sSL "$RESULT_URL" -o "{{OUTPUT_DIR}}/{{OUTPUT_FILENAME}}"
```

Dosya boyutunun 50000 baytın üzerinde olup olmadığını kontrol ederek indirmenin gerçekleştiğini doğrula (gerçek üretilmiş görseller en az birkaç yüz KB büyüklüğündedir). Dosya daha küçükse URL muhtemelen görsel yerine hata sayfası döndürdü. Bir kez yeniden dene, ardından o spesifik prompt için başarısızlığı bildir ve geri kalanla devam et.

---

## Adım B.9, Manifest

Toplu iş tamamlandıktan sonra (istenen her prompt tamamlandı veya başarısız oldu), `{{OUTPUT_DIR}}/manifest.json` dosyasına bir manifest yaz. Zorunlu alanlar:

```json
{
  "generated_via": "higgsfield-cli",
  "cli_version": "<higgsfield --version'dan>",
  "model_id": "{{MODEL_ID}}",
  "model_label": "<gpt-image-2 veya nano-banana-2 veya seedance-2.0>",
  "workspace": "<uygulanabilirse B.2'den>",
  "total_credits_spent": <tam sayı, B.3 ile toplu işten sonraki güncel `account status` çağrısı arasındaki bakiye farkı>,
  "items": [
    {
      "prompt_number": <tam sayı>,
      "prompt_text": "<aynen prompt metni>",
      "job_id": "<B.8'den>",
      "status": "completed | failed | timeout",
      "output_path": "<mutlak yol veya başarısızlıkta boş>",
      "credits": <üretim başı tam sayı maliyet>,
      "failure_reason": "<başarısızlıkta aynen hata, tamamlandıysa boş>"
    }
  ]
}
```

Üst düzey `generated_via: "higgsfield-cli"` değeri, Yol B (CLI) çıktısını aşağı akış araçları için Yol D (Playwright) çıktısından ayırt eder. Eski `generated_via: "higgsfield-mcp"` değeri artık yayılmıyor; her iki değeri okuyan araçlar ikisini de Yol B çıktısı olarak işlemelidir.

---

## Model Kimliği Eşlemesi

Higgsfield CLI, MCP'nin kullandığından farklı model kimlikleri kullanır. Eşleme:

| Beceri etiketi    | MCP kimliği (eski)    | CLI kimliği         | Notlar |
|-------------------|-----------------------|---------------------|-------|
| GPT Image 2       | `gpt-image-2`         | `gpt_image_2`       | Tüm görsel beceriler için varsayılan. |
| Nano Banana 2     | `nano-banana-2`       | `nano_banana_flash` | Daha ucuz alternatif. |
| Seedance 2.0      | `seedance-2`          | `seedance_2_pro`    | Video, ugc-prompt tarafından kullanılır. CLI bilinmeyen-model döndürürse `higgsfield model list` ile kesin kimliği doğrula. |
| Seedance 2.0 Fast | `seedance-2-fast`     | `seedance_2_lite`   | Daha ucuz video varyantı. Aynı doğrulama kuralı. |

Çağıran beceri `$MODEL`'i `gpt-image-2` olarak yakaladıysa `{{MODEL_ID}}` için `gpt_image_2` kullan. `nano-banana-2` ise `nano_banana_flash` kullan. Video için ugc-prompt becerisi `seedance_2_pro` (veya Hızlı varyant için `seedance_2_lite`) kullanır.

Çalışma zamanında kullanılabilir model kimliklerinin canlı listesini almak için çalıştır:

```
"$HIGGS_BIN" model list --json | jq -r '.[].id'
```

Seçilen kimlik listede değilse bulanık eşleşmeye geri dön (`grep -i gpt_image`, `grep -i nano_banana`, `grep -i seedance`) ve en yakın eşleşmeyi kullan. Seçilen kimliği kullanıcıya göster; böylece katalog değiştiyse geçersiz kılabilirler.

---

## Çıktı boyutundan en-boy oranına eşleme

CLI, fal.ai MCP'nin kabul ettiği `image_size` genişlik ve yükseklik yerine, seçilen en-boy oranı için modelin yerel çözünürlüğünde görseller döndürür. 4K'da GPT Image 2 için gözlemlenen boyutlar:

- `1:1` için 2880x2880
- `9:16` için 2160x3840
- `4:5` için 2560x3200
- `16:9` için 3840x2160
- `3:4` için 2400x3200

Bunlar, fal.ai Yol C bağlantısının istediği boyutların aynısıdır; bu nedenle aşağı akış araçları (Meta yükleyiciler, açılış sayfası varlık yuvaları) Yol B ve Yol C çıktılarını birbirinin yerine kullanır.

2K'da Nano Banana 2 için döndürülen boyutlar, aynı en-boy oranında GPT Image 2 4K boyutlarının yaklaşık yarısıdır.

---

## Platformlar arası notlar

- **macOS / Linux**: varsayılan kurulum yolu `/usr/local/bin/higgsfield`. Kullanıcı-prefix yedek `~/.local/bin/higgsfield`'e gelir. Her ikisi de `command -v higgsfield` ile tespit edilebilir.
- **Windows**: `npm install -g @higgsfield/cli@^0.1` komutu `%APPDATA%\npm\higgsfield.cmd`'ye kurar. `command -v` kontrolü Git Bash ve WSL altında çalışır. PowerShell altında `Get-Command higgsfield` kullan. Kullanıcı-prefix yedek `~/.local` yerine `%APPDATA%\npm-userconfig` kullanır; `npm config set prefix "$env:APPDATA\npm-userconfig"` ile ayarlanır.
- **Windows'ta WSL**: WSL Linux tarafında (Ubuntu / Debian) kur. WSL içinden Windows tarafı kurulumu çağırma; dosya yolları çevrilmez.

Windows'ta kurulum yolu tespiti başarısız olursa, `where higgsfield` (cmd) veya `Get-Command higgsfield | Select-Object -ExpandProperty Source` (PowerShell) komutunu çalıştır ve o yolu açıkça kullan.

---

## Bu referansı yükleyen her beceri için katı kurallar

1. **Otomatik üretim yapma.** Her toplu iş, B.5 onay özetinden sonra kullanıcıdan açık `evet` gerektirir.
2. **Her zaman B.3'te kredi bakiyesini ve B.4'te üretim başı maliyeti göster.** Onay kapısından önce kullanıcı gerçek sayıları görmelidir, tahmin değil.
3. **Açık `evet` olmadan Higgsfield kredisi harcama.** Tek bir test çalışması bile olsa.
4. **Her çıktıyı diske kaydet** çağıran becerinin `{{OUTPUT_DIR}}` dizinine (örn. `path_b_outputs/`). Manifest zorunludur.
5. **Yolları sessizce değiştirme.** CLI hata döndürürse yeniden denemek, Yol A'ya (manuel) geçmek veya vazgeçmek isteyip istemediklerini sor. Yol C'ye otomatik geri dönme.
6. **Kullanıcıya görünen etiket `Yol B, Higgsfield MCP` olarak kalır.** Bu dosya yalnızca altta yatan uygulamayı değiştirir; kullanıcının gördüğü seçici promptu ve mesajlar, mevcut onboarding ekran görüntüleri ve belgelerinin doğru kalması için tam olarak o etiketi kullanmalıdır.

---

## Smoke test

Tek seferlik bir smoke test scripti `scripts/smoke-test-path-b.sh` konumundadır. Kurulumdan sonra veya CLI sürümü her değiştiğinde, ikili dosyanın erişilebilir olduğunu, kimlik doğrulamasının güncel olduğunu ve beklenen model kimliklerinin katalogda bulunduğunu doğrulamak için çalıştır. Script başarıda 0 ile çıkar ve aksi hâlde hangi kontrolün başarısız olduğunu yazdırır.
