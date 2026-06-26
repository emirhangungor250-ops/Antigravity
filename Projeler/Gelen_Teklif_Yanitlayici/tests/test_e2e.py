# -*- coding: utf-8 -*-
"""Uçtan uca test.

Bölüm A — Karar beyni (en kritik): gerçekçi mail metinleriyle LLM niteleme +
  deterministik aksiyon kararı. Yanlış-pozitif (collab olmayanı işleme) ve
  düşük teklifi otomatik gönderme yok — bunları doğrular. Hiç mail göndermez.
Bölüm B — Referans seçimi (Notion) + yönetici teklif yazımı kalitesi.
Bölüm C (--live) — Tam canlı mekanik: marka maili gönder -> tanıştırma -> yönetici
  teklif TASLAĞI; thread + To/CC doğrulanır. Sadece --live ile.

NOT: Bölüm A/B gerçek LLM çağrısı yapar (OPENAI_API_KEY* gerekir). Bölüm C ise gerçek
Gmail hesapları arasında mail gönderir (config.ADDR doldurulmuş olmalı). Önce DRY_RUN ile
mantığı doğrula; canlı çağrıları minimumda tut.
"""
import sys, os, time
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import config
from services import llm, notion_portfolio as NP, gmail_ops as G
from core import templates as T

PASS, FAIL = [], []

# Test senaryolarında gönderenin (sender) kutusu olarak kullanılacak adres.
# config.ADDR['inbox_primary'] doldurulmuşsa onu, yoksa jenerik bir örnek adres kullan.
SENDER_ADDR = config.ADDR.get("inbox_primary") or "you@yourdomain.com"


def check(name, cond, detail=""):
    (PASS if cond else FAIL).append(name)
    print(f"  [{'PASS' if cond else 'FAIL'}] {name}" + (f" — {detail}" if detail else ""))


# ── Bölüm A: karar senaryoları ────────────────────────────
SCENARIOS = {
    "confident_en": {
        "text": f"""--- [Mon, 2 Jun 2026] FROM: Sarah Chen <sarah@growthlabs.io> TO: {SENDER_ADDR}
SUBJECT: Paid Collaboration Opportunity with PixelFlow AI
Hi there, I'm Sarah handling creator partnerships at PixelFlow AI, an AI tool that turns text prompts into scroll-stopping short videos. We love your AI content and would like to do a PAID dedicated short-form video across your platforms (Reels / Shorts / TikTok). Could you share your rates and availability? Best, Sarah""",
        "expect_collab": True, "expect_lang": "en", "expect_action": "auto_intro",
    },
    "confident_tr": {
        "text": f"""--- [Sal, 3 Haz 2026] FROM: Oğuz Han <dev@oyunstudyo.com> TO: {SENDER_ADDR}
SUBJECT: Marka İş Birliği Teklifi
Merhaba, AI destekli oyun platformumuz için sizinle ücretli bir Instagram Reels iş birliği yapmak istiyoruz. Bütçemiz hazır. Güncel reklam/tanıtım fiyatlarınızı paylaşabilir misiniz? Teşekkürler, Oğuz""",
        "expect_collab": True, "expect_lang": "tr", "expect_action_not": "ignore",
    },
    "lowball_commission": {
        "text": f"""--- [Per, 12 Mar 2026] FROM: Cora <creatorcollabs@kolconnecthub.com> TO: {SENDER_ADDR}
SUBJECT: Partnering with Nextify
Hi, We are opening paid collaborations. We'd love to feature two projects (Pipiads + Nextify.ai) in a single video for $250 + 4 months membership for each project + 20% commission for Pipiads + 30% commission for Nextify, with 2-3 minutes intro each. Let us know! Best, Cora""",
        "expect_collab": True, "expect_action": "draft_intro",
    },
    "newsletter": {
        "text": f"""--- [Çar, 3 Haz 2026] FROM: LawChat <bulten@lawchat.com.tr> TO: {SENDER_ADDR}
SUBJECT: Yeni: Detaylı Dilekçe Aracı Yayında
Merhaba, LawChat'e yeni bir özellik ekledik: artık detaylı dilekçe oluşturabilirsiniz. UYAP entegrasyonumuzu da deneyin. Keyifli kullanımlar!""",
        "expect_collab": False, "expect_action": "ignore",
    },
    "renewal": {
        "text": f"""--- [Çar, 3 Haz 2026] FROM: Beatrice Wang <beatrice@brightnote.ai> TO: {SENDER_ADDR}
SUBJECT: Invitation to Renew Collaboration + Updated Brief
Hi, we really enjoyed our last two collaborations and would love to renew for a third paid video, this time featuring BrightNote's new Image 2 feature. Are the same terms okay? Best, Beatrice""",
        "expect_collab": True, "expect_action": "draft_intro",
    },
    "inscope_dashcam": {
        "text": f"""--- [Mon, 2 Jun 2026] FROM: Mark Reed <mark@roadcampro.com> TO: {SENDER_ADDR}
SUBJECT: Paid Collaboration with RoadCam Pro
Hi there, I'm Mark from RoadCam Pro. We make premium 4K dashcams for cars (car accessory hardware, no app or AI). We'd love a PAID dedicated short-form video across your platforms featuring our new dashcam. Our budget is ready. Could you share your rates? Best, Mark""",
        # Dashcam tüketici elektroniği = kapsam içi (config.SCOPE_NOTE'taki gibi bir kapsamda).
        # Ücretli + yeni + iyi + kapsam-içi -> otomatik tanıştır.
        "expect_collab": True, "expect_action": "auto_intro",
    },
    "inbound_sales": {
        "text": f"""--- [Çar, 3 Haz 2026] FROM: Jane from Emergent <team@ship.emergent.sh> TO: {SENDER_ADDR}
SUBJECT: skip the blank screen
Hey there, We've put together a collection of pre-built apps on Emergent: landing pages, business tools and more. Pick one and make it yours. Start building today!""",
        "expect_collab": False, "expect_action": "ignore",
    },
    # PROGRAM DAVETİ: marka bize ödeme yapmıyor, bizi kendi programına çağırıyor -> iş birliği DEĞİL.
    "program_recruitment": {
        "text": f"""--- [Mon, 8 Jun 2026] FROM: Alex Rivera <value@creatorcircle.com> TO: {SENDER_ADDR}
SUBJECT: Huge opportunity for content creators
I'm looking to partner with a small elite group of educational content creators with over 100k+ followers to help you make more from your existing audience. We added over 1,258,486 NEW users to our base. We need more HIGH QUALITY EDUCATORS. Join our creator/partner program and monetize your audience with us, all in starting July 1.""",
        "expect_collab": False, "expect_action": "ignore",
    },
    # Gönderenin KENDİ HİZMETİNİ satın alma (kurumsal eğitim) -> iş birliği DEĞİL, yöneticiye GİTMEZ.
    "corporate_training": {
        "text": f"""--- [Mon, 15 Dec 2025] FROM: Selin Kaya <selin@acmeyayin.com.tr> TO: {SENDER_ADDR}
SUBJECT: Yapay Zeka Eğitiminiz Hk.
Merhaba, Acme Akademi'de çalışıyorum. Şirketimizdeki yapay zeka projemiz kapsamında üretken yapay zeka ve otomasyon eğitimleriniz hakkında bilgi almak istiyoruz. Eğitim başlıklarını paylaşabilir misiniz? Uygun olursa kısa bir toplantı ile iş birliği kapsamında değerlendirelim.""",
        "expect_collab": False, "expect_action": "ignore",
    },
    # Tanınmış marka + 'bütçe hazır' + 'iş birliği' dese BİLE asıl iş ekip eğitimi/workshop -> not_collab.
    "team_workshop_paid": {
        "text": f"""--- [Tue, 2 Jun 2026] FROM: Elif Demir <elif@acmebank.com.tr> TO: {SENDER_ADDR}
SUBJECT: Ekip eğitimi iş birliği
Merhaba, AcmeBank dijital ekibine özel bir yapay zeka ve otomasyon eğitimi vermenizi istiyoruz. Bu iş birliği için bütçemiz hazır. Günlük eğitim ücretinizi ve müsait tarihlerinizi paylaşır mısınız?""",
        "expect_collab": False, "expect_action": "ignore",
    },
}


def part_a():
    print("\n== Bölüm A: karar beyni ==")
    for name, sc in SCENARIOS.items():
        try:
            q = llm.qualify(sc["text"])
            action = llm.decide_action(q)
            print(f"  · {name}: collab={q.is_collaboration} type={q.collab_type} "
                  f"conf={q.confidence} quality={q.offer_quality} lang={q.language} -> {action}")
            if "expect_collab" in sc:
                check(f"{name}: is_collaboration={sc['expect_collab']}",
                      q.is_collaboration == sc["expect_collab"], q.reasoning[:80])
            if "expect_lang" in sc:
                check(f"{name}: lang={sc['expect_lang']}", q.language == sc["expect_lang"])
            if "expect_action" in sc:
                check(f"{name}: action={sc['expect_action']}", action == sc["expect_action"],
                      f"got {action}")
            if "expect_action_not" in sc:
                check(f"{name}: action!={sc['expect_action_not']}",
                      action != sc["expect_action_not"], f"got {action}")
        except Exception as e:
            check(f"{name}: qualify çalıştı", False, str(e)[:120])


# ── Bölüm A2: gönderen kara listesi (deterministik, API'siz) ──
def part_a2():
    print("\n== Bölüm A2: gönderen kara listesi ==")
    # Örnek: bir aracı ajansı domainini config.SENDER_BLOCKLIST'e koy -> bloklu olmalı.
    # (Burada test için geçici olarak bir domain ekleyip kaldırıyoruz.)
    config.SENDER_BLOCKLIST.append("aha.inc")
    config.SENDER_BLOCKLIST.append("ahacreator")
    try:
        check("Örnek ajans domaini bloklu",
              config.is_blocked_sender("support@creator.aha.inc", "Liz from AhaCreator"))
        # Ajansın pitch ettiği markalar doğrudan gelirse iş kaçmasın diye serbest kalmalı
        check("Aracının markaları serbest",
              not config.is_blocked_sender("hello@anygen.io", "AnyGen")
              and not config.is_blocked_sender("team@aident.ai", "Aident AI"))
        check("alakasız marka serbest", not config.is_blocked_sender("marketing@nike.com", "Nike"))
    finally:
        config.SENDER_BLOCKLIST.remove("aha.inc")
        config.SENDER_BLOCKLIST.remove("ahacreator")
    # Referans 'Konu' deterministik kısaltma (uzun video-başlığı teklife sızmasın)
    st = NP._short_topic("AI Video ve Görsel Üretimi, NanoBanana, AI Video Models", "Creati")
    check("_short_topic ilk virgülde kesti", st == "AI Video ve Görsel Üretimi", st)
    check("_short_topic 6 kelimeyi aşmıyor",
          len(NP._short_topic("bir iki üç dört beş altı yedi sekiz").split()) <= 6)
    check("_short_topic marka tekrarını atıyor",
          not NP._short_topic("Creati - AI video", "Creati").lower().startswith("creati"))


# ── Bölüm A3: hitap güvenliği + blocklist sınırı + fallback (deterministik, API'siz) ──
def part_a3():
    print("\n== Bölüm A3: hitap güvenliği + blocklist sınırı + fallback kuralları ==")
    from core import pipeline as P

    # first_name_from: gerçek kişi adı çalışır
    check("first_name_from gerçek ad", T.first_name_from('"Sarah Chen" <s@b.com>') == "Sarah")
    check("first_name_from TR ad", T.first_name_from("Oğuz Han <o@b.com>") == "Oğuz")
    # marka/rol/sistem adı -> None (Bey/Hanım yapışmasın, oto-gönderim güvenliği)
    for h in ('"PixelFlow AI" <h@p.ai>', "Sales Team <s@b.com>", "noreply <n@b.com>",
              "Partnerships <p@b.com>", "BrandX Marketing <m@b.com>"):
        check(f"first_name_from kişi-değil -> None: {h[:20]}", T.first_name_from(h) is None, repr(T.first_name_from(h)))
    # "Soyad, Ad" -> ön ad doğru (virgül/soyad sızmaz)
    check("first_name_from 'Soyad, Ad' -> ön ad", T.first_name_from('"Chen, Sarah" <s@b.com>') == "Sarah",
          repr(T.first_name_from('"Chen, Sarah" <s@b.com>')))
    # baştaki unvan atlanır
    check("first_name_from unvan atlar -> Ayşe", T.first_name_from("Dr. Ayşe Kaya <a@b.com>") == "Ayşe",
          repr(T.first_name_from("Dr. Ayşe Kaya <a@b.com>")))
    # tek harf reddedilir
    check("first_name_from tek harf -> None", T.first_name_from("X <x@b.com>") is None)
    # markanın KENDİ adı kişi sanılmaz (brand-name guard, pipeline katmanı)
    check("_person_first_name marka adını eler (Higgsfield)",
          P._person_first_name("Higgsfield <h@higgsfield.ai>", "Higgsfield") is None)
    check("_person_first_name gerçek kişiyi korur",
          P._person_first_name('"Sarah Chen" <s@higgsfield.ai>', "Higgsfield") == "Sarah")
    # bounce/no-reply adresi alıcı seçilmez
    check("_is_junk_addr postmaster", P._is_junk_addr("postmaster@bounce.sendgrid.net"))
    check("_is_junk_addr gerçek kişi değil", not P._is_junk_addr("sarah@brand.com"))

    # blocklist SINIR-FARKINDA: rotasyon domainleri bloklu, yanlış-pozitifler serbest
    config.SENDER_BLOCKLIST.append("aha.inc")
    config.SENDER_BLOCKLIST.append("ahacreator")
    try:
        check("blocklist creator.aha.inc bloklu", config.is_blocked_sender("support@creator.aha.inc", "AhaCreator"))
        check("blocklist ahacreator-vision bloklu", config.is_blocked_sender("x@ahacreator-vision.services", "Iris"))
        check("blocklist creator.ahacreator.com bloklu", config.is_blocked_sender("x@creator.ahacreator.com", "Tripo"))
        check("blocklist mahacreator.io SERBEST (FP fix)", not config.is_blocked_sender("team@mahacreator.io", "Maha Creator"))
        check("blocklist ahacreators.com SERBEST (FP fix)", not config.is_blocked_sender("hello@ahacreators.com", "Aha Creators"))
        check("blocklist brandaha.inc.co SERBEST (FP fix)", not config.is_blocked_sender("x@brandaha.inc.co", "Brand"))
        check("blocklist Nike serbest", not config.is_blocked_sender("marketing@nike.com", "Nike"))
    finally:
        config.SENDER_BLOCKLIST.remove("aha.inc")
        config.SENDER_BLOCKLIST.remove("ahacreator")

    # offer_fallback: em-dash yok, boş referansta boş 'örnekler' bloğu yok, fiyat kanonik (TR=EN)
    for lang in ("tr", "en"):
        empty = T.offer_fallback(lang, "TestBrand", [])
        check(f"offer_fallback em-dash yok ({lang})", "—" not in empty)
        check(f"offer_fallback boş-ref 'Instagram\\n' başlığı yok ({lang})", "Instagram\n" not in empty)
        check(f"offer_fallback kanonik fiyat ({lang})",
              config.PRICE_LONG in empty and config.PRICE_BUNDLE in empty, config.PRICE_BUNDLE)
    fake_refs = [{"brand": "Nim", "topic": "AI video", "url": "https://x.com/p", "views_label": "1M views"}]
    check("offer_fallback referanslıyken örnek cümlesi var", "recent examples" in T.offer_fallback("en", "TestBrand", fake_refs))
    check("offer_fallback boş-ref örnek cümlesi yok", "recent examples" not in T.offer_fallback("en", "TestBrand", []))


# ── Bölüm A4: çıktı koruması (meta/analiz sızıntısı) — deterministik, API'siz ──
# "Bana taslak yerine analiz geliyor" hatasının regresyon kalkanı.
def part_a4():
    print("\n== Bölüm A4: çıktı koruması (e-posta mı, analiz mi) ==")
    # İmza adı, templates'in fallback varsayılanıyla AYNI olmalı (ENV boşken de imza eşleşsin):
    #  - teklif fallback imzası: config.MANAGER_NAME or "Partnerships Manager"
    #  - tanıştırma imzası: config.SENDER_NAME or ("Ben"/"Me")
    SIGN = (config.MANAGER_NAME or "Partnerships Manager",)
    SIGN_SENDER_TR = (config.SENDER_NAME or "Ben",)
    SIGN_SENDER_EN = (config.SENDER_NAME or "Me",)
    # A) Gerçek sızıntı şekli (imzasız/selamsız analiz) -> REDDET
    leak = (
        "Bu diğerlerinden tamamen farklı bir teklif türü. Burada bir marka içerik üreticisini "
        "işbirliğine davet etmiyor.\n\n"
        "Özet:\n"
        "Bu bir marka iş birliği teklifi DEĞİL. Bu yüzden bu maile portföy + fiyat "
        "taslağı uygulamadım.\n\n"
        "Önerim: Bu maile hemen taahhüt içeren bir yanıt vermeyin.\n"
        "Nasıl ilerleyelim, ilgi varsa taahhütsüz bir bilgi-toplama taslağı yazayım?"
    )
    check("koruma: analiz metnini REDDediyor", not llm.looks_like_outbound_email(leak, SIGN))

    # B) Gerçek teklif fallback'i KABUL (şablon kendini elemesin -> except dalı patlamasın)
    for lang in ("tr", "en"):
        fb = T.offer_fallback(lang, "TestBrand", [])
        check(f"koruma: offer_fallback geçerli e-posta ({lang})",
              llm.looks_like_outbound_email(fb, SIGN))

    # C) Gerçek tanıştırma KABUL
    check("koruma: intro_body geçerli (tr/Aylin)",
          llm.looks_like_outbound_email(T.intro_body("tr", "Aylin"), SIGN_SENDER_TR))
    check("koruma: intro_body geçerli (en/nötr)",
          llm.looks_like_outbound_email(T.intro_body("en", None), SIGN_SENDER_EN))

    # D) Yanlış-pozitif kalkanı: meşru numaralı 'menü' teklifi KABUL edilmeli
    mgr = config.MANAGER_NAME or "Partnerships Manager"
    menu = (
        "Merhaba,\n\n"
        f"Ben {mgr}, Partnerships Manager'ım; süreci buradan ben yürüteceğim.\n\n"
        "Size birkaç seçenek sunayım:\n"
        f"(1) kısa video paketi {config.PRICE_SHORT}\n"
        f"(2) YouTube dedicated uzun video {config.PRICE_LONG}\n"
        f"(3) ikisi birlikte {config.PRICE_BUNDLE}\n\n"
        "Hangisi size uygun olur? Öncelikli platform ve hedef tarihi paylaşır mısınız?\n\n"
        f"Sevgiler,\n{mgr}"
    )
    check("koruma: numaralı 'menü' teklifi KABUL (FP yok)",
          llm.looks_like_outbound_email(menu, SIGN))

    # E) Sınır durumlar -> REDDET
    check("koruma: çok kısa -> reddet", not llm.looks_like_outbound_email("ok", SIGN))
    check("koruma: imzasız selam-only -> reddet",
          not llm.looks_like_outbound_email("Merhaba,\n\nTeşekkürler, en kısa sürede size döneriz efendim.", SIGN))
    check("koruma: selamsız 'Özet:' -> reddet",
          not llm.looks_like_outbound_email(f"Özet: bu mail bir bülten.\nSevgiler, {mgr}", SIGN))

    # F) SARMALI analiz (sahte selam+imza) -> yine REDDET (fold + operatör-marker kalkanı)
    wrapped_ascii = f"Merhaba,\n\nBu maili inceledim, bence bir is birligi degil. Nasil ilerleyelim?\n\nSevgiler,\n{mgr}"
    check("koruma: sarmalı ASCII-marker (Nasil) reddet", not llm.looks_like_outbound_email(wrapped_ascii, SIGN))
    wrapped_op = f"Merhaba,\n\nBence bu marka bizimle pek uyumlu degil. Sence ne yapalim?\n\nSevgiler,\n{mgr}"
    check("koruma: sarmalı operatör-soru (ne yapalim) reddet", not llm.looks_like_outbound_email(wrapped_op, SIGN))


# ── Bölüm A5: marka-yüzü servis düzeltmeleri (deterministik, API'siz) ──
def part_a5():
    print("\n== Bölüm A5: marka-yüzü servis düzeltmeleri ==")
    from services import notion_portfolio as NP, brand_web as BW, gmail_ops as G
    from email.utils import getaddresses
    import base64 as _b64, email as _email

    # _fmt_views: ASLA yukarı yuvarlamaz (markaya şişirilmiş izlenme gitmesin)
    check("_fmt_views 1501 -> 1K (şişmez)", NP._fmt_views(1501, "en") == "1K views", NP._fmt_views(1501, "en"))
    check("_fmt_views 1999 -> 1K", NP._fmt_views(1999, "tr") == "1K izlenme", NP._fmt_views(1999, "tr"))
    check("_fmt_views 999600 -> 999K (1000K değil)", NP._fmt_views(999600, "en") == "999K views", NP._fmt_views(999600, "en"))
    check("_fmt_views 1290000 -> 1.2M (şişmez)", NP._fmt_views(1290000, "en") == "1.2M views", NP._fmt_views(1290000, "en"))
    check("_fmt_views 0 -> boş", NP._fmt_views(0, "en") == "")

    # _domain: lstrip karakter-kümesi bug'ı yok
    check("_domain wattpad korunur", BW._domain("https://wattpad.com/x") == "wattpad.com", BW._domain("https://wattpad.com/x"))
    check("_domain wise korunur", BW._domain("https://wise.com") == "wise.com", BW._domain("https://wise.com"))
    check("_domain www. soyulur", BW._domain("https://www.acme.com") == "acme.com", BW._domain("https://www.acme.com"))

    # _norm_platform: select(string) -> liste (['Instagram'][0]='I' bug'ı yok)
    check("_norm_platform string->liste", NP._norm_platform("Instagram") == ["Instagram"])
    check("_norm_platform liste korunur", NP._norm_platform(["YouTube", "Instagram"]) == ["YouTube", "Instagram"])
    check("_norm_platform None->[]", NP._norm_platform(None) == [])

    # offer_fallback: boş alanlı referans -> 'None' / boş '()' / sarkan '- :' YOK
    bad_refs = [{"brand": "Nim", "topic": "", "url": "https://x.com/p", "views_label": ""},
                {"brand": "", "category": "", "topic": "", "url": "https://y.com/q", "views_label": "1M views"}]
    fb = T.offer_fallback("en", "TestBrand", bad_refs)
    check("offer_fallback 'None' yok", "None" not in fb, fb[:200])
    check("offer_fallback boş '()' yok", "()" not in fb)
    check("offer_fallback sarkan '- :' yok", "- :" not in fb and "-  :" not in fb)
    check("offer_fallback URL'ler korunur", "https://x.com/p" in fb and "https://y.com/q" in fb)

    # build_raw: From display adı Türkçe olsa da adres ÇÖZÜLEBİLİR kalmalı
    raw = G.build_raw("Ada Lovelace <you@yourdomain.com>", "brand@x.com", "Re: İş Birliği", "Merhaba, gövde.")
    m = _email.message_from_bytes(_b64.urlsafe_b64decode(raw))
    parsed = getaddresses([m["From"]])
    check("build_raw From adresi çözülüyor", bool(parsed) and parsed[0][1] == "you@yourdomain.com", str(parsed))

    # _b64d: padding'siz veri patlamadan çözülür (sessiz thread düşmesi yok)
    nopad = _b64.urlsafe_b64encode("Merhaba dunya test".encode()).decode().rstrip("=")
    try:
        check("_b64d padding'siz veriyi çözer", G._b64d(nopad) == "Merhaba dunya test")
    except Exception as e:
        check("_b64d padding'siz veriyi çözer", False, str(e))


# ── Bölüm A6: selamlama/isim/HTML sağlamlığı (deterministik, API'siz) ──
# "markalara yanlış isimle hitap (BÜYÜK-HARF ad / uydurma / düşen-Bey)" + "normal mail gibi görünmüyor"
# (text/plain-only) hatalarının regresyon kalkanı.
def part_a6():
    print("\n== Bölüm A6: selamlama + isim + HTML sağlamlığı ==")
    import email as _email
    from email.utils import getaddresses
    SIGN = (config.MANAGER_NAME or "Partnerships Manager",)

    # first_name_from: büyük-harf normalize, compound, yabancı, ayraç-kurtarma, marka-sızıntısı kalkanı
    cases = {
        '"ZEYNEP AKSU" <z@x.com>': "Zeynep",            # büyük-harf From -> Title-case
        "MEHMET-ALI YILDIZ <m@x.com>": "Mehmet-Ali",     # compound, yabancı I noktalı
        "D'ANGELO RUSSELL <d@x.com>": "D'Angelo",        # apostrof
        "WILLIAM SMITH <w@x.com>": "William",            # yabancı BÜYÜK-HARF (Wıllıam DEĞİL)
        "IŞIL KIVANÇ <i@x.com>": "Işıl",                 # Türkçe-harfli korunur
        "Best Of The Best - Yasin Ocak <y@x.com>": "Yasin",   # ayraçlı kişi kurtarma
        "SlashAgency | Ahmet Kaya <a@x.com>": "Ahmet",        # 'Ad Soyad' segment -> kişi
        "Murat Bey | TechCorp <x@y.com>": "Murat",            # honorific = kişi sinyali (marka sızmaz)
        "Ahmet Demir - Mehmet Kaya <a@x.com>": None,          # iki kişi -> belirsiz -> None
        '"Bey" <b@x.com>': None,                              # honorific tek başına ad değil
        '"Sales Team" <s@x.com>': None,                       # rol -> None (kalkan korunur)
    }
    for hdr_v, exp in cases.items():
        got = T.first_name_from(hdr_v)
        check(f"first_name_from {hdr_v[:28]} -> {exp!r}", got == exp, f"got {got!r}")

    # enforce_greeting: deterministik selam AMA içerik ASLA silinmez
    g = llm.enforce_greeting("Merhaba ZEYNEP Hanım,\n\nTeşekkürler.\n\nSevgiler,\nTest", "tr", "Zeynep")
    check("enforce: ZEYNEP -> Zeynep (büyük-harf gider)", g.split("\n")[0].startswith("Merhaba Zeynep") and "ZEYNEP" not in g)
    g = llm.enforce_greeting("Merhaba Best,\n\nBen test.\n\nSevgiler,\nTest", "tr", None)
    check("enforce: uydurma 'Best' -> nötr 'Merhaba,'", g.split("\n")[0] == "Merhaba," and "Best," not in g)
    g = llm.enforce_greeting("Merhaba Ahmet,\n\nTeklifiniz ilgimi çekti.\n\nSevgiler,\nTest", "tr", "Ahmet")
    check("enforce: düşen honorific eklenir (Ahmet Bey)", g.split("\n")[0].startswith("Merhaba Ahmet Bey"))
    # içerik koruma
    g = llm.enforce_greeting("Hi-tech tools are exciting, and we love them.\n\nBest,\nTest", "en", "Sarah")
    check("enforce: 'Hi-tech...' parçalanmaz", "Hi-tech tools are exciting, and we love them." in g and g.split("\n")[0] == "Hi Sarah,")
    g = llm.enforce_greeting("Hello and thank you so much for reaching out about this.\n\nI'm here.\n\nBest,\nTest", "en", "Sarah")
    check("enforce: virgülsüz 'Hello and thank you...' korunur", "thank you so much for reaching out" in g)
    g = llm.enforce_greeting("Değerli vaktinizi ayırdığınız için teşekkür ederiz, başlayalım.\n\nBen test.\n\nSevgiler,\nTest", "tr", "Ahmet")
    check("enforce: 'Değerli vaktinizi...,' korunur", "Değerli vaktinizi ayırdığınız için teşekkür ederiz" in g)
    g = llm.enforce_greeting("Memnun oldum Mehmet Bey,\n\nteklifinizi değerlendirdik.\n\nSevgiler,\nTest", "tr", "Ali")
    check("enforce: 'Memnun oldum Mehmet Bey,' içerik korunur", "Memnun oldum Mehmet Bey," in g)

    # build_raw: multipart/alternative + HTML link güvenliği
    body = ("Merhaba Ahmet Bey,\n\nLinkler: https://instagram.com/reel/x.\n\nSevgiler,\nAda Lovelace\n\n"
            "15 Jun 2026 tarihinde Ahmet <a@x.com> yazdı:\n> site <https://brand.co/x>.\n>> eski")
    raw = G.build_raw("Ada Lovelace <you@yourdomain.com>", "a@x.com", "Re: İş Birliği", body, cc_h="manager@yourdomain.com")
    m = _email.message_from_bytes(__import__("base64").urlsafe_b64decode(raw))
    types = [p.get_content_type() for p in m.walk()]
    check("build_raw multipart/alternative", m.get_content_type() == "multipart/alternative" and "text/html" in types and "text/plain" in types, str(types))
    html = [p for p in m.walk() if p.get_content_type() == "text/html"][0].get_payload(decode=True).decode("utf-8")
    check("HTML <blockquote> (alıntı normal görünür)", "<blockquote" in html)
    check("HTML URL sonu noktası href dışı", 'href="https://instagram.com/reel/x"' in html)
    check("HTML '<url>' &gt; sızmaz", 'href="https://brand.co/x"' in html)
    check("HTML XSS-güvenli (escape korunur)", "<script" not in html)
    check("From adresi çözülüyor (multipart)", getaddresses([m["From"]])[0][1] == "you@yourdomain.com")
    g = llm.enforce_greeting(T.offer_fallback("tr", "TestBrand", []), "tr", None)
    check("offer_fallback+enforce hâlâ geçerli e-posta", llm.looks_like_outbound_email(g, SIGN))


# ── Bölüm B: referans + yazım ─────────────────────────────
def part_b():
    print("\n== Bölüm B: referans seçimi + yönetici yazımı ==")
    refs = NP.select_references("AI Video", lang="en", n=3)
    if not refs:
        print("  (portföy boş/yapılandırılmamış — referans testleri atlandı)")
    else:
        check("referanslar gerçek URL", all(r["url"].startswith("http") for r in refs))

    offer = llm.write_offer("en", "PixelFlow AI", "AI short-form video tool",
                            "paid dedicated short-form across Reels/Shorts/TikTok", "new", refs)
    sign = config.MANAGER_NAME or ""
    if sign:
        check("EN teklif yönetici imzalı", sign in offer)
    check("EN teklif fiyat içeriyor", any(p in offer for p in (config.PRICE_SHORT, config.PRICE_LONG, config.PRICE_BUNDLE)))
    if refs:
        check("EN teklif seçili referansı gömdü", any(r["url"] in offer for r in refs))
    check("EN teklifte em-dash yok", "—" not in offer, "em-dash bulundu")

    refs_tr = NP.select_references("Vibe Coding", lang="tr", n=3)
    offer_tr = llm.write_offer("tr", "KodlaAI", "AI vibe coding aracı",
                               "Instagram Reels ücretli iş birliği", "new", refs_tr)
    if sign:
        check("TR teklif yönetici imzalı", sign in offer_tr)
    check("TR teklif Türkçe kapanış", ("Sevgiler" in offer_tr or "teşekkür" in offer_tr.lower()))
    print("\n  --- ÖRNEK EN TEKLİF (ilk 600 karakter) ---")
    print("  " + offer[:600].replace("\n", "\n  "))


# ── Bölüm C: canlı mekanik (--live) ───────────────────────
def part_c():
    print("\n== Bölüm C: canlı mekanik (marka -> tanıştırma -> yönetici taslağı) ==")
    BRAND = config.ADDR["inbox_personal"]   # marka rolünü oynayan kutu (kendi ikinci hesabın)
    SENDER = config.ADDR["inbox_primary"]
    MGR = config.ADDR["manager"]
    if not (BRAND and SENDER and MGR):
        print("  (config.ADDR eksik — canlı test atlandı)")
        return
    subj = "Paid Collaboration Opportunity with Lumina AI [Test 2]"
    brand_body = ("Hi there, I'm Aylin from Lumina AI, an AI tool that turns prompts into short "
                  "videos. We'd love a paid dedicated short-form video across your platforms. "
                  "Could you share your rates?\n\nBest, Aylin\n\n(Otomasyon testi.)")
    raw1 = G.build_raw(f"Aylin (Lumina AI) <{BRAND}>", SENDER, subj, brand_body)
    s1 = G.send("inbox_personal", raw1)
    mid1 = G.rfc822_msgid("inbox_personal", s1["id"])
    print(f"  marka maili gönderildi mid={mid1}")
    r1 = G.find_by_rfc822("inbox_primary", mid1)
    check("marka maili birincil kutuya düştü", bool(r1))
    if not r1:
        return
    tid_dol = r1["threadId"]

    # tanıştırma (gönderen -> marka, cc yönetici), threaded
    body2 = T.intro_body("en", "Aylin")
    raw2 = G.build_raw(G.display_from("inbox_primary", config.SENDER_NAME), BRAND, "Re: " + subj,
                       body2, cc_h=MGR, in_reply_to=mid1, references=mid1)
    s2 = G.send("inbox_primary", raw2, thread_id=tid_dol)
    mid2 = G.rfc822_msgid("inbox_primary", s2["id"])
    r2 = G.find_by_rfc822("manager", mid2)
    check("tanıştırma yönetici kutusuna CC ile düştü", bool(r2))
    if not r2:
        return
    tid_cer = r2["threadId"]

    # Yönetici teklif taslağı (reply-all: To marka, CC gönderen)
    refs = NP.select_references("AI Video", lang="en", n=3)
    offer = llm.write_offer("en", "Lumina AI", "AI short-form video tool",
                            "paid dedicated short-form across platforms", "new", refs)
    raw3 = G.build_raw(G.display_from("manager", config.MANAGER_NAME), BRAND, "Re: " + subj, offer,
                       cc_h=SENDER, in_reply_to=mid2, references=f"{mid1} {mid2}")
    draft = G.create_draft("manager", raw3, thread_id=tid_cer)
    d = G.service("manager").users().drafts().get(userId="me", id=draft["id"], format="metadata").execute()
    m = d["message"]
    check("taslak doğru thread'te", m["threadId"] == tid_cer)
    check("taslak To = marka", BRAND in G.hdr(m, "To"))
    check("taslak CC = gönderen", SENDER in G.hdr(m, "Cc"))
    print(f"  yönetici teklif taslağı hazır (draft id={draft['id']})")


if __name__ == "__main__":
    part_a2()      # API gerektirmez — her zaman çalışır
    part_a3()      # API gerektirmez — hitap/blocklist/fallback deterministik kontroller
    part_a4()      # API gerektirmez — çıktı koruması (meta/analiz sızıntısı)
    part_a5()      # API gerektirmez — marka-yüzü servis düzeltmeleri (views/domain/From/b64/fallback)
    part_a6()      # API gerektirmez — selamlama/isim/HTML sağlamlığı
    part_a()       # LLM çağrısı yapar (OPENAI_API_KEY* gerekir)
    part_b()       # LLM çağrısı yapar
    if "--live" in sys.argv:
        part_c()   # gerçek Gmail hesapları arasında mail gönderir (config.ADDR dolu olmalı)
    print(f"\n==== SONUÇ: {len(PASS)} PASS / {len(FAIL)} FAIL ====")
    if FAIL:
        print("FAIL:", ", ".join(FAIL))
        sys.exit(1)
