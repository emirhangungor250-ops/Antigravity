#!/usr/bin/env bash
# baslat.sh — one-shot JARVIS setup + launch (macOS).
# First run installs everything; later runs just start. Idempotent.
set -e
cd "$(dirname "$0")"

# Finder'dan (Jarvis.app) açıldığında GUI ortamının PATH'i dar olur; npm/node
# /usr/local/bin veya /opt/homebrew/bin'de durur ama PATH'te olmayabilir. Standart
# kurulum dizinlerini ekle ki "npm: command not found" ile build adımında ölmeyelim.
export PATH="/usr/local/bin:/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin:$HOME/.nvm/versions/node/*/bin:$PATH"

echo "▶ JARVIS — hazırlık..."

# --- Python backend deps (venv) ---
if [ ! -d venv ]; then
  python3 -m venv venv
fi
source venv/bin/activate
pip install -q --disable-pip-version-check -r requirements.txt
# Playwright Chromium (for the web-automation/browse features); skip silently if present
python -c "import playwright" 2>/dev/null && playwright install chromium >/dev/null 2>&1 || true

# --- Frontend build (only if needed). Önemli: npm yoksa VEYA build hazırsa ATLA;
# bu adım 'set -e' altında sunucuyu engellemesin (eski hata: Jarvis.app açılışında
# npm bulunamayınca script burada ölüyor, sunucu hiç başlamıyordu). dist hazırsa
# zaten gerek yok; frontend kaynağı değişince elle 'npm run build' yapılır.
if command -v npm >/dev/null 2>&1; then
  if [ ! -d frontend/node_modules ]; then
    ( cd frontend && npm install --silent ) || true
  fi
  if [ ! -f frontend/dist/index.html ]; then
    ( cd frontend && npm run build --silent ) || ( cd frontend && npm run build ) || true
  fi
else
  echo "ℹ npm bulunamadı; mevcut frontend/dist kullanılacak (build atlandı)."
fi
# Güvenlik: dist hâlâ yoksa dürüst uyar (sunucu yine de açılır, sayfa boş gelebilir).
[ -f frontend/dist/index.html ] || echo "⚠ frontend/dist yok; arayüz görünmeyebilir."

# --- Fish Audio voice key check ---
if ! grep -q '^FISH_API_KEY=.\+' .env 2>/dev/null; then
  echo ""
  echo "⚠  Ses için Fish Audio anahtarı eksik."
  echo "   fish.audio'dan ücretsiz token al, .env içindeki FISH_API_KEY= satırına yapıştır."
  echo "   (Anahtar olmadan JARVIS düşünür ama konuşmaz.)"
  echo ""
fi

# --- Launch backend (serves built frontend at http://127.0.0.1:8340) ---
echo "▶ JARVIS başlıyor → http://127.0.0.1:8340"
echo "  Tarayıcıda aç, bir kez tıkla, konuş. Durdurmak için Ctrl+C."

# Sunucu venv python'u ile çalışmalı (playwright + Pillow + bağımlılıklar orada).
# venv yukarıda 'source' edildi; yine de doğru yorumlayıcıyı garanti et.
if [ -x ./venv/bin/python ]; then
  # Sunucu sağlık verince JARVIS sekmesini ana Chrome'da aç (arka planda bekler).
  ( for i in $(seq 1 40); do
      if curl -sf -o /dev/null "http://127.0.0.1:8340" 2>/dev/null; then
        open -a "Google Chrome" "http://127.0.0.1:8340" 2>/dev/null || true
        break
      fi
      sleep 0.5
    done ) &
  exec ./venv/bin/python server.py
else
  exec python server.py
fi
