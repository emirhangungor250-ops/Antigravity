# Shorts Dizi Fabrikası — Senaryodan Tam Otomatik AI Mini Dizi

Tek bir senaryo metninden, tutarlı karakterlerle, tam otomatik dikey (9:16) YouTube
Shorts mini dizisi üretir. Önce kalıcı bir "dizi kitabı" kurulur (karakterler + ses
kimlikleri + ortamlar + aksesuarlar + sanat stili). Sonra her bölüm 6-10 sahneye bölünür,
sahne sahne video üretilir, ffmpeg ile sesli birleştirilir ve Google Drive'a yüklenir.
Karakter ve stil tutarlılığı; sabit karakter kimlikleri + referans görseller + kilitli
bir stil bloğuyla sağlanır, böylece her bölüm aynı evrende geçer.

## Bu desen ne işine yarar

Aynı karakterlerle düzenli kısa video serisi üretmek isteyen herkes için: korku-gerilim
mini dizileri, eğitici çizgi seriler, marka maskotu içerikleri, hikâye anlatımı kanalları.
Senaryoyu sen yazarsın; fabrika dizi kitabını kurar, bölümleri üretir ve birleştirir.
"Dizi kitabı bir kez kurulur, her bölümde aynen kullanılır" mantığı tutarlılığın anahtarıdır.

## Stack

Python · Kie AI (gemini-omni-video / character / audio + nano-banana-2 görsel) · bir LLM
(senarist + dizi kitabı; varsayılan ucuz model, `.env`'den değiştirilir) · ImgBB (referans
görsel host'u) · ffmpeg (imageio-ffmpeg) · Google Drive API (çıktı yükleme)

## Çalışma Şekli

```
python main.py kur   --senaryo senaryo.md --seri <slug>   # dizi kitabı + referanslar (1 kez)
python main.py bolum --seri <slug> [--konu "..."] [--devam] [--test]
python main.py durum --seri <slug>
```

`senaryo_mini_test.md` örnek bir senaryodur; kendi senaryonla değiştir. Seri durumu
`seriler/<slug>/` altında JSON olarak yaşar; her sahne geçişi diske yazılır, yarıda kesilen
bölüm `--devam` ile kaldığı yerden sürer (aynı task'a yeniden poll, çifte ödeme yok).
`--test`: 2 sahne × 4 sn @720p ucuz duman testi.

## Environment Setup

`.env.example` → `.env` kopyala, kendi anahtarlarını gir: `KIE_API_KEY`, `ANTHROPIC_API_KEY`
(veya kendi LLM sağlayıcın), `IMGBB_API_KEY`. Drive yüklemesi için Google OAuth token'ı
(`GOOGLE_OUTREACH_TOKEN_JSON` veya lokal token dosyası) gerekir.
`ENV=development` tüm dış API'leri taklitle çalıştırır (sıfır maliyet, fixture döner).

## Deploy

Lokalde komutla çalışır. 7/24 ister bir sunucuya taşırsan `railway.json` Railway için
hazırdır (`startCommand: python main.py`); arg yerine `MODE` + `SERI_SLUG` env'leri kullanılır.
Seri durumu diskte yaşar; cloud'da kalıcı disk yoksa state her deploy'da sıfırlanır, taşımadan
önce bunu çöz.

## Maliyet uyarısı

Senaryo/dizi kitabı için varsayılan model bilinçli olarak ucuz seçilmiştir. Pahalı bir model
(Opus/Sonnet sınıfı) varsayılan yapma; gerçekten gerekmedikçe ucuz modelde kal. Video üretimi
(Kie kredisi) asıl maliyet kalemidir; `MAX_EPISODE_CREDITS` ile bölüm başına bütçe koyabilirsin.
