---
description: Marketplace, eklenti, dört MCP sunucusunu (apify, playwright, fal-ai, higgsfield), Fal anahtarını, Higgsfield OAuth durumunu, makine durumunu ve CLI PATH'i doğrulayan tanılama kontrol listesi. Ayrıca mevcut çalışma klasörünün "Reklam Fabrikası" alt klasörüne sahip olup olmadığına dair bilgilendirici bir not içerir.
---

# /doctor

Yedi noktalı tanılama çalıştır. Her OK olmayan satır için `[OK]`, `[WARN]`, `[FAIL]` veya `[INFO]` etiketi ve yapıştırılabilir düzeltme komutu içeren bir kontrol listesi yazdır.

Her kontrolü kendin gerçekleştirmek için Bash aracını kullan. Kullanıcıya terminalde komut çalıştırmasını asla söyleme.

## 0. Yeni kurulum tespiti (tüm kontrollerden önce çalıştır)

İsteğe bağlı MCP'ler (Apify, Fal AI, Higgsfield) kasıtlı olarak tembeldir. Bunlar yalnızca gerçekten ihtiyaç duyduklarında kullanıcı tarafından yapılandırılır. Yeni bir kurulumda, bunların her biri yapılandırılmamış görünecektir; bu doğru davranıştır, bir hata değil. Yeni kurulum sinyali olmadan `/doctor`, art arda birden fazla `[WARN]` satırı gösterecek ve kurulumun başarısız olmuş gibi görünmesine neden olacak.

Yeni kurulum durumunu iki sinyali birleştirerek tespit et:

```
SETTINGS="$HOME/.claude/settings.json"
FRESH_SETTINGS=1
if [ -f "$SETTINGS" ]; then
  # pluginConfigs["reklam-fabrikasi"] altında boş olmayan değer ara.
  HAS_CFG="$(python3 -c "import json,sys
try:
    cfg = json.load(open('$SETTINGS')).get('pluginConfigs',{}).get('reklam-fabrikasi',{}) or {}
    print('YES' if any(isinstance(v,str) and v.strip() for v in cfg.values()) else 'NO')
except Exception:
    print('NO')" 2>/dev/null)"
  [ "$HAS_CFG" = "YES" ] && FRESH_SETTINGS=0
fi

FRESH_PROJECT=1
if [ -d "$(pwd)/Reklam Fabrikası" ]; then
  # "Reklam Fabrikası" altında en az bir dosyaya sahip herhangi bir alt klasör gerçek işin yapıldığı anlamına gelir.
  if find "$(pwd)/Reklam Fabrikası" -mindepth 2 -type f 2>/dev/null | head -n 1 | grep -q .; then
    FRESH_PROJECT=0
  fi
fi

if [ "$FRESH_SETTINGS" = "1" ] && [ "$FRESH_PROJECT" = "1" ]; then
  FRESH_INSTALL=1
else
  FRESH_INSTALL=0
fi
```

`FRESH_INSTALL=1` ise raporun en üstüne, 1. satırdan önce şu başlık satırını yazdır:

> Yeni kurulum tespit edildi. İsteğe bağlı MCP'ler henüz yapılandırılmamış. Bu normaldir.

`FRESH_INSTALL` değerini aşağıdaki 4., 5. ve 6. satırlara taşı; böylece bu satırlar isteğe bağlı kurulum mesajları için `[WARN]` yerine `[INFO]` seçsin. Yeni kurulum olmayan durumda (`FRESH_INSTALL=0`), mevcut `[WARN]` davranışı değişmez; böylece gerçek sorunlar yine de ortaya çıkar.

## 1. CLI PATH'te

En son kurulu eklenti dizinini bul, ardından çözücüyü çalıştır:

```
PLUGIN_DIR="$(ls -td ~/.claude/plugins/cache/reklam-fabrikasi/reklam-fabrikasi/*/ 2>/dev/null | head -n 1)"
RESOLVER="$PLUGIN_DIR/scripts/resolve-claude-cli.sh"
RESOLVED="$(bash "$RESOLVER" 2>/dev/null)"
ON_PATH="$(command -v claude 2>/dev/null)"
```

Üç sonuç:

- Çözücü başarısız (diskte hiçbir yerde claude ikili dosyası yok):
  `[FAIL] claude CLI bulunamadı. Fix: claude CLI'yı https://claude.ai/download adresinden yeniden yükle, ardından /reklam-fabrikasi:repair-path çalıştır`
- Çözücü başarılı ama `command -v claude` hiçbir şey veya `Library/Application Support/Claude` içinde bir yol döndürüyor:
  `[WARN] claude ikili dosyası bulundu ama PATH'te değil. Fix: /reklam-fabrikasi:repair-path`
- Çözücü başarılı ve `command -v claude` sabit bir yol döndürüyor:
  `[OK] claude şu yolda: <yol>`

Bu satır `[FAIL]` ise burada dur. CLI olmadan diğer kontrollerin hiçbiri güvenilir şekilde çalışamaz.

## 2. Marketplace kayıtlı

`~/.claude/plugins/known_marketplaces.json` dosyasını oku ve adı `reklam-fabrikasi` olan bir giriş ara.

- Başarılı: `[OK] marketplace kayıtlı`
- Başarısız: `[FAIL] marketplace kayıtlı değil. Fix: eklentiyi açtığınız klasörden ekleyin: claude plugin marketplace add <reklam-fabrikasi-klasör-yolu>`

## 3. Eklenti kurulu

`~/.claude/plugins/installed_plugins.json` dosyasını (veya `~/.claude/plugins/cache/reklam-fabrikasi/` dizinini) oku. Kullanıcı kapsamında kurulmuş `reklam-fabrikasi` ara.

- Başarılı: `[OK] Reklam Fabrikası eklentisi kurulu`
- Başarısız: `[FAIL] eklenti kurulu değil. Fix: claude plugin install reklam-fabrikasi@reklam-fabrikasi --scope user`

## 4. MCP sunucuları erişilebilir

`claude mcp list` çalıştır ve `apify`, `playwright`, `fal-ai` ve `higgsfield`'ın tamamının göründüğünü doğrula.

- Erişilebilir olduğunda her sunucu için: `[OK] mcp:apify` / `[OK] mcp:playwright` / `[OK] mcp:fal-ai` / `[OK] mcp:higgsfield`
- Erişilemeyen sunucu için sınıflandırma, 0. satırdaki `FRESH_INSTALL` değerine bağlıdır.
  - `mcp:playwright` listelenmemesi, yeni kurulum durumundan bağımsız olarak her zaman gerçek bir arıza olarak değerlendirilir; playwright paketlenmiş olduğundan her zaman yüklenmeli:
    - `[FAIL] mcp:playwright listelenmemiş. Fix: claude plugin install reklam-fabrikasi@reklam-fabrikasi --scope user komutunu yeniden çalıştır`
  - `mcp:apify`, `mcp:fal-ai`, `mcp:higgsfield`'ın tamamı tam bağlantı için kullanıcı tarafından sağlanan kimlik bilgileri veya OAuth gerektirir. Yeni kurulumda (`FRESH_INSTALL=1`) `[INFO]` kullan. Yeni kurulum olmayan durumda `[WARN]` kullan.
    - apify: `[INFO] mcp:apify, isteğe bağlı kurulum. İhtiyaç duyduğunuzda yapılandırın. Casus veya ugc-scraper becerilerini kullanmak istiyorsanız /reklam-fabrikasi:setup-apify çalıştırın.` veya `[WARN] mcp:apify kimlik doğrulaması gerekiyor. Fix: apify aracını bir sonraki çağırışınızda OAuth el sıkışmasını tamamlayın veya /apify-token aracılığıyla token ayarlayın`
    - fal-ai: `[INFO] mcp:fal-ai, isteğe bağlı kurulum. İhtiyaç duyduğunuzda yapılandırın. Yol C üretimi kullanmak istiyorsanız /reklam-fabrikasi:setup-fal-ai çalıştırın.` veya `[WARN] mcp:fal-ai anahtara ihtiyaç duyuyor. Fix: ~/.claude/settings.json dosyasında fal_api_key ayarlayın`
    - higgsfield: `[INFO] mcp:higgsfield, isteğe bağlı kurulum. İhtiyaç duyduğunuzda yapılandırın. Yol B üretimi kullanmak istiyorsanız Claude Code içinde /mcp çalıştırın ve Higgsfield OAuth girişini tamamlayın.` veya `[WARN] mcp:higgsfield bağlı değil. Fix: Claude Code içinde /mcp çalıştırın ve Higgsfield OAuth girişini tamamlayın. Yalnızca statik, ugc-prompt, çoğaltıcı veya yeniden oluşturma için Yol B kullanmayı planlıyorsanız gereklidir.`

## 5. Fal AI anahtarı mevcut

`~/.claude/settings.json` dosyasını oku ve `pluginConfigs["reklam-fabrikasi"].fal_api_key` alanına bak. Boş olmayan bir dize olmalı.

- Başarılı: `[OK] fal_api_key settings.json dosyasında mevcut`
- Yeni kurulumda eksik (`FRESH_INSTALL=1`): `[INFO] fal_api_key, isteğe bağlı kurulum. İhtiyaç duyduğunuzda yapılandırın. Yol C üretimi kullanmak istiyorsanız /reklam-fabrikasi:setup-fal-ai çalıştırın.`
- Yeni kurulum olmayan durumda eksik (`FRESH_INSTALL=0`): `[WARN] fal_api_key eksik. Fix: ~/.claude/settings.json dosyasını aç ve pluginConfigs["reklam-fabrikasi"].fal_api_key alanını https://fal.ai/dashboard/keys adresindeki Fal AI anahtarınıza ayarla`

(Fal yalnızca Yol C üretimi için gerekli olduğundan hiçbir zaman `[FAIL]` olmaz. Yalnızca Kendin Yap veya Playwright yollarını kullanan kullanıcıların buna ihtiyacı yok.)

## 6. Higgsfield MCP + CLI bağlantısı

Yol B eskiden Higgsfield MCP'yi çağırırdı. v1.6.0 itibarıyla Yol B, MCP yerine resmi Higgsfield CLI'ını (`@higgsfield/cli` npm'de) kullanıyor; dolayısıyla MCP tamamen isteğe bağlı. Bu bölüm iki bilgilendirici kontrol çalıştırır; biri MCP üzerinde, biri CLI üzerinde. Hiçbiri tanılamayı başarısız kılamaz.

### Higgsfield MCP (v1.6.0+ sonrası yalnızca bilgilendirici)

`mcp__higgsfield__*` araçlarının mevcut olup olmadığını kontrol ederek araştır. v1.6.0 sonrasında hiçbir yol için MCP gerekmediğinden `[WARN]` veya `[FAIL]` olmadan sonucu bilgilendirici olarak raporla:

- Yüklenmiş `mcp__higgsfield__*` aracı yoksa: `[INFO] Higgsfield MCP: bağlı değil (v1.6.0+ sonrasında isteğe bağlı, Yol B @higgsfield/cli kullanıyor)`
- Araçlar yüklüyse ve `mcp__higgsfield__balance` bir kredi toplamı döndürüyorsa: `[INFO] Higgsfield MCP: bağlı, bakiye <kredi> kredi (v1.6.0+ sonrasında isteğe bağlı, Yol B @higgsfield/cli kullanıyor)`
- Araçlar yüklüyse ama `mcp__higgsfield__balance` hata veriyorsa: `[INFO] Higgsfield MCP: bağlı ama hata döndürdü (v1.6.0+ sonrasında isteğe bağlı, Yol B @higgsfield/cli kullanıyor)`

### Higgsfield CLI (Yol B tarafından kullanılır)

İkili dosyayı bulmak için bu çözücüyü çalıştır:

```
command -v higgsfield 2>/dev/null || ls ~/.local/bin/higgsfield 2>/dev/null
```

Bir yol döndürülürse CLI kurulu demektir. Aşağıdaki kimlik doğrulama alt kontrolü için `$HIGGS_BIN` olarak yakala.

- Kuruluysa: `[OK] Higgsfield CLI: kurulu <yolda>`
- Kurulu değilse: `[INFO] Higgsfield CLI: kurulu değil, ilk Yol B çalıştırmasında otomatik kurulur veya proaktif olarak \`npm install -g @higgsfield/cli@^0.1\` çalıştırılabilir`

İkili dosya yalnızca bulunduğunda kimlik doğrulama durumunu araştır:

```
"$HIGGS_BIN" auth token >/dev/null 2>&1
```

- Çıkış 0 ise: `[OK] Higgsfield CLI kimlik doğrulaması: kimlik doğrulandı`
- Sıfır olmayan ise: `[INFO] Higgsfield CLI kimlik doğrulaması: giriş yapılmamış, ilk Yol B çalıştırmasında \`higgsfield auth login\` bunu halleder`

Bu bölümün tamamı hiçbir zaman `[FAIL]` veya `[WARN]` olmaz. Higgsfield (MCP veya CLI) yalnızca Yol B için gereklidir. Yol A, C veya D kullanan kullanıcıların ikisine de ihtiyacı yok. CLI kurulumu ve kimlik doğrulama ilk Yol B çağrısında tembelce çalışır; dolayısıyla her iki satırı da kurulu olmayan ve kimlik doğrulanmamış olarak gösteren yeni kurulum makinesi beklenen başlangıç durumudur.

## 7. Makine durumu yazılabilir + çalışma klasörü notu

İki bölüm. Önce, makine durumu ağacının mevcut ve yazılabilir olduğunu doğrula. `~/Reklam-Fabrikasi/_meta/.state/` içinde geçici bir dosya oluşturmayı dene. Bu, makine başına durumdur; proje çalışması değil.

- Başarılı: `[OK] ~/Reklam-Fabrikasi/_meta/.state yazılabilir`
- Başarısız: `[FAIL] makine durumu klasörü eksik veya yazılabilir değil. Fix: bash ~/.claude/plugins/cache/reklam-fabrikasi/reklam-fabrikasi/*/scripts/ensure-folders.sh`

İkinci olarak, mevcut çalışma klasörü hakkında bilgilendirici bir satır. Proje çalışması artık klasör başına olduğundan, yeni bir proje klasöründe "Reklam Fabrikası/" eksikliği normal bir durumdur, hata değil:

```
PROJ="$(pwd)/Reklam Fabrikası"
if [ -d "$PROJ" ]; then
  echo "[INFO] Çalışma klasörü kontrolü: $(pwd) zaten Reklam Fabrikası/ içeriyor (proje başlatılmış)."
else
  echo "[INFO] Çalışma klasörü kontrolü: $(pwd) henüz Reklam Fabrikası/ içermiyor. Burada çalıştırdığınız ilk beceri onu oluşturacak."
fi
```

Bu satırı her zaman yazdır. `[INFO]` etiketli, hata değil.

## Çıktı

Yedi satırı sonunda tablo ile kontrol listesi olarak yazdır. Tablo her satırı etiketine göre sayar. Format:

```
Tablo: <X> OK, <Y> INFO, <Z> WARN, <W> FAIL.
```

`[INFO]` satırları uyarı olarak sayılmaz. `INFO` grubuna dahil edilir. Bu önemlidir çünkü yeni kurulumda isteğe bağlı MCP'ler `INFO`'ya düşer, `WARN`'a değil; böylece yeni kurulum temiz tablo yerine birden fazla şeyin bozulmuş gibi görünmesini raporlamaz.

Her şey `[OK]` ise veya yalnızca isteğe bağlı kurulum satırları `[INFO]` veya `[WARN]` ise (satır 4, 5, 6), şununla bitir:

> Tüm sistemler hazır. Şimdi ne yapacağınızı görmek için `/next` yazın.

Herhangi bir satır `[FAIL]` ise şununla bitir:

> Yukarıdaki [FAIL] satırlarını düzeltin, ardından `/doctor` komutunu yeniden çalıştırın.

Em-dash yok. Kısa tut.
