# Paylaşım Notu — Otonom Kapak Üreticisi

## Mod
C — Şablona çevir

## Ne yapıldı

### Temizlenen sırlar
- Koda gömülü API anahtarı bulunmadı — tüm anahtarlar `os.getenv()` üzerinden okunuyor.
- `run_manual.py` (eski adı `run_manual_claude_code.py`) içindeki hardcoded kişisel
  mutlak `master.env` yolu kaldırıldı; artık proje kökündeki `.env`
  dosyasından okuyor.
- Owner'a ait trigger script'lerindeki hardcoded Notion sayfa ID'leri ve Google Drive
  klasör URL'leri içeren dosyalar tamamen silindi (aşağıya bakın).

### Scrub edilen kişisel veriler
- `core/google_auth.py`: kişisel Google hesap e-postaları (3 adet) → `<GOOGLE_HESABI>`
  placeholder; kişisel hesap anahtarı → jenerik `account2`
- `agents/learnings.md`: "Dolunay" isim referansları → "anchor kişisi / anchor fotoğraf"
- `main.py` ve `README.md`: "Dolunay Otonom Kapak" → "Otonom Kapak Üreticisi"
- `core/notion_service.py`: "Dolunay Reels & YouTube" DB adı yorumu jenerikleştirildi
- `agents/cutout_tags.json`: owner'ın gerçek yüz cutout dosya envanteri (23 dosya)
  → 3 satırlık placeholder şablon
- **Silinen dosyalar:** owner'ın yüz cutout fotoğrafları (`assets/cutouts/*.png`, 23 adet),
  storyboard referansları (`assets/refs/`), tüm üretilmiş kapaklar (`outputs/`, 90+ PNG),
  Notion screenshot'ları, owner'a özel trigger script'leri (`trigger_abacus7.py`,
  `trigger_kimi5*.py`, `trigger_topview5*.py` — hepsi gerçek Notion ID + Drive URL içeriyordu),
  owner'a özel test dosyaları (`test_identity_lock.py`, `test_gpt_image_2_scenes.py`,
  `test_notion.py`), scratch dosyaları
- `assets/cutouts/` klasörü boş bırakıldı, açıklayıcı `README.md` eklendi

### Eklenen dosyalar
- `trigger_example.py` — owner trigger'larının yerine jenerik tek-video tetikleme şablonu
- `assets/cutouts/README.md` — anchor fotoğrafların nasıl ekleneceğini anlatır
- `.env.example` — placeholder'lı ortam değişkeni şablonu
- `.gitignore` / `.railwayignore` düzeltildi (eskiden `trigger_*.py` ve `run_*.py`
  ignore ediliyordu — yeni örnek dosyalar git'e girebilsin diye pattern daraltıldı)

## Öğrenci ne yapmalı

1. `.env.example` → `.env` kopyalayın, tüm `<...>` placeholder'ları kendi
   anahtarlarınızla doldurun (Notion, Kie AI, Gemini, ImgBB, Google OAuth)
2. Notion'da video takip database'i oluşturun, ID'sini `.env`'e girin
3. Kendi yüz referans fotoğraflarınızı `assets/cutouts/` klasörüne koyun
   (bkz. `assets/cutouts/README.md`)
4. `agents/cutout_tags.json` içine fotoğraf dosya adlarınızı ve meta-verileri girin
5. `trigger_example.py` veya `run_manual.py` içindeki `TODO:` alanlarını kendi
   video bilgilerinizle doldurarak test edin
6. `python main.py --type reels` ile çalıştırın

## Mod C — Orijinal amaç → yeni jenerik çerçeve

**Orijinal:** Belirli bir içerik üreticisinin kendi Reels/YouTube videoları için
kapak üreten production servisi — kendi yüz fotoğrafı kütüphanesi, kendi Notion
veritabanı, kendi Drive klasörleri ve kendi videoları için yazılmış trigger'larla
dolu canlı bir sistem.

**Yeni çerçeve:** Herhangi bir içerik üreticisinin kullanabileceği genel amaçlı
"video kapak/thumbnail üretici" pipeline'ı. Identity Lock mimarisi, Gemini Vision
self-review, otomatik iterasyon ve çoklu-tema üretim deseni korundu. Owner'a özel
her şey (yüz fotoğrafları, Notion/Drive bağları, kişiye özel trigger'lar) çıkarıldı;
öğrenci kendi anchor fotoğraflarını koyup kendi içeriğini bağlayarak kullanır.
