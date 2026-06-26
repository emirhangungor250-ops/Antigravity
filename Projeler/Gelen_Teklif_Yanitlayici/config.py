# -*- coding: utf-8 -*-
"""Merkezi konfigürasyon — gelen iş birliği / teklif maili yanıt otomasyonu.

Tüm kişiye-özel değerler (e-posta adresleri, ekip üyesi adı, portföy DB'si,
fiyatlar) ENV değişkeninden okunur. `.env.example`'ı `.env` olarak kopyalayıp
doldur (Railway'de aynı isimlerle servis env'ine geçir).

Roller:
- GÖNDEREN (sender)  = otomasyonun adına çalıştığı içerik üreticisi / freelancer.
                       Markaya ilk "köprü" tanıştırma mailini onun ağzından atar.
- YÖNETİCİ (manager) = teklif/fiyat görüşmesini yürüten ekip üyesi (Partnerships
                       Manager). Teklif taslakları onun ağzından ve onun kutusunda
                       hazırlanır; ASLA otomatik gönderilmez.
Tek kişiysen GÖNDEREN ile YÖNETİCİ aynı isim/e-posta olabilir.
"""
import os
import re


def load_env():
    """Aynı klasördeki `.env` varsa os.environ'a yükle (mevcut değerleri EZME).

    Lokal geliştirmede kolaylık; Railway/production'da env var'lar zaten set'tir
    ve onlar kazanır (setdefault). Bağımlılık eklememek için elle parse edilir.
    """
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    if os.path.exists(env_path):
        for line in open(env_path, encoding="utf-8"):
            line = line.strip()
            if "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())


load_env()

# ── Hesaplar ──────────────────────────────────────────────
# Gelen ilk temas iki kutuya birden düşebilir (markalar genelde önce kişisel
# kutuya yazar); ikisi de taranır. Tek kutun varsa aynı değeri iki kez verebilir
# ya da listeyi tek elemana indirebilirsin.
INBOUND_ACCOUNTS = ["inbox_primary", "inbox_personal"]   # gönderenin tarayacağı kutular
MANAGER_ACCOUNT = "manager"                              # teklif taslağı buraya düşer

# Her hesap anahtarının gerçek e-posta adresi (ENV'den).
ADDR = {
    "inbox_primary": os.environ.get("SENDER_PRIMARY_EMAIL", ""),    # ör. you@yourdomain.com
    "inbox_personal": os.environ.get("SENDER_PERSONAL_EMAIL", ""),  # ör. you@gmail.com
    "manager": os.environ.get("MANAGER_EMAIL", ""),                 # ör. manager@yourdomain.com
}
# "Bizim taraf" = counterparty çıkarımında dış marka SAYILMAYAN adresler.
# ENV: INTERNAL_ADDRESSES="you@domain.com,manager@domain.com,@domain.com" (virgüllü).
# Boşsa ADDR'deki üç adres + onların domaini kullanılır.
_internal_env = os.environ.get("INTERNAL_ADDRESSES", "")
if _internal_env.strip():
    INTERNAL_ADDRESSES = tuple(x.strip().lower() for x in _internal_env.split(",") if x.strip())
else:
    _addrs = [a for a in ADDR.values() if a]
    _domains = ["@" + a.split("@", 1)[1] for a in _addrs if "@" in a]
    INTERNAL_ADDRESSES = tuple(dict.fromkeys([a.lower() for a in _addrs] + [d.lower() for d in _domains]))

# Gönderen + yönetici görünen adları (mail "From" display + imza için).
SENDER_NAME = os.environ.get("SENDER_NAME", "")     # ör. "Ada Lovelace" — markaya görünen ad
MANAGER_NAME = os.environ.get("MANAGER_NAME", "")   # ör. "Maya" — teklif imzası

# ── Tarama ────────────────────────────────────────────────
SCAN_WINDOW_DAYS = int(os.environ.get("SCAN_DAYS", "7"))
MAX_THREADS_PER_RUN = int(os.environ.get("MAX_THREADS", "25"))

# ── Teklif draft varyantları ──────────────────────────────
# Yöneticiye tek teklif yerine N ayrı hazır draft bırakılır:
# odaklı / paket(bundle) / menü. Yönetici en uygununu seçip gönderir, gerisini siler.
# 1 -> tek-draft davranışı. Sıra: [odaklı, paket, menü].
OFFER_VARIANTS = max(1, min(3, int(os.environ.get("OFFER_VARIANTS", "3"))))
# Fiyatlar ENV'den (kendi rate card'ına göre). Para birimi sembolünü kendin yaz.
PRICE_SHORT = os.environ.get("PRICE_SHORT", "$800")        # kısa-form video paketi
PRICE_LONG = os.environ.get("PRICE_LONG", "$2000")        # uzun-form (YouTube) video
PRICE_BUNDLE = os.environ.get("PRICE_BUNDLE", "$2500")    # paket (kısa + uzun birlikte)
# Geriye dönük uyum: eski isim BUNDLE_PRICE hâlâ çalışsın.
BUNDLE_PRICE = PRICE_BUNDLE

# ── Gmail etiketleri (idempotency + görünürlük) ───────────
# İstersen ENV LABEL_PREFIX ile değiştir (varsayılan "Inbound").
_LP = os.environ.get("LABEL_PREFIX", "Inbound")
LBL_HANDLED = f"{_LP}/Islendi"            # inbound kutuda işlenmiş thread
LBL_AUTO_INTRO = f"{_LP}/OtoTanistirildi" # tanıştırma otomatik gönderildi
LBL_DRAFT_INTRO = f"{_LP}/TanistirmaTaslagi"  # tanıştırma taslak (gönderen onaylasın)
LBL_SKIPPED = f"{_LP}/IsbirligiDegil"     # collab değil, atlandı
LBL_OFFER_READY = f"{_LP}/TeklifHazir"    # yönetici teklif taslağı oluşturuldu

# ── LLM ───────────────────────────────────────────────────
# Yönlendirme (services/llm.py): model adında "/" VARSA -> OpenRouter; YOKSA -> OpenAI direkt.
# Varsayılan üç iş de gpt-4.1-mini @ OpenAI direkt. OpenAI'da "data sharing" açıksa mini
# tier günlük belli bir token'a kadar ÜCRETSİZdir (bedava krediden faydalanmak için
# OpenRouter değil direkt çağrı şart). Detay: OpenAI hesabının kullanım ayarları.
# OpenRouter yalnızca env ile "/"-li bir model verilirse devreye girer (opsiyonel).
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENAI_DIRECT_URL = "https://api.openai.com/v1/chat/completions"
# Bedava data-shared anahtar (mini tier). Yoksa normal OPENAI_API_KEY'e düş (ücretli ama çalışır).
OPENAI_DIRECT_KEY = os.environ.get("OPENAI_API_KEY_DATA_SHARED", "") or os.environ.get("OPENAI_API_KEY", "")

QUALIFY_MODEL = os.environ.get("QUALIFY_MODEL", "gpt-4.1-mini")  # bare -> OpenAI direkt
WRITER_MODEL = os.environ.get("WRITER_MODEL", "gpt-4.1-mini")    # bare -> OpenAI direkt
INTRO_MODEL = os.environ.get("INTRO_MODEL", "gpt-4.1-mini")      # bare -> OpenAI direkt

# ── Notion referans portföyü (OPSİYONEL) ──────────────────
# Teklif maillerine eklenecek geçmiş iş örnekleri (referanslar) bu Notion DB'sinden
# okunur. Kullanmak istemezsen NOTION_PORTFOLIO_DB_ID'yi boş bırak -> teklif referanssız
# çıkar (yine çalışır). DB şeması services/notion_portfolio.py başında anlatılır.
PORTFOLIO_DB_ID = os.environ.get("NOTION_PORTFOLIO_DB_ID", "")
NOTION_TOKEN_CANDIDATES = [
    os.environ.get("NOTION_TOKEN", ""),
    os.environ.get("NOTION_TOKEN_2", ""),
]
# Portföy DB'sindeki "Kategori" alanının olası değerleri (kendi nişine göre düzenle).
# QUALIFY LLM gelen markayı bu kategorilerden birine eşler -> uygun referans seçilir.
PORTFOLIO_CATEGORIES = [c.strip() for c in os.environ.get(
    "PORTFOLIO_CATEGORIES",
    "AI Video, AI Yazı, AI Avatar, AI Asistan, E-ticaret, AI Görsel, "
    "Kariyer, Müzik, AI Genel, Vibe Coding, AI Reklam",
).split(",") if c.strip()]

# ── İş birliği KAPSAMI (niche_fit kararının dayanağı) ──────
# Gönderenin kitlesine UYGUN markalar otomatik karşılanır; kitleyle alakasızlar taslak
# bırakılır. Kapsamı KENDİ nişine göre ENV ile değiştir (SCOPE_NOTE), ya da aşağıdaki
# varsayılanı düzenle. ÖRNEK kapsam (tech/dijital içerik üreticisi); kendi sektörüne uyarla.
SCOPE_NOTE = os.environ.get("SCOPE_NOTE", """KAPSAM İÇİ (in_scope — oto-cevap uygun):
- AI / yazılım / SaaS / uygulama / geliştirici aracı
- Tüketici elektroniği & gadget (telefon, kulaklık, dashcam, robot süpürge, powerbank, laptop/gaming, TV)
- E-ticaret / pazaryeri / dropshipping / kargo-lojistik araçları
- Fintech / finans / ödeme / yatırım / banka
- Seyahat / bağlanabilirlik / eSIM
- Elektronik perakende ve genel dijital servis / online platform / abonelik
KAPSAM DIŞI (off_scope — oto-cevap YOK, taslak bırak; kitleyle GERÇEKTEN alakasız):
- Gıda takviyesi / diyet / sağlık ürünü; moda / giyim; kozmetik / kişisel bakım; mobilya / dekor;
  yerel hizmet (diş hekimi, restoran, emlak); kumar / bahis, yetişkin, MLM / şüpheli
Emin değilsen in_scope (otomasyonu gereksiz durdurma). Markanın ne yaptığına SİTE/METİN'den bak; adından tahmin etme.""")

# ── Görmezden gelinecek gönderenler (kalıcı kara liste) ───
# Burada eşleşen thread'ler otomasyon tarafından TAMAMEN atlanır: ne tanıştırma,
# ne teklif taslağı. Gönderen adresi + display header'a (sınır-farkında) bakılır.
# Israrcı bir aracı ajansı varsa domain'iyle bloklarsın; markası değişse de yakalanır.
# ENV ile doldur/genişlet: SENDER_BLOCKLIST="domain1.com,bir-ajans" (virgüllü).
SENDER_BLOCKLIST = []
_extra_block = os.environ.get("SENDER_BLOCKLIST", "")
if _extra_block.strip():
    SENDER_BLOCKLIST += [x.strip().lower() for x in _extra_block.split(",") if x.strip()]


def _label_blocks(label, b):
    """Bir domain etiketi (ör. 'someagency-vision') kara-liste token'ı b ile SINIR-FARKINDA eşleşir mi?
    Tam eşit / 'b-' ile başlar / '-b' ile biter / '-b-' ortada. Bitişik türevleri (ör. 'someagencys')
    ELEMEZ (yanlış-pozitif yemez)."""
    return (label == b or label.startswith(b + "-")
            or label.endswith("-" + b) or ("-" + b + "-") in ("-" + label + "-"))


def is_blocked_sender(*texts):
    """texts (gönderen adresi, display header) kara listeyle SINIR-FARKINDA eşleşirse True.
    Düz substring DEĞİL: 'foo.com' yalnız domain == foo.com / *.foo.com; 'fooagency' yalnız bir
    domain etiketi ya da serbest metin token'ı olarak. Böylece bitişik yanlış-pozitifler elenir
    AMA ajansın rotasyon domainleri yakalanmaya devam eder. LLM çağrısından ÖNCE kullanılır."""
    blob = " ".join(t for t in texts if t).lower()
    domains = re.findall(r'@([a-z0-9.\-]+)', blob)
    for b in SENDER_BLOCKLIST:
        b = (b or "").strip().lower()
        if not b:
            continue
        if "." in b:                       # tam / alt-domain eşleşmesi
            if any(d == b or d.endswith("." + b) for d in domains):
                return True
        else:                              # domain etiketi VEYA serbest metin token'ı (sınır-farkında)
            if any(_label_blocks(lbl, b) for d in domains for lbl in d.split(".")):
                return True
            if re.search(r'(?<![a-z0-9])' + re.escape(b) + r'(?![a-z0-9])', blob):
                return True
    return False


# ── Güvenlik anahtarı: canlı gönderimi tamamen kapatma ────
# DRY_RUN=1 -> hiç mail göndermez/taslak yazmaz, sadece ne yapacağını loglar.
DRY_RUN = os.environ.get("DRY_RUN", "0") == "1"
# AUTO_SEND_INTRO=0 -> "emin" durumda bile otomatik göndermez, taslak bırakır (acil fren).
AUTO_SEND_INTRO = os.environ.get("AUTO_SEND_INTRO", "1") == "1"
