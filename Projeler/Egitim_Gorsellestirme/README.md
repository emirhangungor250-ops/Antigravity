# Egitim_Gorsellestirme

Eğitimlerde anlatılan konseptleri (örneğin "evrim aşamaları" gibi metaforlar) interaktif, scroll-bazlı tek sayfalık web görselleri olarak sunan statik HTML projesi. Topluluk eğitimlerinde slayt yerine kullanılır.

## Stack
Vanilla HTML + CSS + JavaScript. Build adımı yok — `index.html` direkt tarayıcıda açılır.

## Çalışma Şekli
Statik dosyalar:
- `index.html` — sayfa iskeleti, aşama section'ları
- `style.css` — animasyon ve layout
- `script.js` — scroll progress bar + section reveal animasyonları
- `assets/` — slayt görselleri (kendiniz koyarsınız)

Lokal görüntüleme: `open index.html` (veya basit bir HTTP server). İçerik güncellenmek istenirse `index.html` içindeki `<section class="stage">` blokları düzenlenir.

## Environment Setup
Bu proje environment değişkeni kullanmaz. Tamamen statik.

## Deploy
Deploy yok. Lokal `open index.html` veya istenirse Netlify/GitHub Pages'e drag-drop ile yüklenebilir.
