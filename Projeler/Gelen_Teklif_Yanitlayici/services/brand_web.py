# -*- coding: utf-8 -*-
"""Marka website özeti — niteleme/yazımı GERÇEKLE temellendirir.

İnsan manuel çalışırken markanın sitesine bakıp ne yaptığını öğrenir. Bot e-postadan
markanın ne yaptığını çıkaramayınca UYDURABİLİR (ör. adı "video" çağrıştıran bir markayı
yanlışlıkla "video aracı" sanmak). Burada thread'deki marka URL'lerini + gönderen domainini
bulup <title> + meta description çekeriz; bu özet qualify'a verilir. Best-effort: her hata
sessizce "" döndürür, pipeline ASLA patlamaz.
"""
import os
import re
import json
import html as _html
import requests

import config  # config.py .env'i os.environ'a yükler (FIRECRAWL_API_KEY lokalde gelsin)

# Bizim KENDİ domainlerimiz marka sitesi değildir -> dışla. config.INTERNAL_ADDRESSES'teki
# "@domain" girdilerinden türet (ör. "@yourdomain.com" -> "yourdomain.com"). Tam e-posta
# adreslerini (you@...) DEĞİL, yalnız domain girdilerini al. Böylece kişisel domain gömülü değil.
_OWN_HOSTS = tuple(a[1:] for a in config.INTERNAL_ADDRESSES if a.startswith("@") and "." in a)

# Marka olmayan / gürültü hostlar (aracı/araç/doküman/sosyal/freemail/relay)
_EXCLUDE = (
    "google.", "gstatic", "googleusercontent", "googleapis", "docs.google", "drive.google",
    "streaklinks", "feishu", "larksuite", "notion.site", "notion.so", "calendly",
    "youtube.", "youtu.be", "instagram.", "tiktok.", "facebook.", "fb.com", "fb.me",
    "linkedin.", "twitter.", "x.com", "t.co", "we.tl", "wetransfer", "payoneer",
    "lovable.app", "loom.com", "vimeo.", "bit.ly", "tinyurl", "mailchi",
    "gmail.com", "outlook.", "yahoo.", "hotmail.",
    "proton.me", "protonmail", "qq.com", "163.com", "icloud.com",
    "list-preferences", "unsubscribe", "click.", "email.", "links.", "track.",
) + _OWN_HOSTS
# Gönderen domaini relay/freemail görünüyorsa marka sitesi değildir (best-effort)
_RELAY_HINT = ("mail", "msg", "send", "influx", "offer", "campaign", "partner", "invite",
               "flux", "-biz", "biz.", "tec-do", "relay", "inbox", "notify", "noreply",
               "mktg", "outreach", "media.", "agency", "group")

_URL_RE = re.compile(r'https?://[^\s<>"\')\]]+', re.I)
_EMAIL_DOMAIN_RE = re.compile(r'[\w.\-+]+@([\w.\-]+\.[A-Za-z]{2,})')
_CACHE = {}

# Firecrawl: rendered (JS dahil) sayfa içeriği -> markanın ne yaptığını ham title/meta'dan
# çok daha iyi temellendirir (markayı adından yanlış tahmin etme hatasını kapatır). Anahtar
# yoksa veya hata olursa sessizce ham fetch'e düşülür; pipeline ASLA patlamaz.
_FIRECRAWL_URL = "https://api.firecrawl.dev/v1/scrape"


def _clean_md(md):
    """Firecrawl markdown -> düz kısa metin: görsel/link sözdizimi ve md gürültüsü temizlenir."""
    md = re.sub(r"!\[[^\]]*\]\([^)]*\)", " ", md)        # görseller
    md = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", md)      # linkler -> sadece metin
    md = re.sub(r"https?://\S+", " ", md)                 # çıplak URL
    md = re.sub(r"[#>*_`|]+", " ", md)                    # md işaretleri
    return re.sub(r"\s+", " ", md).strip()


def _firecrawl_one(url):
    """Firecrawl ile rendered sayfa -> 'domain: başlık — açıklama — ana içerik' özeti.
    Anahtar yok / hata / boş -> "" (çağıran ham fetch'e düşer)."""
    key = os.environ.get("FIRECRAWL_API_KEY", "")   # çağrı anında oku (import sırası + Railway env'e dayanıklı)
    if not key:
        return ""
    try:
        r = requests.post(
            _FIRECRAWL_URL,
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            data=json.dumps({"url": url, "formats": ["markdown"],
                             "onlyMainContent": True, "timeout": 20000}),
            timeout=28,
        )
        if r.status_code != 200:
            return ""
        data = (r.json() or {}).get("data") or {}
        meta = data.get("metadata") or {}
        title = (meta.get("title") or "").strip()
        desc = (meta.get("description") or meta.get("ogDescription") or "").strip()
        parts = [p for p in (title, desc) if p]
        # başlık+açıklama zayıfsa ana içerikten kısa bir parça ekle (ne yaptığını anlamak için)
        body = _clean_md(data.get("markdown") or "")
        if len(" ".join(parts)) < 80 and body:
            parts.append(body[:300])
        if not parts:
            return ""
        out = f"{_domain(url)}: " + " — ".join(parts)
        return re.sub(r"\s+", " ", out)[:600]
    except Exception:
        return ""


def _fetch_summary(url):
    """Önce Firecrawl (zengin/rendered), olmazsa ham title+meta. İkisi de best-effort."""
    return _firecrawl_one(url) or _fetch_one(url)


def _domain(url):
    m = re.match(r'https?://([^/]+)', url, re.I)
    host = (m.group(1) if m else url).lower()
    # lstrip("www.") KARAKTER KÜMESİ siler (wattpad.com->attpad.com, wise.com->ise.com!) -> prefix sil.
    return re.sub(r'^www\.', '', host)


def _is_brandish(url):
    u = url.lower()
    if any(x in u for x in _EXCLUDE):
        return False
    # görsel/asset uzantısı
    if re.search(r'\.(png|jpe?g|gif|svg|webp|pdf|mp4|zip|css|js)(\?|$)', u):
        return False
    return True


def _candidate_urls(thread_text, max_n=2):
    """Thread'deki marka URL'leri + gönderen email domaini -> aday kök URL listesi."""
    cands, seen = [], set()

    def add(url):
        d = _domain(url)
        if not d or d in seen:
            return
        seen.add(d)
        cands.append(f"https://{d}/")

    # 1) gövdedeki açık URL'ler (marka linkleri öncelik)
    for u in _URL_RE.findall(thread_text or ""):
        if _is_brandish(u):
            add(u)
    # 2) gönderen email domaini (markanın kendi domaininden direkt yazdığı durum)
    for dom in _EMAIL_DOMAIN_RE.findall(thread_text or ""):
        dl = dom.lower()
        if any(x in dl for x in _EXCLUDE):
            continue
        if any(h in dl for h in _RELAY_HINT):   # relay/freemail -> atla
            continue
        if dl not in seen:
            seen.add(dl)
            cands.append(f"https://{dl}/")
    return cands[:max_n]


def _fetch_one(url):
    try:
        r = requests.get(url, timeout=8, allow_redirects=True, headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
            "Accept-Language": "en;q=0.9",
        })
        if r.status_code != 200 or not r.text:
            return ""
        t = r.text[:200000]

        def grab(pat):
            m = re.search(pat, t, re.I | re.S)
            return _html.unescape(re.sub(r"<[^>]+>", "", m.group(1))).strip() if m else ""

        title = grab(r"<title[^>]*>(.*?)</title>")
        desc = (grab(r'<meta[^>]+name=["\']description["\'][^>]+content=["\'](.*?)["\']')
                or grab(r'<meta[^>]+property=["\']og:description["\'][^>]+content=["\'](.*?)["\']'))
        if not (title or desc):
            return ""
        out = f"{_domain(url)}: {title}".strip(" :")
        if desc:
            out += f" — {desc}"
        return re.sub(r"\s+", " ", out)[:320]
    except Exception:
        return ""


def summary_from_thread(thread_text):
    """Thread'den marka site özet(ler)i. En fazla 2 aday dener, çalışanları döndürür.
    Her şey best-effort; hata/boş -> "". Çıktı qualify'a 'MARKA SİTE BİLGİSİ' olarak verilir."""
    key = (thread_text or "")[:500]
    if key in _CACHE:
        return _CACHE[key]
    parts = []
    for url in _candidate_urls(thread_text):
        s = _fetch_summary(url)
        if s:
            parts.append(s)
    out = "\n".join(parts)
    _CACHE[key] = out
    return out
