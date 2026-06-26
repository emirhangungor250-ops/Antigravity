# Paylasim Notu — kie-ai-video-production

**Mod:** A

## Ne yapildi
- Birden fazla dosyada hardcoded gercek API anahtarlari temizlendi:
  - Kie AI API key (`97d226...`, `0bf011...`) → `<KIE_AI_API_KEY>`; scriptlerde env degiskeninden okunacak sekilde duzeltildi.
  - ImgBB API key (`77ae1f...`) → `<IMGBB_API_KEY>`.
- Etkilenen dosyalar: `scripts/kie_poll.sh`, `scripts/seedance_test.sh`, `SKILL.md`, `pipelines/*.md`, `models/elevenlabs-tts.md`.

## Ogrenci ne yapmali
- `KIE_AI_API_KEY` ve `IMGBB_API_KEY` degiskenlerini ortam degiskeni / `master.env` olarak ayarlayin.
