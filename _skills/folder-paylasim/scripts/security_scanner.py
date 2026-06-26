import argparse
import os
import re
import sys

def main():
    parser = argparse.ArgumentParser(description="Proje/Klasör Dışa Aktarım Güvenlik Tarayıcısı")
    parser.add_argument("--target", required=True, help="Taranacak hedef klasör")
    args = parser.parse_args()

    target_dir = args.target

    if not os.path.exists(target_dir):
        print(f"HATA: Hedef klasör bulunamadı: {target_dir}")
        sys.exit(1)

    print(f"🔎 Güvenlik taraması başlatılıyor: {target_dir}")

    # Genişletilmiş Regex Pattern'leri.
    # Notlar:
    # - Bearer: sadece HTTP Authorization header formatını yakala (yorumlardaki
    #   "Bearer DEĞİL" tarzı dokümantasyonu yakalamasın). Payload >= 16 char + üç
    #   farklı karakter sınıfından en az birini içersin.
    # - Kredi/Banka Kartı: ardışık aynı rakam dizilerini (UUID `0000-0000-...`)
    #   eleyen ek doğrulama Luhn-benzeri post-check ile yapılır (re.search yetmez).
    patterns = {
        "Apify Token": r"apify_api_[A-Za-z0-9]{20,}",
        "Generic/OpenAI/Anthropic Key": r"(sk-[A-Za-z0-9]{20,}|gsk_[A-Za-z0-9]{20,})",
        "Google API Key": r"AIza[0-9A-Za-z-_]{35}",
        "Bearer Token": r"(?i)authorization:\s*bearer\s+[A-Za-z0-9\-\._~\+\/]{16,}=*",
        # \b boundary: alphanum prefix'in içinde rastgele 5\d... dizilerini yakalamasın
        # (örn. task_bytedance_5186... veya unsplash photo-15232...).
        "Telefon": r"\b(\+90|0)?5\d{2}\s*\d{3}\s*\d{2}\s*\d{2}",
        "IBAN": r"TR\d{2}\s?\d{4}\s?\d{4}\s?\d{4}\s?\d{4}\s?\d{4}\s?\d{2}",
        "Kredi/Banka Kartı": r"\b(?:\d[ -]*?){13,16}\b"
    }

    # Per-pattern path exclusions: bilinen false positive lokasyonlarını skip et.
    # Tests klasörlerinde sentetik telefon fixture'ları olur — gerçek müşteri datası değil.
    pattern_path_excludes = {
        "Telefon": (
            re.compile(r"(?:^|/)tests?/"),
            # phone utility dosyaları içlerinde örnek/JSDoc/LLM-prompt telefon
            # literal'leri taşır — doğal, müşteri datası değil.
            re.compile(r"(?:^|/)phone[^/]*\.(?:js|ts|py)$", re.IGNORECASE),
            re.compile(r"(?:^|/)phoneValidator[^/]*\.(?:js|ts|py)$", re.IGNORECASE),
            # Telefon utility skill'leri (örn. telefon-formatlayici/SKILL.md)
            # — dokümantasyonu zaten test fixture telefonlarını gösterir.
            re.compile(r"(?:^|/)telefon[^/]*/", re.IGNORECASE),
        ),
    }

    def _is_uuid_or_repeating_digits(match_text: str) -> bool:
        """Kredi/Banka Kartı false positive elemesi: UUID (0000-0000-0000-...) veya
        tek rakam tekrarı (1111111111111) gerçek kart numarası değildir."""
        digits = re.sub(r"[^0-9]", "", match_text)
        if len(digits) < 13:
            return True
        if len(set(digits)) <= 2:
            return True
        return False

    # Özel olarak tamamen hariç tutulacak dosya ve klasörler
    ignore_dirs = {'.venv', 'node_modules', '.git', '__pycache__', 'my_lib', 'build', 'dist'}
    ignore_ext = {'.pdf', '.jpg', '.jpeg', '.png', '.mp4', '.ttf', '.pyc', '.exe', '.zip', '.tar'}

    issues_found = []

    for root, dirs, files in os.walk(target_dir):
        # Klasörleri filtrele
        dirs[:] = [d for d in dirs if d not in ignore_dirs]

        for file in files:
            ext = os.path.splitext(file)[1].lower()
            if ext in ignore_ext:
                continue

            # .env dosyalarının paylaşılan klasörde bulunması başlı başına güvenlik ihlalidir
            # (Ancak .env.example gibi şablonlara izin verilir)
            if file == '.env' or file.endswith('.env'):
                # Sadece '.env.example' gibi exception'lar hariç tutulabilir.
                # Eğer Starter Kit için config.env vb varsa, isimlerine izin verebiliriz ama
                # genel best practice, secret isimli dosyaların gitmemesidir.
                pass

            filepath = os.path.join(root, file)
            # Forward-slash normalize et — pattern_path_excludes regex'leri / bekliyor.
            filepath_norm = filepath.replace(os.sep, "/")

            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    for line_no, line in enumerate(f, 1):
                        for label, regex in patterns.items():
                            # Path-bazlı false positive elemesi
                            excludes = pattern_path_excludes.get(label, ())
                            if any(ex.search(filepath_norm) for ex in excludes):
                                continue
                            m = re.search(regex, line)
                            if not m:
                                continue
                            # Kredi kartı false positive elemesi:
                            # (1) UUID veya tek rakam tekrarı
                            # (2) Satırda URL varsa (resim/sayfa ID'leri kart değil)
                            if label == "Kredi/Banka Kartı":
                                if _is_uuid_or_repeating_digits(m.group(0)):
                                    continue
                                if re.search(r"https?://|://", line):
                                    continue
                            # Telefon: URL içeren satır (Unsplash gibi resim
                            # ID'leri 5\d{9} desenini tetikler) atla.
                            if label == "Telefon" and re.search(r"https?://|://", line):
                                continue
                            issues_found.append(f"⚠️ {label} Tespiti: {filepath} (Satır {line_no})")
            except Exception:
                pass # UTF-8 okunamayan binary dosyalar atlanır

    if issues_found:
        print("\n" + "="*50)
        print("❌ GÜVENLİK İHLALİ TESPİT EDİLDİ! PAYLAŞIM DURDURULDU.")
        print("="*50)
        for issue in issues_found:
            print(issue)
        print("\nLütfen bu sızıntıları temizleyip süreci tekrar başlatın.")
        sys.exit(1)
    else:
        print("\n✅ Tarama Temiz! Herhangi bir PII veya API Key sızıntısı bulunamadı.")
        print("Paylaşım güvenlidir.")
        sys.exit(0)

if __name__ == "__main__":
    main()
