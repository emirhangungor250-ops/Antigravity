# -*- coding: utf-8 -*-
"""Deterministik metin şablonları.

- Tanıştırma (intro): gönderenin ağzından, neredeyse sabit -> şablon (otomatik gönderim güvenli).
- Teklif fallback: LLM patlarsa yöneticinin ağzından deterministik teklif (taslak).

İmza adları config.SENDER_NAME / config.MANAGER_NAME (ENV)'den gelir.
"""
import re

import config

# ── Gönderen tanıştırma maili ─────────────────────────────
def intro_body(language, brand_first_name=None):
    sender = config.SENDER_NAME or ("Ben" if language == "tr" else "Me")
    manager = config.MANAGER_NAME or ("Partnerships Manager" if language == "tr" else "my Partnerships Manager")
    # TR'de hitap saygı eki ister; deterministik fallback cinsiyeti bilemez -> güvenli "Bey/Hanım".
    greeting = f"Merhaba {brand_first_name} Bey/Hanım," if (language == "tr" and brand_first_name) else \
               (f"Hi {brand_first_name}," if brand_first_name else ("Merhaba," if language == "tr" else "Hi,"))
    if language == "tr":
        return (f"{greeting}\n\n"
                "Çok teşekkürler. İş birliği için memnuniyetle görüşelim.\n\n"
                f"Sizi Partnerships Manager'ım {manager} ile tanıştırıyorum (CC'de). "
                "Detayları ve teklifimizi kendisi paylaşacak.\n\n"
                f"Sevgiler,\n{sender}")
    return (f"{greeting}\n\n"
            "Thank you very much. We're happy to connect and explore this collaboration.\n\n"
            f"I am connecting you with my Partnerships Manager, {manager}, who is CC'd here. "
            "They will share our offer and the details.\n\n"
            f"Best regards,\n{sender}")


# ── Yönetici teklif (LLM fallback) ────────────────────────
# Em-dash YOK; TR/EN aynı kanonik fiyat yapısı (WRITER_SYSTEM rate card ile hizalı:
# config.PRICE_SHORT / PRICE_LONG / PRICE_BUNDLE); referans yoksa 'örnekler' bölümü atlanır.
def _ref_line(r):
    """Tek referans satırı; BOŞ alanları atlar. Fallback'te '- None -' / boş '()' / sarkan ':'
    çıkmasın (select_references sıfır-izlenme/boş-konu satırı dönebilir)."""
    brand = (r.get("brand") or "").strip()
    topic = (r.get("topic") or "").strip()
    url = (r.get("url") or "").strip()
    views = (r.get("views_label") or "").strip()
    head = " - ".join(p for p in (brand, topic) if p)
    tail = f" ({views})" if views else ""
    return f"   - {head}: {url}{tail}" if head else f"   - {url}{tail}"


def offer_fallback(language, brand_name, references):
    name = brand_name or ("markanız" if language == "tr" else "your brand")
    sender = config.SENDER_NAME or ("içerik üreticimiz" if language == "tr" else "our creator")
    manager = config.MANAGER_NAME or ("Partnerships Manager" if language == "tr" else "Partnerships Manager")
    ps, pl, bundle = config.PRICE_SHORT, config.PRICE_LONG, config.PRICE_BUNDLE
    if language == "tr":
        ref = "\n".join(_ref_line(r) for r in references)
        ref_block = (f"Son dönemden bazı örnekler:\n\nInstagram\n{ref}\n\n" if references else "")
        return (f"Merhaba,\n\n"
                f"Ulaştığınız için teşekkürler. Ben {manager}, {sender}'in Partnerships Manager'ıyım; "
                f"süreci buradan ben yürüteceğim.\n\n"
                f"{sender}; AI, teknoloji ve dijital araçlar alanında içerik üretiyor. "
                f"{name} ile güçlü bir uyum olduğunu düşünüyoruz.\n\n"
                f"{ref_block}"
                f"Paket ve fiyatlarımız:\n"
                f"   - Kısa video paketi (Instagram Reel + Story + Gönderi, cross-post): {ps}\n"
                f"   - YouTube dedicated uzun video: {pl}\n"
                f"   - İkisi birlikte (avantajlı paket): {bundle}\n"
                f"Her paket: 1 dedicated video (script + video onayı + 1 revize), comment-to-DM otomasyonu, "
                f"3 ay kullanım hakkı, reklam yetkisi + Spark code, video 100K izlenmeye ulaşmazsa bonus Story.\n\n"
                f"Size en doğru teklifi sunabilmemiz için: öncelikli platform, hedef tarih ve "
                f"3 aydan uzun usage rights ihtiyacınız olup olmadığını paylaşır mısınız?\n\n"
                f"Süreci kolay takip etmek adına ilerleyişi e-posta üzerinden yürütmeyi tercih ediyoruz.\n\n"
                f"Sevgiler,\n{manager}")
    ref = "\n".join(_ref_line(r) for r in references)
    ref_block = (f"Here are a few recent examples in the same space:\n\nInstagram\n{ref}\n\n"
                 if references else "")
    return (f"Hi,\n\n"
            f"Thank you for reaching out, and great to connect. I'm {manager}, {sender}'s Partnerships "
            f"Manager, and I'll be your point of contact from here.\n\n"
            f"{sender}'s audience is highly engaged with AI tools and apps, so {name} sounds like a "
            f"strong fit.\n\n"
            f"{ref_block}"
            f"Our packages and pricing:\n"
            f"   - Short-form package (Instagram Reel + Story + Post, cross-posted to Reels/Shorts/TikTok): {ps}\n"
            f"   - YouTube dedicated long-form video: {pl}\n"
            f"   - Both together (bundle): {bundle}\n"
            f"Each package includes 1 dedicated video (script and video approval, plus 1 revision), "
            f"comment-to-DM automation, 3-month usage rights, ad code + Spark code, and a bonus Story "
            f"if the video does not reach 100K views.\n\n"
            f"To finalize the right setup, could you share your budget range, ideal go-live timeline, "
            f"and whether you need usage rights beyond the standard 3-month window?\n\n"
            f"Once we have these, we can lock in the proposal. We'd also prefer to keep the process over "
            f"email so everything stays well documented.\n\n"
            f"Best,\n{manager}")


# From display'i kişi adı DEĞİL (marka/rol/sistem kutusu) işaret eden kelimeler.
# Display-name'de kelime olarak geçerse gönderen kişi değildir -> hitap nötr olur.
# (Hitap bug sınıfı: 'PixelFlow AI' / 'Sales Team' / 'noreply' -> 'X Bey/Hanım' YANLIŞ.)
_NON_PERSON_TOKENS = {
    "team", "ekip", "sales", "satış", "marketing", "mktg", "pazarlama", "partnerships",
    "partner", "partners", "growth", "media", "press", "pr", "agency", "ajans", "info",
    "hello", "hi", "contact", "iletisim", "iletişim", "support", "destek", "noreply",
    "no-reply", "donotreply", "do-not-reply", "brand", "brands", "official", "hq", "inc",
    "llc", "ltd", "gmbh", "co", "corp", "studio", "studios", "labs", "lab", "ai", "io",
    "app", "collab", "collabs", "collaboration", "collaborations", "creators", "creator",
    "outreach", "newsletter", "bulten", "bülten", "notifications", "notification",
    "account", "accounts", "billing", "admin", "office", "the", "team.",
}
# Honorific'ler: SET'e koyma (segmenti komple eler, 'Murat Bey' -> None olurdu). Ayrı ele:
# baştan/sondan sıyır, KİŞİ sinyali say. Tek başına honorific olan display -> ad değil.
_HONORIFICS = {"bey", "hanım", "hanim", "bay", "bayan", "sn"}
# Baştaki unvanlar (atlanır; sonraki kelime ön ad sayılır).
_TITLES = {"dr", "prof", "mr", "mrs", "ms", "mx", "miss", "sayin", "sayın",
           "av", "doc", "doç", "uzm", "op"}


def _cap_one(p):
    return {"i": "İ", "ı": "I"}.get(p[0], p[0].upper()) + p[1:] if p else p


_TR_CHARS = set("çğıöşüâîûÇĞİÖŞÜ")   # Türkçe'ye ÖZGÜ harfler (i/ı dotting kararı bunlara bakar)


def _tr_title_token(w):
    """Tek ad parçasını sunum-haline getir: TÜMÜ büyük ('ZEYNEP') ya da tümü küçük ('ahmet') ise
    Title-case; zaten karışık ('Ayşe','McAfee') ise DOKUNMA. Tire/apostrofla birleşik adların HER
    parçasını büyütür ('MEHMET-ALI'->'Mehmet-Ali', \"D'ANGELO\"->\"D'Angelo\"). I->ı dönüşümü YALNIZ
    Türkçe harf içeren adda (IŞIL->Işıl, KIVANÇ->Kıvanç korunur); yabancı adda standart (WILLIAM->William,
    PIERRE->Pierre — 'Wıllıam' bozulması yok)."""
    if not w or not (w.isupper() or w.islower()):
        return w
    if any(ch in _TR_CHARS for ch in w):
        low = w.replace("İ", "i").replace("I", "ı").lower()   # Türkçe-duyarlı (i̇ bozulması yok)
    else:
        low = w.lower()                                        # yabancı: standart küçültme
    if not low:
        return w
    return re.sub(r"[^\W\d_]+", lambda mo: _cap_one(mo.group()), low, flags=re.UNICODE)


# Ad ayraçları: 'Marka - Kişi' / 'Kişi | Marka' / 'Marka • Kişi' (boşluksuz tireyi BOZMA: 'Mehmet-Ali').
_NAME_SEP_RE = re.compile(r"\s*[|•·/]\s*|\s+[-–—]\s+")


def _seg_person(seg):
    """Tek display segmentinden (ön_ad|None, ad_kelime_sayısı, honorific_vardı_mı).
    Baştaki unvanı (Dr.) ve sondaki honorific'i (Bey/Hanım) sıyırır; 'Soyad, Ad' çözülür.
    Honorific = güçlü KİŞİ sinyali (markada 'Bey' olmaz) -> ayraçlı seçimde kişiyi kurtarır."""
    s = (seg or "").strip()
    if "," in s:                                  # segment içi 'Soyad, Ad' -> virgülden sonrası ön ad
        after = s.split(",", 1)[1].strip()
        if after:
            s = after
    words = [w for w in re.split(r"\s+", s) if w]
    while words and words[0].lower().strip(".") in _TITLES:        # baştaki unvanları at
        words.pop(0)
    had_hon = False
    while words and words[-1].lower().strip(".,") in _HONORIFICS:   # sondaki honorific'i sıyır (kişi sinyali)
        words.pop()
        had_hon = True
    if not words:
        return None, 0, False
    if {w.lower().strip(".,") for w in words} & _NON_PERSON_TOKENS:   # marka/rol işareti
        return None, 0, False
    cand = words[0].strip(".,")
    if cand.lower() in _HONORIFICS or len(cand) < 2 or any(ch.isdigit() for ch in cand):
        return None, 0, False
    if not re.match(r"^[^\W\d_][\w'\-]*$", cand, re.UNICODE):   # harfle başlayan ad gibi mi
        return None, 0, False
    return _tr_title_token(cand), len(words), had_hon   # 'ZEYNEP' -> 'Zeynep'


def first_name_from(header_value):
    """From display-name'den GÜVENLİ kişi ön adı. Kişi adı değilse (marka/rol/sistem kutusu,
    unvan-only, tek harf, rakamlı) None döner -> çağıran nötr 'Merhaba,'/'Hi,' kullanır.
    'Soyad, Ad' biçimini çözer, baştaki unvanı atar. 'Aylin Demir <x@y>' -> 'Aylin'.
    Ayraçlı 'Marka SEP Kişi' / 'Kişi SEP Marka' (| • · / ya da boşluklu - – —): GÜÇLÜ kişi adayını
    (2+ kelime 'Ad Soyad' VEYA honorific'li) seçer ('Best Of The Best - Yasin Ocak'->'Yasin',
    'Murat Bey | TechCorp'->'Murat'); iki güçlü aday ya da hepsi belirsizse None (marka SIZMASIN)."""
    m = re.match(r'\s*"?([^"<@]+?)"?\s*<', header_value or "")
    if not m:
        return None
    raw = m.group(1).strip().strip("'\"").strip()
    if not raw or "@" in raw:
        return None
    segs = [s for s in _NAME_SEP_RE.split(raw) if s.strip()]
    if len(segs) >= 2:
        persons = [_seg_person(s) for s in segs]
        strong = [nm for nm, n, hon in persons if nm and (n >= 2 or hon)]   # 'Ad Soyad' / honorific'li
        if len(strong) == 1:
            return strong[0]
        weak = [nm for nm, n, hon in persons if nm and n == 1 and not hon]
        if not strong and len(weak) == 1:
            return weak[0]          # tek zayıf aday (diğerleri marka/rol) -> al
        return None                 # 0 ya da 2+ güçlü/zayıf -> belirsiz -> nötr selam
    return _seg_person(raw)[0]
