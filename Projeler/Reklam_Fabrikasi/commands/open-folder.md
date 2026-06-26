---
description: Mevcut projenin "Reklam Fabrikası" klasörünü (Claude Code'un açık olduğu çalışma klasöründeki "./Reklam Fabrikası") macOS'te Finder'da, Windows'ta Dosya Gezgini'nde açar.
---

# /open-folder

Kullanıcı az önce `/open-folder` yazdı. Mevcut çalışma klasöründeki "Reklam Fabrikası" alt klasörünü aç.

Reklam Fabrikası artık çıktıları proje bazlı yazıyor, yani bu komut Claude Code'un şu an açık olduğu marka veya müşteri klasörünü açar. Her çalışma klasörünün kendi bağımsız "Reklam Fabrikası" alt klasörü vardır.

## Ne yapmalı

Platformu tespit edip doğru komutu çalıştırmak için Bash aracını kullan. Verdiğin mesaj kullanıcıya tam olarak hangi klasörü açtığını göstersin diye önce mutlak yolu `pwd` ile çöz.

### macOS veya Linux

```
TARGET="$(pwd)/Reklam Fabrikası"
if [ ! -d "$TARGET" ]; then
  echo "MISSING:$TARGET"
else
  if command -v open >/dev/null 2>&1; then
    open "$TARGET"
  else
    xdg-open "$TARGET"
  fi
  echo "OPENED:$TARGET"
fi
```

### Windows

```
$target = Join-Path (Get-Location).Path "Reklam Fabrikası"
if (-not (Test-Path $target)) {
  Write-Output "MISSING:$target"
} else {
  Start-Process explorer.exe $target
  Write-Output "OPENED:$target"
}
```

## Kullanıcıya ne söylemeli

- Script `OPENED:<yol>` yazdıysa: tek satırla yanıtla. "`<yol>` klasörünü dosya gezgininde açtım."
- Script `MISSING:<yol>` yazdıysa: yanıtla: "Bu klasörde henüz çıktı yok. Yapıyı oluşturmak için önce bir beceri çalıştır (`/next` dene ya da ne yapmak istediğini anlat), ya da Claude Code'u daha önce çalıştığın bir klasörde aç."

Klasörü burada otomatik oluşturma. Kullanıcının bu klasörde çalıştıracağı ilk beceri onay isteyip yapıyı rızasıyla oluşturur.

Em-dash yok. Kısa tut.
