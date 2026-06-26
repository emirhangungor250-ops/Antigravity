# -*- coding: utf-8 -*-
"""Geçmiş iş örnekleri (referans) portföyünü bir Notion DB'sinden okur ve markaya en
uygun referansları (kategori + en yüksek izlenme) seçer. OPSİYONEL: config.PORTFOLIO_DB_ID
boşsa boş liste döner (teklif referanssız çıkar, bot yine çalışır).

Referans seçimi DETERMINISTIK (yapılı veri): link/izlenme uydurulmaz.
LLM yazar sadece bu seçilmiş referansların etrafına cümle kurar.

Notion DB ŞEMASI (kendi DB'nde bu adlarda property'ler olmalı; farklıysa env ile değiştir):
  PROP_BRAND    = "Marka"     (title)        -> referansın markası
  PROP_CATEGORY = "Kategori"  (select)       -> config.PORTFOLIO_CATEGORIES'ten biri
  PROP_PLATFORM = "Platform"  (multi/select) -> Instagram / YouTube / TikTok ...
  PROP_VIEWS    = "İzlenme"   (number)       -> izlenme sayısı
  PROP_TOPIC    = "Konu"      (rich_text)    -> videonun konusu/başlığı
  PROP_URL      = "URL"       (url)          -> referans video linki
"""
import os
import re
import requests
import config

# Notion property adları (kendi DB başlıklarına göre ENV ile değiştir).
PROP_BRAND = os.environ.get("NOTION_PROP_BRAND", "Marka")
PROP_CATEGORY = os.environ.get("NOTION_PROP_CATEGORY", "Kategori")
PROP_PLATFORM = os.environ.get("NOTION_PROP_PLATFORM", "Platform")
PROP_VIEWS = os.environ.get("NOTION_PROP_VIEWS", "İzlenme")
PROP_TOPIC = os.environ.get("NOTION_PROP_TOPIC", "Konu")
PROP_URL = os.environ.get("NOTION_PROP_URL", "URL")

_CACHE = {"rows": None}


def _short_topic(topic, brand=""):
    """Notion 'Konu' alanı = video başlığı (uzun, virgüllü anahtar-kelime listesi olabilir).
    Teklifte temiz görünmesi için ilk ayraçta kesip kısalt (deterministik). Yazar zaten kategoriden
    tanım üretir; bu yalnızca uzun metnin teklife sızmasına karşı kemer-askı güvencesi."""
    t = (topic or "").strip()
    if not t:
        return ""
    if brand and t.lower().startswith(brand.lower()):     # "Creati - Creati ..." tekrarını at
        t = t[len(brand):].lstrip(" -–—:|,")
    t = re.split(r"\s*,|\s*\||\s*/|\n|\s[-–—:]\s|\.\s", t, maxsplit=1)[0].strip()
    words = t.split()
    if len(words) > 6:
        t = " ".join(words[:6])
    return t.strip(" -–—:|.,")


def _prop_text(props, name):
    v = props.get(name, {})
    t = v.get("type")
    if t == "title":
        return "".join(x["plain_text"] for x in v.get("title", []))
    if t == "rich_text":
        return "".join(x["plain_text"] for x in v.get("rich_text", []))
    if t == "number":
        return v.get("number")
    if t == "select":
        return (v.get("select") or {}).get("name")
    if t == "multi_select":
        return [o["name"] for o in v.get("multi_select", [])]
    if t == "url":
        return v.get("url")
    return None


def _norm_platform(v):
    """Notion 'Platform' multi_select (liste) VEYA select (tek string) olabilir; her zaman liste
    döndür. Aksi halde select'te (r['platform'] or [...])[0] -> 'Instagram'[0]='I' platformu olur."""
    if isinstance(v, list):
        return v
    return [v] if v else []


def _working_token():
    for tok in config.NOTION_TOKEN_CANDIDATES:
        if tok:
            return tok
    return ""


def fetch_portfolio(force=False):
    if _CACHE["rows"] is not None and not force:
        return _CACHE["rows"]
    # Portföy opsiyonel: DB ID veya token yoksa boş liste (teklif referanssız çıkar).
    token = _working_token()
    if not config.PORTFOLIO_DB_ID or not token:
        _CACHE["rows"] = []
        return []
    rows, cursor = [], None
    headers = {"Authorization": f"Bearer {token}", "Notion-Version": "2022-06-28",
               "Content-Type": "application/json"}
    url = f"https://api.notion.com/v1/databases/{config.PORTFOLIO_DB_ID}/query"
    for _ in range(10):
        payload = {"page_size": 100}
        if cursor:
            payload["start_cursor"] = cursor
        r = requests.post(url, headers=headers, json=payload, timeout=30)
        r.raise_for_status()
        data = r.json()
        for p in data.get("results", []):
            pr = p["properties"]
            url_v = _prop_text(pr, PROP_URL)
            views = _prop_text(pr, PROP_VIEWS)
            if not url_v:
                continue
            rows.append({
                "brand": _prop_text(pr, PROP_BRAND) or "",
                "category": _prop_text(pr, PROP_CATEGORY) or "AI Genel",
                "platform": _norm_platform(_prop_text(pr, PROP_PLATFORM)),
                "views": int(views) if views else 0,
                "topic": _prop_text(pr, PROP_TOPIC) or "",
                "url": url_v,
            })
        if not data.get("has_more"):
            break
        cursor = data.get("next_cursor")
    _CACHE["rows"] = rows
    return rows


# Markanın diline göre izlenmeyi okunur yaz
def _fmt_views(n, lang):
    if not n:
        return ""
    # AŞAĞI yuvarla (asla şişirme): markaya gönderilen izlenme sayısı gerçeğin ÜSTÜNde olmamalı.
    # round() 1501'i "2K" yapıyordu; floor "1K" verir (markanın gördüğü gerçek sayıya yakın/altında).
    if n >= 1_000_000:
        s = f"{int(n / 100_000) / 10:.1f}".rstrip("0").rstrip(".") + "M"
    elif n >= 1000:
        s = f"{n // 1000}K"
    else:
        s = str(n)
    return f"{s} izlenme" if lang == "tr" else f"{s} views"


def select_references(category, lang="en", platform_pref=None, n=3):
    """Markanın kategorisine göre en yüksek izlenmeli n referansı seç.
    Yetersizse genel en yüksek izlenmelilerle tamamla."""
    rows = fetch_portfolio()
    if not rows:
        return []

    def plat_ok(r):
        if not platform_pref:
            return True
        return platform_pref in (r["platform"] or [])

    # Erişim önce: izlenme baz, platform eşleşmesi yalnızca YUMUŞAK çarpan (1.25x).
    # Böylece platform-eşleşen 40K'lık ref, 1.7M'lik eşleşmeyeni EZEMEZ (teklif hep en yüksek
    # izlenmeyi/erişimi gösterir). Eşit güçte refler arasında platform tercih edilir.
    def score(r):
        return r["views"] * (1.25 if plat_ok(r) else 1.0)

    primary = sorted([r for r in rows if r["category"] == category], key=score, reverse=True)
    overall = sorted(rows, key=score, reverse=True)

    chosen, seen_urls, seen_brands = [], set(), set()

    def take(pool, allow_dup_brand, require_views=True):
        for r in pool:
            if len(chosen) >= n:
                return
            if r["url"] in seen_urls:
                continue
            if require_views and not r["views"]:
                continue
            if not allow_dup_brand and r["brand"] in seen_brands:
                continue
            chosen.append(r)
            seen_urls.add(r["url"])
            seen_brands.add(r["brand"])

    # 1) kategori içi, izlenmesi olan + marka çeşitliliğiyle (marka başına 1)
    take(primary, allow_dup_brand=False)
    # 2) yetersizse genel en yüksek izlenme, izlenmesi olan + marka çeşitliliğiyle
    take(overall, allow_dup_brand=False)
    # 3) hâlâ yetersizse marka tekrarına izin ver (izlenmesi olan)
    take(primary, allow_dup_brand=True)
    take(overall, allow_dup_brand=True)
    # 4) son çare: izlenmesi olmayanları da kabul et
    take(overall, allow_dup_brand=True, require_views=False)

    out = []
    for r in chosen[:n]:
        out.append({
            "brand": r["brand"],
            "category": r["category"],
            "topic": _short_topic(r["topic"], r["brand"]),
            "url": r["url"],
            "views_label": _fmt_views(r["views"], lang),
            "platform": (r["platform"] or ["Instagram"])[0],
        })
    return out
