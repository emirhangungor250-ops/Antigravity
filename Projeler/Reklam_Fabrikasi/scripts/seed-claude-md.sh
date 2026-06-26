#!/usr/bin/env bash
# Bir beceri marka klasörünü onayladıysa ve henüz CLAUDE.md yoksa,
# <pwd>/Reklam Fabrikası/ içine başlangıç CLAUDE.md'si yerleştir.
#
# Bu dosya markanın yaşayan kural kitabıdır. Marka klasörü bağlamda
# olduğunda Claude Code onu otomatik yükler, yani buraya kaydedilen her
# kural her gelecekteki oturuma ve her gelecekteki beceri çalıştırmasına
# uygulanır.
#
# İki yerden çağrılır:
#   1. SessionStart hook'u (bu özellikten önceki marka klasörlerinde ya da
#      İLK ÇALIŞTIRMA yerleştirmesinin kaçtığı yerlerde dönen oturumları yakalar)
#   2. Her becerinin İLK ÇALIŞTIRMA KORUMASI bloğu, marka klasörü onaylanıp
#      folder-confirmed.flag yazıldıktan hemen sonra
#
# Idempotent. Yapacak bir şey yoksa sessizce 0 ile çıkar. Tekrar çağrılması
# güvenli. Mevcut bir CLAUDE.md'nin asla üzerine yazmaz.

set -u

# Eklenti kökünü bu scriptin kendi konumundan çöz. Bu her bağlamda
# güvenilirdir, SessionStart'ta bozuk olan CLAUDE_PLUGIN_ROOT'un aksine
# (upstream Claude Code issue 27145).
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLUGIN_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
TEMPLATE="$PLUGIN_DIR/skills/_shared/claude-md-template.md"

# Projenin marka klasörünü çöz. Burada OLUŞTURMUYORUZ, bu her becerinin
# İLK ÇALIŞTIRMA KORUMASI bloğunun sorumluluğudur; o blok herhangi bir
# klasör oluşturmadan önce kullanıcıdan onay ister.
PROJECT_ROOT="${PWD}/Reklam Fabrikası"
CLAUDE_MD="${PROJECT_ROOT}/CLAUDE.md"

# Yalnızca marka klasörü zaten varsa yerleştir. Beceri kullanıcıya çoktan
# sormuş, folder-confirmed.flag bırakmış ve klasör ağacını oluşturmuştur.
# Klasör yoksa marka hafızasını bağlayacak bir şey yoktur.
[ -d "$PROJECT_ROOT" ] || exit 0

# Mevcut bir CLAUDE.md'nin asla üzerine yazma. Bir kez yerleştirildiğinde
# dosya markaya aittir ve Claude oradan itibaren kendi günceller.
[ -f "$CLAUDE_MD" ] && exit 0

# Mümkünse paketle gelen şablonu tercih et. Şablon dosyası eksikse
# satır-içi minimal sürüme geri düşer (savunma amaçlı, sağlıklı bir
# kurulumda olmaması gerekir).
if [ -f "$TEMPLATE" ]; then
  cp "$TEMPLATE" "$CLAUDE_MD" 2>/dev/null || exit 0
else
  cat > "$CLAUDE_MD" <<'EOF'
# Reklam Fabrikası için marka hafızası

Bu dosya markanın yaşayan kural kitabıdır. Kullanıcı eklentiyi kullandıkça
Claude onu kendi günceller.

## Bu dosya nasıl güncellenir (Claude'a talimatlar)

Kullanıcı bir marka tercihi, kısıtı veya düzeltmesi belirttiğinde, bu dosyayı
Edit aracıyla güncelle. Yeni girdi mevcut bir kuralla çelişiyorsa eski kuralı
değiştir. Örtüşüyorsa birleştir. Yeniyse aşağıdaki doğru bölüme bugünün
tarihiyle ekle. Her değişiklikten sonra, kullanıcının doğrulayabilmesi için
tek satır söyle.

## Marka Kuralları

(boş)

## Yasak Kelimeler ve İfadeler

(boş)

## Görsel Kurallar

(boş)

## Son gözden geçirme

(bu dosya değiştiğinde otomatik güncellenir)
EOF
fi

# Son gözden geçirme satırını bugünün UTC tarihiyle damgala, böylece
# kullanıcı dosyaya en son ne zaman dokunulduğunu görebilir. Elden geldiğince,
# bu yüzden script asla başarısız olmaz.
TODAY="$(date -u +%Y-%m-%d 2>/dev/null || echo '')"
if [ -n "$TODAY" ] && [ -f "$CLAUDE_MD" ]; then
  # BSD sed (macOS) ve GNU sed (Linux) genelinde taşınabilir yerinde düzenleme.
  TMP="${CLAUDE_MD}.tmp"
  sed "s|(bu dosya[^)]*)|$TODAY|" "$CLAUDE_MD" > "$TMP" 2>/dev/null \
    && mv "$TMP" "$CLAUDE_MD" 2>/dev/null
  rm -f "$TMP" 2>/dev/null || true
fi

echo "[reklam-fabrikasi] Marka hafızası şuraya yerleştirildi: $CLAUDE_MD"
exit 0
