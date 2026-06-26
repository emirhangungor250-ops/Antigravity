# Fal.ai MCP Sunucusu, Claude Code Kurulum Rehberi

Yeni Claude Code kullanıcılarının **fal.ai MCP sunucusunu** eklemesi için pratik rehber; üç premium model için tam referans şemaları ve araç kataloğu.

---

## 1. fal.ai MCP nedir?

[fal.ai](https://fal.ai), görüntü, video, ses, 3D ve LLM iş yükleri için 1.000'den fazla modele sahip üretken medya API platformudur. Resmi **fal-ai MCP sunucusu**, tüm bu modelleri Claude Code'a tek bir MCP bağlantısıyla sunar; keşif, şema arama, fiyatlandırma, dosya yükleme, senkron çalıştırma ve asenkron işler Claude oturumunda birinci sınıf araçlara dönüşür.

---

## 2. Ön koşullar

1. **Bir fal.ai API anahtarı,** [fal.ai](https://fal.ai)'ye kayıt ol ve panelden bir anahtar al. Anahtar formatı `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx:hex...` şeklindedir.
2. **Claude Code kurulu,** ya bağımsız CLI (`npm install -g @anthropic-ai/claude-code`) ya da macOS için Claude masaüstü uygulaması.

> **macOS masaüstü uygulaması kullanıcıları:** `claude` CLI, uygulamanın içinde şurada gömülüdür:
> `~/Library/Application Support/Claude/claude-code/<sürüm>/claude.app/Contents/MacOS/claude`
> ve `PATH`'te **değildir**. Ya bu yolu doğrudan kullan ya da takma ad oluştur:
> ```bash
> alias claude='/Users/$USER/Library/Application\ Support/Claude/claude-code/$(ls ~/Library/Application\ Support/Claude/claude-code | sort -V | tail -1)/claude.app/Contents/MacOS/claude'
> ```

---

## 3. fal-ai MCP sunucusunu ekle

### Seçenek A, Proje kapsamı (test için önerilen)

fal-ai'nin mevcut olmasını istediğin proje klasörünün içinden çalıştır:

```bash
claude mcp add --transport http fal-ai \
  https://mcp.fal.ai/mcp \
  --header "Authorization: Bearer YOUR_FAL_KEY"
```

`YOUR_FAL_KEY` yerine gerçek fal.ai API anahtarını koy. Sunucu, `~/.claude.json` içinde o projenin girişine kaydedilir.

### Seçenek B, Kullanıcı kapsamı (her yerde erişilebilir)

```bash
claude mcp add --scope user --transport http fal-ai \
  https://mcp.fal.ai/mcp \
  --header "Authorization: Bearer YOUR_FAL_KEY"
```

### Doğrulama

```bash
claude mcp list
```

Şunu görmelisin:

```
fal-ai: https://mcp.fal.ai/mcp (HTTP) - ✓ Connected
```

### Yeniden yükle

Ekledikten sonra **Claude Code oturumunu yeniden yükle** (kapat ve yeniden aç, ya da masaüstü uygulamasını yeniden başlat). Yeni `mcp__fal-ai__*` araçları bir sonraki oturumda görünür.

---

## 4. fal-ai MCP, tam araç kataloğu

### Keşif

| Araç | Ne yapar |
|---|---|
| `search_models` | fal'ın 1.000'den fazla modellik kataloğunu anahtar kelime veya kategoriye göre arar |
| `get_model_schema` | Herhangi bir model için tam girdi/çıktı parametrelerini getirir |
| `get_pricing` | Kullanmadan önce bir modeli çalıştırmanın maliyetini kontrol eder |
| `search_docs` | Rehberler, örnekler ve API referansları için fal belgelerini arar |

### Çalıştırma

| Araç | Ne yapar |
|---|---|
| `run_model` | Herhangi bir modeli çalıştırır ve sonucu bekler (görüntü, video, ses vb.) |
| `submit_job` | Uzun süren bir iş gönderir ve istek ID'siyle hemen döner |
| `check_job` | İş durumunu kontrol eder, sonuçları getirir ya da çalışan işi iptal eder |

### Yardımcı

| Araç | Ne yapar |
|---|---|
| `upload_file` | Model girdisi olarak kullanmak üzere fal CDN'ine dosya (yerel yol veya URL) yükler |
| `recommend_model` | Ne yapmak istediğini açıkla ve model önerileri al |

**İş akışı kılavuzu:** `recommend_model` veya `search_models` -> `get_model_schema` -> `get_pricing` -> `run_model` (senkron) veya `submit_job` + `check_job` (asenkron).

---

## 5. Model referansı

Tam girdi şeması, varsayılanlar ve reklam-kreatif çalışması için önerilen **premium / maksimum kalite** ayarlarıyla üç üretime hazır model.

---

### 5.1 `bytedance/seedance-2.0/reference-to-video`

ByteDance'ın en gelişmiş referanstan videoya modeli. 9'a kadar görüntü, 3 video ve 3 ses klibiyle yerel ses ve sinematik kamera kontrolüyle video üretir.

**Fiyatlandırma:** birim başına 0,014 dolar

**Zorunlu girdi**

| Parametre | Tür | Notlar |
|---|---|---|
| `prompt` | string | Yüklenen medyaya `@Image1`, `@Video1`, `@Audio1` vb. olarak başvur |

**İsteğe bağlı girdi**

| Parametre | Tür | Varsayılan | Seçenekler / Notlar |
|---|---|---|---|
| `aspect_ratio` | string | `auto` | `21:9`, `16:9`, `4:3`, `1:1`, `3:4`, `9:16`, `auto` |
| `duration` | string | `auto` | `4`, `15` saniye veya `auto` |
| `resolution` | string | `720p` | `480p`, `720p`, `1080p` |
| `generate_audio` | bool | `true` | Senkronize SFX, ortam sesi, dudak senkronizasyonu. Maliyet her iki durumda aynı. |
| `image_urls` | array&lt;string&gt; | | Her biri ≤ 30 MB, **9**'a kadar JPEG/PNG/WebP |
| `video_urls` | array&lt;string&gt; | | **3**'e kadar MP4/MOV, toplam 2-15s, ≤ 50 MB toplam, ~480p, 720p |
| `audio_urls` | array&lt;string&gt; | | **3**'e kadar MP3/WAV, toplam ≤ 15s, her biri ≤ 15 MB. En az bir görüntü veya video gerektirir. |
| `seed` | int \| null | | Tekrarlanabilirlik |
| `end_user_id` | string \| null | | Son kullanıcı atıfı |

> Tüm modalitelerdeki toplam medya dosyaları **12'yi geçmemeli**.

**Çıktı**

| Alan | Tür |
|---|---|
| `video` | file |
| `seed` | int |

**Premium varsayılanlar**

```json
{
  "resolution": "1080p",
  "duration": "15",
  "generate_audio": true,
  "aspect_ratio": "16:9"
}
```

---

### 5.2 `fal-ai/nano-banana-2` (metinden görüntüye)

Google'ın son teknoloji hızlı görüntü üretim ve düzenleme modeli (Gemini 3.1 Flash Image).

**Zorunlu girdi**

| Parametre | Tür | Notlar |
|---|---|---|
| `prompt` | string | Serbest metin |

**İsteğe bağlı girdi**

| Parametre | Tür | Varsayılan | Seçenekler / Notlar |
|---|---|---|---|
| `aspect_ratio` | string \| null | `auto` | Aşırı oranları destekler: `4:1`, `1:4`, `8:1`, `1:8` |
| `resolution` | string | `1K` | `0.5K`, `1K`, `2K`, `4K` |
| `output_format` | string | `png` | `jpeg`, `png`, `webp` |
| `num_images` | int | `1` | |
| `thinking_level` | string \| null | kapalı | `minimal`, `high`; çıktıda akıl yürütme döndürür |
| `enable_web_search` | bool | `false` | Modelin üretimeye canlı web bilgisi çekmesine izin verir |
| `safety_tolerance` | string | `4` | `1` (katı) - `6` (gevşek) |
| `limit_generations` | bool | `true` | Her prompt turunu 1 görüntüyle sınırlar. Prompt içi sayım talimatlarını uygularsa `false` yap. |
| `seed` | int \| null | | Tekrarlanabilirlik |
| `sync_mode` | bool | `false` | Veri URI'si döndürür; sonuç istek geçmişinde olmaz |

**Çıktı**

| Alan | Tür |
|---|---|
| `images` | array |
| `description` | string (modelin ürettiklerinin açıklaması) |

**Premium varsayılanlar**

```json
{
  "resolution": "4K",
  "output_format": "png",
  "thinking_level": "high",
  "enable_web_search": true,
  "num_images": 1
}
```

---

### 5.3 `openai/gpt-image-2` (metinden görüntüye)

OpenAI'nin en yeni görüntü modeli; ince tipografi ile son derece ayrıntılı görüntüler.

**Zorunlu girdi**

| Parametre | Tür | Notlar |
|---|---|---|
| `prompt` | string | Serbest metin |

**İsteğe bağlı girdi**

| Parametre | Tür | Varsayılan | Seçenekler / Notlar |
|---|---|---|---|
| `image_size` | object \| string | `landscape_4_3` | Ön ayar adı VEYA `{width, height}`. Her iki boyut 16'nın katı, maksimum kenar 3840px, oran ≤ 3:1, toplam piksel 655.360 - 8.294.400. |
| `quality` | string | `high` | `low`, `medium`, `high` |
| `output_format` | string | `png` | `jpeg`, `png`, `webp` |
| `num_images` | int | `1` | |
| `sync_mode` | bool | `false` | Veri URI'si döndürür; sonuç istek geçmişinde olmaz |

**Çıktı**

| Alan | Tür |
|---|---|
| `images` | array |

**Premium varsayılanlar**

```json
{
  "image_size": { "width": 3840, "height": 2160 },
  "quality": "high",
  "output_format": "png",
  "num_images": 1
}
```

> 3840 × 2160 = 8.294.400 piksel; 16:9'da modelin üst sınırı.

---

## 6. Hızlı karşılaştırma

| Özellik | Seedance 2.0 ref→video | Nano Banana 2 | GPT Image 2 |
|---|---|---|---|
| Çıktı | Video (+ ses) | Görüntü | Görüntü |
| Maksimum çözünürlük | 1080p | 4K | ~3840px kenar |
| Çok referanslı girdi | 9 görüntü + 3 video + 3 ses | yalnızca metin | yalnızca metin |
| Web araması | | ✓ | |
| Düşünme modu | | ✓ | |
| Kalite kontrolü | çözünürlük tabanlı | çözünürlük tabanlı | düşük / orta / yüksek |
| Fiyatlandırma | birim başına 0,014 dolar | (`get_pricing` çalıştır) | (`get_pricing` çalıştır) |

---

## 7. İlk test çalıştırması (doğrulama)

Yeniden yüklendikten sonra Claude Code'a sor:

> "fal-ai ile 'flux schnell' için model ara, şemayı al ve sonra 'bisiklete binen bir kızıl panda' promptuyla çalıştır."

Sonuçta üretilmiş bir görüntü URL'si görüyorsan kurulum uçtan uca çalışıyor demektir.

---

## 8. Sorun giderme

| Belirti | Çözüm |
|---|---|
| `claude: command not found` | Paketlenmiş ikili yolu kullan (ön koşullara bak) veya npm CLI'yi kur |
| `mcp list` `✗ Failed to connect` gösteriyor | Geçersiz/süresi dolmuş API anahtarı; yeni anahtarla sunucuyu yeniden ekle |
| Yeni araçlar oturumda görünmüyor | Claude Code'u yeniden yükle (kapat ve yeniden aç, ya da masaüstü uygulamasını yeniden başlat) |
| Yetkilendirme başlığı `YOUR_FAL_KEY` olarak kalıyor | Yer tutucuyu değiştirmeyi unutmuşsun; üzerine yazmak için `mcp add`'i yeniden çalıştır |
| Proje kapsamlı sunucu yalnızca tek klasörde görünüyor | Global yapmak için `--scope user` ile yeniden ekle |

---

## 9. Faydalı bağlantılar

- fal.ai paneli ve API anahtarları: https://fal.ai/dashboard
- fal.ai model kataloğu: https://fal.ai/models
- Claude Code MCP belgeleri: https://docs.claude.com/en/docs/claude-code/mcp
- MCP sunucu uç noktası: `https://mcp.fal.ai/mcp` (HTTP taşıma, Bearer kimlik doğrulaması)
