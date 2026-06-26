#!/usr/bin/env bash
# Yol B (Higgsfield CLI) için smoke testi. Kurulumdan sonra ya da CLI
# sürümü değiştiğinde çalıştır. Her kontrol geçerse 0, ilk başarısızlıkta
# sıfır olmayan kodla çıkar.
#
#   ./scripts/smoke-test-path-b.sh
#
# Kontroller, sırayla:
#   1. higgsfield ikili dosyasına erişilebiliyor
#   2. higgsfield --version bir şey döndürüyor
#   3. higgsfield auth token başarılı (kullanıcı giriş yapmış)
#   4. higgsfield model list becerilerin kullandığı kimlikleri içeriyor
#   5. higgsfield generate cost, 9:16 4K'da GPT Image 2 için bir sayı döndürüyor

set -eu

HIGGS_BIN="$(command -v higgsfield 2>/dev/null || echo "$HOME/.local/bin/higgsfield")"

if [ ! -x "$HIGGS_BIN" ]; then
  echo "FAIL: higgsfield ikili dosyası bulunamadı. Çalıştır: npm install -g @higgsfield/cli"
  exit 1
fi

echo "OK: ikili dosya: $HIGGS_BIN"

CLI_VERSION="$("$HIGGS_BIN" --version 2>/dev/null || true)"
if [ -z "$CLI_VERSION" ]; then
  echo "FAIL: higgsfield --version hiçbir şey döndürmedi"
  exit 1
fi
echo "OK: CLI sürümü $CLI_VERSION"

if ! "$HIGGS_BIN" auth token >/dev/null 2>&1; then
  echo "FAIL: kimlik doğrulanmamış. Çalıştır: higgsfield auth login"
  exit 1
fi
echo "OK: kimlik doğrulandı"

MODEL_LIST="$("$HIGGS_BIN" model list 2>/dev/null || true)"
if [ -z "$MODEL_LIST" ]; then
  echo "FAIL: higgsfield model list hiçbir şey döndürmedi"
  exit 1
fi

for expected_id in gpt_image_2 nano_banana_flash; do
  if ! echo "$MODEL_LIST" | grep -q "$expected_id"; then
    echo "FAIL: model kimliği '$expected_id' katalogda yok. Mevcut olanlar:"
    echo "$MODEL_LIST"
    exit 1
  fi
  echo "OK: model '$expected_id' mevcut"
done

COST_OUTPUT="$("$HIGGS_BIN" generate cost gpt_image_2 \
  --prompt "smoke test" \
  --aspect_ratio "9:16" \
  --quality "high" \
  --resolution "4k" 2>&1 || true)"

if ! echo "$COST_OUTPUT" | grep -qiE '[0-9]+\s*(credit|cost)'; then
  echo "FAIL: maliyet kuru çalışması bir kredi sayısı döndürmedi. Çıktı:"
  echo "$COST_OUTPUT"
  exit 1
fi
echo "OK: maliyet kuru çalışması bir değer döndürdü"

echo ""
echo "Tüm Yol B smoke kontrolleri geçti."
exit 0
