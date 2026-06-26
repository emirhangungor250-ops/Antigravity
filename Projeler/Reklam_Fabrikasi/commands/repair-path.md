---
description: Kendi kendini onarma komutu. Eklenti ile gelen Claude CLI'ını kullanıcının PATH'ine ekler. /doctor CLI'ın sağlıksız olduğunu bildirirse çalıştır.
---

# /repair-path

Mevcut işletim sistemi için install-claude-on-path scriptini yeniden çalıştırır; eklenti ile gelen `claude` CLI binary'sini bulur ve kalıcı bir PATH sembolik bağı oluşturur.

Tekrar çalıştırması güvenlidir. Her an çalıştırılabilir.

## Ne yapmalı

Bash aracını kullan. İşletim sistemini tespit et, en son kurulan eklenti dizinini bul, sonra scripti çalıştır.

### macOS / Linux

```
PLUGIN_DIR="$(ls -td ~/.claude/plugins/cache/reklam-fabrikasi/reklam-fabrikasi/*/ 2>/dev/null | head -n 1)"
if [ -z "$PLUGIN_DIR" ]; then
  echo "[FAIL] plugin not installed. Fix: claude plugin install reklam-fabrikasi@reklam-fabrikasi --scope user"
  exit 1
fi
echo "Repair: claude CLI on PATH"
bash "$PLUGIN_DIR/scripts/install-claude-on-path.sh"
```

### Windows

```
$pluginRoot = Join-Path $env:USERPROFILE ".claude\plugins\\cache\\reklam-fabrikasi\\reklam-fabrikasi"
$pluginDir  = (Get-ChildItem -Directory $pluginRoot | Sort-Object LastWriteTime -Descending | Select-Object -First 1).FullName
Write-Host "Repair: claude CLI on PATH"
powershell -NoProfile -ExecutionPolicy Bypass -File "$pluginDir\scripts\install-claude-on-path.ps1"
```

## Çıktı

Scriptin stdout çıktısını ekrana yansıt. Script kendi OK / WARN satırlarını zaten içeriyor.

Onarımdan sonra:

- CLI'ı doğrula: `command -v claude` (Mac/Linux) ya da `Get-Command claude` (Windows). Yolu göster.

Doğrulama başarılıysa şununla bitir:
> Onarım tamam. `claude` CLI artık PATH'te.

Başarısızsa, kullanıcının destek için paylaşabilmesi adına `~/Reklam-Fabrikasi/_meta/.state/install.log` yolunu vererek bitir.

Em-dash yok. Kısa tut.
