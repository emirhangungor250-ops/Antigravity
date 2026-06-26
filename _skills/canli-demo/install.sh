#!/usr/bin/env bash
# Canlı demo bağımlılığını (cloudflared) paket içine kurar.
# brew gerekmez; doğrudan GitHub release binary'sini indirir.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BIN_DIR="${SCRIPT_DIR}/bin"
mkdir -p "${BIN_DIR}"

UNAME_S="$(uname -s)"
UNAME_M="$(uname -m)"

case "${UNAME_S}_${UNAME_M}" in
  Darwin_arm64)  ASSET="cloudflared-darwin-arm64.tgz" ;;
  Darwin_x86_64) ASSET="cloudflared-darwin-amd64.tgz" ;;
  Linux_x86_64)  ASSET="cloudflared-linux-amd64" ;;
  Linux_aarch64) ASSET="cloudflared-linux-arm64" ;;
  *)
    echo "❌ Desteklenmeyen platform: ${UNAME_S} ${UNAME_M}" >&2
    exit 1
    ;;
esac

URL="https://github.com/cloudflare/cloudflared/releases/latest/download/${ASSET}"
echo "→ İndiriliyor: ${URL}"

cd "${BIN_DIR}"
if [[ "${ASSET}" == *.tgz ]]; then
  curl -fsSL -o "${ASSET}" "${URL}"
  tar -xzf "${ASSET}"
  rm "${ASSET}"
else
  curl -fsSL -o cloudflared "${URL}"
fi
chmod +x cloudflared

echo "✓ Kuruldu: ${BIN_DIR}/cloudflared"
"${BIN_DIR}/cloudflared" --version
