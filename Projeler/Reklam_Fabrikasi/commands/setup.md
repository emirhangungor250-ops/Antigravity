---
description: Reklam Fabrikası için tek komutlu ana kurulum. İşletim sistemini algılar, eksik geliştirici araçlarını yükler (macOS için Homebrew, Windows için winget; winget yoksa Scoop, artı git, Node 20+, Python 3.12+, ffmpeg), git'i yapılandırır, Playwright Chromium'u ön ısıtır, MCP sunucularının bağlı olduğunu onaylar ve gerekirse claude PATH'ini otomatik düzeltir. Idempotent (tekrar çalıştırması güvenli). Eklenti kurulumundan sonra bir kez çalıştırın. Kullanıcılar bu işlem bittikten sonra /welcome yazar.
---

# /setup

Reklam Fabrikası eklentisinin içinde çalışıyorsunuz. Kullanıcı `/setup` yazdı. Kullanıcının Claude Code'dan çıkmadan veya terminal açmadan tam tek seferlik makine kurulumunu tamamlamasını sağlayın.

## Windows kullanıcıları, önce şunu okuyun

Windows kullanıcıları: `/setup` Scoop kurulumu için duraklarsa bu normaldir. Windows Server ve bazı kurumsal Windows yapılandırmalarında olur. Evet deyin. Scoop, yönetici hakları gerektirmeyen kullanıcı başına bir paket yöneticisidir; bu nedenle makinede `winget` yoksa doğru geri dönüş seçeneğidir.

## Bu komutun katı kuralları

1. **Her kabuk komutunu kendiniz Bash üzerinden çalıştırırsınız.** Kullanıcıya terminal açmasını söylemeyin. Bir komutu yazdırıp çalıştırmasını istemeyin. Yalnızca şu durumlarda istisna vardır:
   - Sizin sorduğunuzda token veya değer yapıştırmak
   - Geri dönüşü zor bir işlemi onaylamak
2. **Idempotent.** Her adım başarılı olduktan sonra `~/Reklam-Fabrikasi/_meta/.state/setup/step-N.done` konumuna bir işaret yazar. Yeniden çalıştırıldığında tamamlanmış adımlar tek satırla atlanır: `step N already complete, skipping`.
3. **Bağımsız işler paralel çalışır** (arka plan süreçleriyle). Birbirine bağlı olmayan iki adım varsa (örneğin işletim sistemi algılama ve araç kontrolleri) ikisini aynı anda başlatın.
4. **Em-dash kullanmayın.** Virgül, "ve" kullanın ya da cümleyi yeniden kurun.
5. **Her hata mesajı tek somut bir çözümle biter.** Uzun metin blokları yazmayın. Kullanıcı `/setup` tekrar çalıştırır veya siz halledersiniz.

## Adım durumu dizini

Önce işaret dizininin var olduğundan emin olun:

```
mkdir -p "$HOME/Reklam-Fabrikasi/_meta/.state/setup"
```

Her adım için, işi çalıştırmadan önce `[ -f "$HOME/Reklam-Fabrikasi/_meta/.state/setup/step-N.done" ]` kontrolü yapın. İşaret varsa `step N already complete, skipping` yazdırıp devam edin.

Her adım başarılı olduktan sonra işareti yazın:

```
date -u +%Y-%m-%dT%H:%M:%SZ > "$HOME/Reklam-Fabrikasi/_meta/.state/setup/step-N.done"
```

## Adım 1: İşletim sistemi ve mimariyi algıla

Adım 2 ile paralel çalıştırın.

```
uname -s; uname -m
```

- `Darwin arm64`: macOS Apple Silicon
- `Darwin x86_64`: macOS Intel
- `MINGW*`, `MSYS*`, `CYGWIN*` veya `uname` yoksa: Windows
- Diğer: tek satır yazdırıp durdurun. Eklenti yalnızca macOS ve Windows'u destekler.

İşletim sistemi ve mimariyi sonraki adımların okuyabileceği şekilde `~/Reklam-Fabrikasi/_meta/.state/setup/os.txt` dosyasına yazın. Adım 1'i tamamlandı olarak işaretleyin.

## Adım 2: Gerekli araçları kontrol et (paralel)

Beş kontrolü tek bir Bash çağrısında çalıştırın, hepsi paralel olsun:

```
{ command -v git >/dev/null 2>&1 && git --version; } &
{ command -v node >/dev/null 2>&1 && node --version; } &
{
  # Python kontrolü: PATH'teki ilk python>=3.12'yi kabul et. Kullanıcıların PATH'inde
  # eski sistem python3'ü (3.9) varken brew'da daha yeni bir python3.12 veya python3.13
  # olabilir. Her ikisi de kabul edilir.
  for cand in python3.14 python3.13 python3.12 python3; do
    if command -v "$cand" >/dev/null 2>&1; then
      v="$($cand --version 2>&1)"
      major=$(echo "$v" | grep -oE '3\.[0-9]+' | head -n 1)
      minor=${major##3.}
      if [ -n "$minor" ] && [ "$minor" -ge 12 ]; then
        echo "python: $cand $v"
        break
      fi
    fi
  done
} &
{ command -v ffmpeg >/dev/null 2>&1 && ffmpeg -version | head -n 1; } &
{ command -v claude >/dev/null 2>&1 && claude --version; } &
wait
```

Her çıktıyı ayrıştırın. Node ana sürümünün >= 20 olduğunu ve PATH'teki en az bir `python3.x` dosyasının >= 3.12 rapor ettiğini doğrulayın. Varsayılan `python3` hâlâ 3.9 (macOS sistem Python'u) olabilir; `python3.12` veya daha yükseği de mevcutsa sorun yok. Kontrol listesini yazdırın:

```
[OK]   git 2.45.1
[OK]   node v22.11.0
[FAIL] python missing
[OK]   ffmpeg 7.1
[OK]   claude 2.1.119
```

Eksik araçlar listesini oluşturun. Adım 2'yi tamamlandı olarak işaretleyin.

## Adım 3: Eksik olanları yükle

Eksik liste boşsa adım 3'ü tamamlandı işaretleyip devam edin. Değilse:

### macOS

Homebrew eksikse (`command -v brew` boşsa) önce onu yükleyin:

```
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

Kurulumdan sonra Apple Silicon'da, `~/.zprofile` dosyasına eval satırı henüz eklenmemişse ekleyin:

```
if [ "$(uname -m)" = "arm64" ] && ! grep -Fq '/opt/homebrew/bin/brew shellenv' "$HOME/.zprofile" 2>/dev/null; then
  echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> "$HOME/.zprofile"
fi
eval "$(/opt/homebrew/bin/brew shellenv)" 2>/dev/null || true
```

Ardından eksik her şeyi tek bir toplu yüklemeyle kurun:

```
brew install git node@20 python@3.12 ffmpeg
```

Yeniden çalıştırmalarda iş tekrarını önlemek için brew install argümanlarını yalnızca gerçekten eksik araçlara göre filtreleyin. Eşleme: `git -> git`, `node -> node@20`, `python -> python@3.12`, `ffmpeg -> ffmpeg`.

Brew install sudo isterse (temiz bir Mac'te nadirdir ama bazı Cellar konumlarında olur) kullanıcıya şunu söyleyin: `brew macOS'ten izin istiyor. Az önce açılan onay penceresini onaylayın.` Tamamlanmasını bekleyin.

### Windows

Önce bu makinede `winget` olup olmadığını kontrol edin. Bazı Windows sürümleri (Windows Server 2019, Windows Server 2022, Windows Server 2025, kısıtlanmış kurumsal Windows 10 ve Windows 11 imajları ve eski bazı tüketici Windows 10 SKU'ları) winget olmadan gelir. Bu makinelerde çıkmaz noktasına girmemek için iki yükleme yolu sunuyoruz.

```
where.exe winget >/dev/null 2>&1 && echo HAVE_WINGET || echo NO_WINGET
```

Sonuç `HAVE_WINGET` ise winget yolunu izleyin. `NO_WINGET` ise Scoop yolunu izleyin.

#### Yol 1, winget mevcut

Tek toplu yükleme:

```
winget install --silent --accept-package-agreements --accept-source-agreements Git.Git OpenJS.NodeJS.LTS Python.Python.3.12 Gyan.FFmpeg
```

Paket listesini yalnızca gerçekten eksik araçlara göre filtreleyin. Eşleme: `git -> Git.Git`, `node -> OpenJS.NodeJS.LTS`, `python -> Python.Python.3.12`, `ffmpeg -> Gyan.FFmpeg`.

winget UAC isterse kullanıcıya şunu söyleyin: `Windows izin istiyor. UAC penceresini onaylayın.` Tamamlanmasını bekleyin.

#### Yol 2, winget yok, Scoop'a geri dön

Kullanıcıya tam olarak şu açıklamayı yazdırın:

> Bu Windows makinesinde winget yüklü değil. Windows Server ve bazı kurumsal Windows yapılandırmalarında bu normaldir. Bunun yerine Scoop kullanabiliriz; Scoop, yönetici hakları gerektirmeden kullanıcı başına yükleme yapar. Scoop, ev klasörünüze yüklenir, sistem klasörlerine dokunmaz ve hiçbir zaman UAC gerektirmez.
>
> Scoop ile devam edilsin mi? (yes / no)

Kullanıcının cevabını bekleyin. `no` veya `yes` dışında bir şey yazarsa adım 3'ü tamamlandı işaretlemeden temiz çıkış yapın ve şu mesajı gösterin:

> Sorun değil. Bunun yerine winget kullanmak için Microsoft Store'dan App Installer'ı yükleyin ya da https://aka.ms/getwinget adresinden MSIX paketini indirin, ardından `/setup` komutunu tekrar çalıştırın. Scoop kullanmak için `/setup` tekrar çalıştırın ve Scoop sorusuna `yes` yanıtı verin.

`yes` yanıtı verirse dört PowerShell çağrısını Bash üzerinden çalıştırın. Her çağrı `powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "<satır>"` formatını kullanır; böylece katı yürütme politikası olan makinelerde bile Scoop kurulumu engellenmez:

```
powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned -Force"
powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "Invoke-RestMethod -Uri https://get.scoop.sh | Invoke-Expression"
powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "scoop bucket add extras"
powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "scoop install nodejs-lts python ffmpeg"
```

Son `scoop install` argüman listesini gerçekten eksik araçlara göre filtreleyin. Eşleme: `git -> git`, `node -> nodejs-lts`, `python -> python`, `ffmpeg -> ffmpeg`. İlk iki PowerShell satırı (politika ayarı ve Scoop bootstrap) yeniden çalıştırmada `command -v scoop` zaten bir yol döndürüyorsa atlanır. Şu şekilde kontrol edin:

```
command -v scoop >/dev/null 2>&1 && echo HAVE_SCOOP || echo NO_SCOOP
```

Sonuç `HAVE_SCOOP` ise doğrudan `scoop bucket add extras` ve `scoop install ...` çağrılarına geçin.

Scoop hiçbir zaman UAC istemez; kullanıcıyı herhangi bir açılır pencere onaylaması için uyarmayın.

### Doğrulama

Adım 2 kontrol döngüsünü yeniden çalıştırın. Daha önce eksik olan tüm araçların artık mevcut olması gerekir.

Scoop'a özgü bir ince nokta vardır. `nodejs-lts` Scoop paketi global shim oluşturmaz; `~/scoop/apps/nodejs-lts/current` dizinini doğrudan PATH'e ekler. Scoop kurulumundan önce başlayan bir Bash oturumunda bu dizin PATH'te olmayabilir; dolayısıyla node kurulu olsa bile `command -v node` boş döner. Bunu işlemek için Scoop yükleme yolundan hemen sonra ek bir kontrol çalıştırın:

```
NODE_PROBE="$(command -v node 2>/dev/null || true)"
if [ -z "$NODE_PROBE" ] && [ -x "$HOME/scoop/apps/nodejs-lts/current/node.exe" ]; then
  NODE_PROBE="$HOME/scoop/apps/nodejs-lts/current/node.exe"
  export PATH="$HOME/scoop/apps/nodejs-lts/current:$PATH"
fi
```

`NODE_PROBE` boş değilse node kurulu olarak kabul edin. PATH dışa aktarımı, `/setup` işleminin geri kalanında Claude Code yeniden başlatılmadan node'un bulunabilmesi için geçerli Bash oturumuna özgüdür.

Doğrulama geçişinden sonra herhangi bir araç hâlâ eksikse araç adını ve şu tek satırı yazdırın: `<araç> kurulumu tamamlanamadı. /setup komutunu tekrar deneyin. İki kez başarısız olursa <aracı> manuel olarak yükleyin, ardından /setup komutunu bir kez daha çalıştırın.` Adım 3'ü tamamlandı işaretlemeyin. Durdurun.

Tüm araçlar mevcutsa adım 3'ü tamamlandı olarak işaretleyin.

## Adım 4: git'i idempotent şekilde yapılandır

`~/Reklam-Fabrikasi/_meta/.state/setup/os.txt` dosyasından işletim sistemini okuyun.

```
git config --global init.defaultBranch main
```

macOS'ta:

```
git config --global core.autocrlf input
```

Windows'ta:

```
git config --global core.autocrlf true
git config --global core.longpaths true
```

Bu çağrılar zaten idempotent'tir (son yazma kazanır, aynı değer işlemsizdir). Adım 4'ü tamamlandı olarak işaretleyin.

## Adım 5: Bulut senkronizasyon tehlikelerini algıla (bilgilendirici)

Proje çıktıları, Claude Code'un açık olduğu klasöre gider. Bir klasörde çalıştırdığınız ilk beceri, iCloud yönetimli bir konumun içinde "Reklam Fabrikası/" oluşturmayı reddeder ve seçilen klasör OneDrive içindeyse uyarır. Bu adım, söz konusu sonraki kontrol için ilgili işaretleri kaydeder.

### macOS, iCloud Depolama Optimize Etme

```
defaults read com.apple.bird OptimizeStorage 2>/dev/null || echo "0"
```

`1` dönerse uyarın: `iCloud Depolama Optimize Etme açık. Claude Code'u bir marka klasöründe açarken ~/Library/Mobile Documents/com~apple~CloudDocs/ içine koymaktan kaçının; iCloud dosyaları silebilir. Bunun yerine ~/Desktop/<marka>/ gibi yerel bir klasör kullanın.`

### Windows, OneDrive yeniden yönlendirmesi

`%USERPROFILE%` değerinin OneDrive içinde çözümlenip çözümlenmediğini kontrol edin:

```
echo "$USERPROFILE" | grep -i OneDrive >/dev/null && echo REDIRECTED || echo OK
```

REDIRECTED çıktısı gelirse uyarın: `Ana klasörünüz OneDrive'a yeniden yönlendirilmiş. ~/Desktop ve ~/Documents altındaki klasörler buluta senkronize olabilir ve büyük oluşturma işlemlerini yavaşlatabilir. Olduğu gibi bırakabilir veya becerileri çalıştırmadan önce Claude Code'u senkronize edilmeyen bir konumda açabilirsiniz.`

### Makine durum ağacını onayla

Reklam Fabrikası, kurulum günlüklerini ve makine düzeyindeki durumu `~/Reklam-Fabrikasi/_meta/` konumunda tutar. Var olduğunu onaylayın (SessionStart hook bunu zaten sağlar, ama yine de kontrol edin):

```
ls -d "$HOME/Reklam-Fabrikasi/_meta"
```

Varsa `Machine state ready at ~/Reklam-Fabrikasi/_meta` yazdırın; yoksa oluşturmak için `bash ~/.claude/plugins/cache/reklam-fabrikasi/reklam-fabrikasi/*/scripts/ensure-folders.sh` çalıştırın. Adım 5'i tamamlandı olarak işaretleyin.

## Adım 6: Playwright Chromium'u ön ısıt

Playwright MCP, Yol B tarayıcı otomasyonu ve marka DNA renk örnekleme için Chromium'un indirilmiş olmasını gerektirir. Bu olmadan her iki özelliğin ilk kullanımı 60 saniyenin üzerinde takılır. Şimdi ön ısıtın.

Zaten yüklenip yüklenmediğini kontrol edin. Playwright önbelleği hem `chromium-<rev>` hem de `chromium_headless_shell-<rev>` dizinlerini kullanır. Herhangi birini kabul ediyoruz:

```
{
  ls -d "$HOME/Library/Caches/ms-playwright/chromium"* 2>/dev/null
  ls -d "$HOME/AppData/Local/ms-playwright/chromium"* 2>/dev/null
} | head -n 1
```

Herhangi bir chromium dizini varsa `Playwright Chromium zaten yüklü.` yazdırın ve adım 6'yı tamamlandı işaretleyin.

Yoksa kullanıcıya şunu söyleyin: `Playwright Chromium indiriliyor. Yaklaşık 150MB, bağlantıya göre 30 ila 90 saniye sürer.` Ardından:

```
npx --yes playwright install chromium
```

Tamamlanmasını bekleyin. Başarılı olursa `Playwright Chromium hazır.` yazdırın ve adım 6'yı tamamlandı işaretleyin.

Başarısız olur veya zaman aşımına uğrarsa bir kez daha deneyin. İkinci girişim de başarısız olursa adım 6'yı tamamlandı işaretlemeyin, ama kurulumu da engellemeyin. Şunu yazdırın: `Playwright Chromium indirilemedi. İhtiyaç duyduğunda (marka DNA, Yol B) indirmeyi tekrar deneyen beceri halleder. Kurulum devam ediyor.`

## Adım 7: Ortam sağlığını doğrula

Bu kontrolleri tek bir Bash çağrısıyla paralel çalıştırın:

```
{ claude plugin list 2>/dev/null | grep reklam-fabrikasi; } &
{ claude mcp list 2>/dev/null; } &
{ ls -d "$HOME/Reklam-Fabrikasi/_meta" "$HOME/Reklam-Fabrikasi/_meta/.state" "$HOME/Reklam-Fabrikasi/_meta/.venvs" 2>/dev/null; } &
wait
```

Çıktıyı ayrıştırın:

- `claude plugin list` v1.2.0 veya daha yeni sürümde `reklam-fabrikasi` göstermelidir. Göstermiyorsa şunu yazdırın: `Eklenti beklenen sürümde değil. claude plugin marketplace update reklam-fabrikasi komutunu çalıştırıp tekrar deneyin.` ve durdurun.
- `claude mcp list` dört sunucu göstermelidir. Beklenen durumlar:
  - `apify`: `Connecting` veya `Connected` olabilir (HTTP MCP, her ikisi de kabul edilir)
  - `playwright`: `Connected` olmalıdır
  - `fal-ai`: kullanıcı anahtar ayarlayana kadar başarısız veya kimlik doğrulanmamış görünür (beklenen)
  - `higgsfield`: kullanıcı /mcp üzerinden OAuth girişini tamamlayana kadar başarısız veya kimlik doğrulanmamış görünür (beklenen)
- Makine durum ağacı (`~/Reklam-Fabrikasi/_meta`, `_meta/.state`) mevcut olmalıdır. Herhangi biri eksikse `bash ~/.claude/plugins/cache/reklam-fabrikasi/reklam-fabrikasi/*/scripts/ensure-folders.sh` çalıştırın.
- Proje çıktı klasörleri burada oluşturulmaz. Artık proje başınadır ve kullanıcı ilk becerisini çalıştırdığında Claude Code'un o anda açık olduğu klasörde tembel olarak oluşturulur.

Kısa bir kontrol listesi yazdırın:

```
[OK]   plugin Reklam Fabrikası v1.4.0
[OK]   mcp:apify
[OK]   mcp:playwright
[WAIT] mcp:fal-ai (ilk kullanımda yapılandırılacak)
[WAIT] mcp:higgsfield (/mcp üzerinden ilk kullanımda yapılandırılacak)
[OK]   ~/Reklam-Fabrikasi/_meta machine-state tree
```

Adım 7'yi tamamlandı olarak işaretleyin.

## Adım 8: `claude` PATH'te mi, otomatik düzelt

Yeni kurulumdan sonra sık görülen bir sorun: paketlenmiş `claude` CLI, `~/.local/bin/claude` (Mac ve Linux) veya `%USERPROFILE%\AppData\Local\AnthropicClaude\bin` tarzı konumlara (Windows) düşer ama ilgili dizin mevcut bash oturumunda PATH'te değildir. Kullanıcı daha sonra iş akışının ortasında `claude: command not found` hatasıyla karşılaşır ve nedenini anlamaz. Bunu, `/setup` tamamlandı demeden önce otomatik düzeltiyoruz.

`claude` PATH'te mi kontrol edin:

```
command -v claude >/dev/null 2>&1 && echo CLI_ON_PATH || echo CLI_OFF_PATH
```

`CLI_ON_PATH` çıktısı gelirse `[OK] claude on PATH at $(command -v claude)` yazdırıp Adım 9'a geçin.

`CLI_OFF_PATH` çıktısı gelirse kullanıcıya hiçbir şey sormayın. `/reklam-fabrikasi:repair-path` becerisinin çalıştırdığı mantığı doğrudan paketlenmiş yükleyici betiğini çağırarak uygulayın. Mevcut işletim sistemine göre betiği seçin:

```
PLUGIN_DIR="$(ls -td ~/.claude/plugins/cache/reklam-fabrikasi/reklam-fabrikasi/*/ 2>/dev/null | head -n 1)"
if [ -z "$PLUGIN_DIR" ]; then
  echo "[FAIL] plugin not installed. Fix: claude plugin install reklam-fabrikasi@reklam-fabrikasi --scope user"
  exit 1
fi
```

macOS veya Linux'ta:

```
bash "$PLUGIN_DIR/scripts/install-claude-on-path.sh"
```

Windows'ta (Git Bash):

```
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$PLUGIN_DIR/scripts/install-claude-on-path.ps1"
```

Betik döndükten sonra yeniden kontrol edin:

```
command -v claude >/dev/null 2>&1 && echo CLI_ON_PATH_AFTER_REPAIR || echo CLI_STILL_OFF_PATH
```

İkinci kontrol `CLI_ON_PATH_AFTER_REPAIR` dönerse `[OK] claude on PATH at $(command -v claude) (otomatik düzeltme başarılı)` yazdırıp Adım 9'a geçin. Adım 8'i tamamlandı işaretleyin.

İkinci kontrol `CLI_STILL_OFF_PATH` dönerse açık bir son hata mesajıyla dokümanlar bağlantısına işaret edin ve durdurun. Adım 8'i tamamlandı işaretlemeyin. Tam olarak şunu yazdırın:

> [FAIL] otomatik düzeltme `claude` komutunu bu kabuk için PATH'e ekleyemedi. Yeni bir terminal açın; yeni oturum açma kabuğu güncellenmiş profili alır, ardından `claude --version` çalıştırın. Hâlâ başarısız olursa Claude Code'u yeniden başlattıktan sonra `/reklam-fabrikasi:repair-path` komutunu manuel çalıştırın. Kurulum günlüğü burada: `~/Reklam-Fabrikasi/_meta/.state/install.log`.

Bu otomatik düzeltme yalnızca `claude` gerçekten PATH'te olmadığında tetiklenir. Sağlıklı bir kurulumda tek hızlı bir kontrol yapılır, başka yan etkisi yoktur.

## Adım 9: Son mesaj

Adım 8'de doğrulanan CLI konumunu okuyun (`CLAUDE_PATH="$(command -v claude)"`) ve son mesaja dahil edin. Tam olarak şunu yazdırın:

> Kurulum tamamlandı. Oluşturmaya başlamaya hazırsınız.
>
> Onaylandı: `claude` CLI, `<CLAUDE_PATH>` konumunda PATH'tedir.
>
> İlk iş akışınıza başlamak için `/welcome` yazın.
>
> Çıktı klasörleri, herhangi bir proje klasöründe bir beceriyi ilk çalıştırdığınızda otomatik olarak oluşturulur. Her marka veya müşteri kendi klasörünü alır. Claude Code'u `~/Desktop/<marka>/` (veya seçtiğiniz herhangi bir klasör) içinde açın; eklenti ilk beceri çalıştırıldığında orada markaya özel bir `Reklam Fabrikası/` alt klasörü oluşturur.
>
> İlk kullanımda bir API anahtarına ihtiyaç duyacak bir beceri var:
> - Fal AI (doğrudan API görüntü ve video üretimi için): istendiğinde `/reklam-fabrikasi:setup-fal-ai` aracılığıyla ayarlayın
>
> Şu an gerekmez. Beceriler ne zaman gerektiğini size söyler.
>
> Canlı Meta kampanya çalışması (analiz veya oluşturma) `/reklam-fabrikasi:meta-handoff` aracılığıyla yapılır. Bu beceri, claude.ai web uygulamasına yapıştırdığınız bağlam açısından zengin bir komut hazırlar; Meta'nın mcp.facebook.com/ads adresindeki resmi Ads MCP orada çalışır. Bu makine için Meta kimlik bilgisi saklanmaz. Kimlik doğrulama, claude.ai içindeki Meta'nın kendi OAuth akışı üzerinden gerçekleşir.

Adım 9'u tamamlandı olarak işaretleyin.

## Hata modu işleme özeti

Bu komuttaki açık işleyicilerin başvuru listesi:

- **Adım 3 yönetici onay penceresi:** brew veya winget UAC ya da sudo istemi tetikler. Kullanıcıya az önce açılan onay penceresini onaylamasını söyleyin. Bekleyin, yeniden denemeyin.
- **Adım 3 Windows'ta winget yok:** `where.exe winget` ile algılayın, yalnızca kullanıcı `yes` onayı verdikten sonra Scoop'a geri dönün. Hayır derlerse temiz çıkış yapın ve adım 3'ü tamamlandı işaretlemeyin.
- **Adım 3 Scoop nodejs-lts shim:** Scoop'un `nodejs-lts` paketi shim oluşturmaz; `~/scoop/apps/nodejs-lts/current` dizinini doğrudan PATH'e ekler. `command -v node` boş döndükten sonra her zaman bu konumu kontrol edin ve `/setup` oturumunun geri kalanı için dışa aktarın.
- **Adım 6 Playwright zaman aşımı:** bir kez daha deneyin. İkinci başarısızlıkta, ihtiyaç duyan sonraki beceriye erteleyin. Kurulumu yine de tamamlandı işaretleyin (Playwright isteğe bağlıdır).
- **Adım 7 eklenti sürüm uyumsuzluğu:** marketplace güncelleme talimatıyla durdurun. Tamamlandı işaretleme.
- **Adım 8 claude PATH'te değil:** `install-claude-on-path.sh` (Windows'ta `.ps1`) otomatik çalıştırın, kullanıcıya sormadan düzeltin. Yeniden kontrol edin. Hâlâ başarısız olursa doküman işaretçisiyle net son hata mesajı gösterin.
