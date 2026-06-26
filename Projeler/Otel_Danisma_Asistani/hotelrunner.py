"""HotelRunner booking engine fiyat/müsaitlik çekici.

Tesisin HotelRunner booking engine'inin kendi public JSON API'sinden saf HTTP ile
fiyat + müsaitlik çeker. Tarayıcı/screenshot/proxy/vision YOK; ek bir ücretli servis
gerekmez.

Akış (3 GET):
  1) infos/timestamp.json        -> sunucu zamanı
  2) search/availabilities.json  -> oda tipleri + satılabilir rate id'leri
  3) search/prices.json          -> gerçek fiyatlar (toplam + günlük)

Tek kapı: X-HR-CHALLENGE header'ı (yoksa {"error":"reset"}). api_key gerekmiyor.
Challenge bir TOTP: secret = base32(md5(host_url)); kod = TOTP(SHA1,6,30, secret, sunucu_zamanı).

KENDİ TESİSİN: Booking engine host adresi env'den okunur (HOTELRUNNER_HOST). Her
HotelRunner müşterisinin kendi alt alan adı vardır, örn:
  https://<tesisinizin-adi>.hotelrunner.com
Bu adresi rezervasyon sayfanızın URL'inden alabilirsiniz.

YEREL FİYAT (ülkeye göre fiyatlama): Bazı booking engine'ler fiyatı ZİYARETÇİ IP'sinin
ülkesine göre belirler; yurt dışı IP daha yüksek fiyat döndürebilir. Sunucunuz (örn.
Railway egress) yurt dışındaysa, doğru yerel fiyat için her isteğe yerel IP'li
`X-Forwarded-For` başlığı eklenir. Yerel IP env'den ayarlanır (HOTELRUNNER_GEO_IP).
Bu davranış tesise/engine'e göre değişir; gerekmiyorsa GEO_IP'yi boş bırakabilirsiniz.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import struct
import time
import urllib.parse
from datetime import date, datetime, timezone

import requests

# Tesisin HotelRunner booking engine host'u. Örn: https://<tesis-adi>.hotelrunner.com
# Rezervasyon sayfanızın adresinden alın. ZORUNLU (env'den).
HOST = os.getenv("HOTELRUNNER_HOST", "https://<tesis-adi>.hotelrunner.com").rstrip("/")
API = f"{HOST}/api/v1/bv3"
SEARCH_PAGE = f"{HOST}/bv3/search"
SEED = HOST  # challenge seed = host url
LOCALE = os.getenv("HOTELRUNNER_LOCALE", "tr")
CURRENCY = os.getenv("HOTELRUNNER_CURRENCY", "TRY")
TIMEOUT = float(os.getenv("HOTELRUNNER_TIMEOUT", "20"))
# Lokal dev'de SSL kesme (self-signed) olabilir; üretimde daima doğrula.
VERIFY_SSL = os.getenv("HOTELRUNNER_VERIFY_SSL", "1") != "0"
if not VERIFY_SSL:  # sadece lokal: uyarı gürültüsünü sustur
    requests.packages.urllib3.disable_warnings()  # type: ignore[attr-defined]

# Yerel fiyatı zorlamak için XFF'e konacak yerel IP'si. Ülkenize ait, coğrafi olarak
# hedef ülkeye çözülen herhangi bir genel IP işe yarar; env ile ayarlayın. Boş = XFF eklenmez.
GEO_IP = os.getenv("HOTELRUNNER_GEO_IP", "")
COUNTRY = os.getenv("HOTELRUNNER_COUNTRY", "TR")

_UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"
_COMMON = {
    "currency": CURRENCY,
    "locale": LOCALE,
    "country_alpha_2": COUNTRY,
    "referral_sessions": '{"deviceType":"desktop"}',
}


class HotelRunnerError(RuntimeError):
    """Fiyat çekme sırasında kurtarılamayan hata."""


def _session() -> requests.Session:
    s = requests.Session()
    s.headers.update({
        "User-Agent": _UA,
        "Accept": "application/json, text/plain, */*",
    })
    # Yerel fiyat için: bazı booking engine'ler geo'yu bu başlıklardan okur. GEO_IP boşsa
    # eklenmez (engine ziyaretçinin gerçek IP'sine göre fiyatlar).
    if GEO_IP:
        s.headers.update({"X-Forwarded-For": GEO_IP, "X-Real-IP": GEO_IP})
    s.verify = VERIFY_SSL
    return s


# --------------------------------------------------------------------------- #
# Challenge (TOTP)                                                             #
# --------------------------------------------------------------------------- #
def _totp(secret_b32: str, for_time: float, period: int = 30, digits: int = 6) -> str:
    counter = int(for_time // period)
    pad = "=" * ((8 - len(secret_b32) % 8) % 8)
    key = base64.b32decode(secret_b32 + pad)
    digest = hmac.new(key, struct.pack(">Q", counter), hashlib.sha1).digest()
    offset = digest[-1] & 0x0F
    code = struct.unpack(">I", digest[offset : offset + 4])[0] & 0x7FFFFFFF
    return str(code % (10 ** digits)).zfill(digits)


def _challenge(server_time_sec: float) -> str:
    md5_hex = hashlib.md5(SEED.encode()).hexdigest()
    secret = base64.b32encode(md5_hex.encode()).decode().replace("=", "")
    return _totp(secret, server_time_sec)


def server_time(sess: requests.Session) -> float:
    """HotelRunner sunucu zamanı (epoch sn). Challenge'ın TOTP penceresi buna bağlı."""
    r = sess.get(f"{API}/infos/timestamp.json", params=_COMMON, timeout=TIMEOUT)
    r.raise_for_status()
    t = r.json().get("time")
    if not t:
        raise HotelRunnerError("timestamp.json 'time' alanı yok")
    return float(t)


# --------------------------------------------------------------------------- #
# Parametre üretimi                                                            #
# --------------------------------------------------------------------------- #
def _norm_rooms(rooms: list[dict]) -> list[dict]:
    out = []
    for r in rooms or []:
        adult = int(r.get("adult_count") or 0)
        child = int(r.get("child_count") or 0)
        ages = [int(a) for a in (r.get("child_ages") or [])]
        out.append({"adult_count": adult, "child_count": child, "child_ages": ages,
                    "guest_count": adult + child})
    return out or [{"adult_count": 2, "child_count": 0, "child_ages": [], "guest_count": 2}]


def _day_count(checkin: str, checkout: str) -> int:
    d1 = datetime.strptime(checkin, "%Y-%m-%d").date()
    d2 = datetime.strptime(checkout, "%Y-%m-%d").date()
    return max((d2 - d1).days, 1)


def _shift_past_dates(checkin: str, checkout: str) -> tuple[str, str]:
    """Giriş tarihi geçmişteyse 1'er yıl ileri at (booking engine'in sessiz
    'düzeltmesi' yerine biz netleştiriyoruz)."""
    d1 = datetime.strptime(checkin, "%Y-%m-%d").date()
    d2 = datetime.strptime(checkout, "%Y-%m-%d").date()
    today = datetime.now(timezone.utc).date()
    while d1 < today:
        d1 = d1.replace(year=d1.year + 1)
        d2 = d2.replace(year=d2.year + 1)
    return d1.isoformat(), d2.isoformat()


def _availability_params(checkin: str, checkout: str, rooms: list[dict]) -> list[tuple[str, str]]:
    total_adult = sum(r["adult_count"] for r in rooms)
    total_child = sum(r["child_count"] for r in rooms)
    p: list[tuple[str, str]] = [
        ("checkin_date", checkin),
        ("checkout_date", checkout),
        ("day_count", str(_day_count(checkin, checkout))),
        ("room_count", str(len(rooms))),
        ("total_adult", str(total_adult)),
        ("total_child", str(total_child)),
    ]
    for r in rooms:  # rooms[][...] — boş index (Rails)
        p.append(("rooms[][adult_count]", str(r["adult_count"])))
        p.append(("rooms[][child_count]", str(r["child_count"])))
        p.append(("rooms[][guest_count]", str(r["guest_count"])))
        for age in r["child_ages"]:
            p.append(("rooms[][child_ages][]", str(age)))
    for i, r in enumerate(rooms):  # guest_rooms[i][...] — indeksli
        p.append((f"guest_rooms[{i}][adult_count]", str(r["adult_count"])))
        p.append((f"guest_rooms[{i}][guest_count]", str(r["guest_count"])))
        p.append((f"guest_rooms[{i}][child_count]", str(r["child_count"])))
        for age in r["child_ages"]:
            p.append((f"guest_rooms[{i}][child_ages][]", str(age)))
    for k, v in _COMMON.items():
        p.append((k, v))
    return p


def _price_params(checkin: str, checkout: str, rooms: list[dict],
                  rate_ids: list[int]) -> list[tuple[str, str]]:
    p: list[tuple[str, str]] = [("checkin_date", checkin), ("checkout_date", checkout)]
    for i, r in enumerate(rooms):
        p.append((f"guest_rooms[{i}][adult_count]", str(r["adult_count"])))
        p.append((f"guest_rooms[{i}][guest_count]", str(r["guest_count"])))
        p.append((f"guest_rooms[{i}][child_count]", str(r["child_count"])))
        for age in r["child_ages"]:
            p.append((f"guest_rooms[{i}][child_ages][]", str(age)))
    for rid in rate_ids:
        p.append(("ids[]", str(rid)))
    for k, v in _COMMON.items():
        p.append((k, v))
    return p


def _get_json(sess: requests.Session, path: str, params: list[tuple[str, str]]) -> dict:
    """Challenge header ile GET. 'reset' dönerse zamanı tazeleyip 1 kez yeniden dener."""
    for attempt in range(2):
        chal = _challenge(server_time(sess))
        headers = {"X-HR-CHALLENGE": chal, "Content-Type": "text/plain",
                   "Referer": f"{HOST}/bv3/search"}
        r = sess.get(f"{API}/{path}", params=params, headers=headers, timeout=TIMEOUT)
        try:
            data = r.json()
        except ValueError:
            raise HotelRunnerError(f"{path}: JSON değil (HTTP {r.status_code})")
        if data.get("error") == "reset" and attempt == 0:
            time.sleep(0.5)
            continue
        if data.get("error"):
            raise HotelRunnerError(f"{path}: API hatası: {data.get('error')}")
        return data
    raise HotelRunnerError(f"{path}: challenge 'reset' (2 deneme)")


# --------------------------------------------------------------------------- #
# Booking linki                                                                #
# --------------------------------------------------------------------------- #
def booking_link(checkin: str, checkout: str, rooms: list[dict]) -> str:
    search = {
        "checkin_date": checkin,
        "checkout_date": checkout,
        "day_count": _day_count(checkin, checkout),
        "room_count": len(rooms),
        "total_adult": sum(r["adult_count"] for r in rooms),
        "total_child": sum(r["child_count"] for r in rooms),
        "rooms": rooms,
        "guest_rooms": {str(i): r for i, r in enumerate(rooms)},
    }
    q = urllib.parse.quote(json.dumps(search))
    return f"{SEARCH_PAGE}?search={q}&locale={LOCALE}&currency={CURRENCY}"


# --------------------------------------------------------------------------- #
# Biçimlendirme                                                               #
# --------------------------------------------------------------------------- #
def format_try(amount: float) -> str:
    """21052.64 -> '21.052,64 TL' (Türkçe biçim)."""
    s = f"{amount:,.2f}"  # 21,052.64
    s = s.replace(",", "X").replace(".", ",").replace("X", ".")
    return f"{s} TL"


def _meal_plan_label(code: str | None, name: str | None) -> str:
    return (name or "").strip() or (code or "")


# --------------------------------------------------------------------------- #
# Ana sorgu                                                                    #
# --------------------------------------------------------------------------- #
def quote(checkin: str, checkout: str, rooms: list[dict] | None = None) -> dict:
    """Müsaitlik + fiyat sorgular.

    Dönüş:
      {
        "available": bool,
        "checkin": "...", "checkout": "...", "nights": N,
        "link": "<booking url>",
        "rooms": [ {name, meal_plan, total, per_night, currency, availability,
                    refundable, rate_name} ],   # en ucuz satılabilir rate, fiyata göre artan
        "message": "<TR özet metin>",
      }
    """
    rooms = _norm_rooms(rooms or [])
    checkin, checkout = _shift_past_dates(checkin, checkout)
    nights = _day_count(checkin, checkout)
    link = booking_link(checkin, checkout, rooms)

    sess = _session()
    avail = _get_json(sess, "search/availabilities.json",
                      _availability_params(checkin, checkout, rooms))
    room_types = avail.get("available_room_types") or []

    if not room_types:
        return {
            "available": False, "checkin": checkin, "checkout": checkout, "nights": nights,
            "link": link, "rooms": [],
            "message": _msg_unavailable(checkin, checkout, rooms),
        }

    # Tüm satılabilir rate id'lerini topla -> tek prices.json çağrısı
    all_rate_ids: list[int] = []
    for rt in room_types:
        all_rate_ids.extend(int(x) for x in (rt.get("available_rate_ids") or []))
    all_rate_ids = list(dict.fromkeys(all_rate_ids))  # uniq, sırayı koru

    price_map: dict[str, dict] = {}
    if all_rate_ids:
        pdata = _get_json(sess, "search/prices.json",
                          _price_params(checkin, checkout, rooms, all_rate_ids))
        # prices: { "<oda_idx>": { "<rate_id>": {price, daily_prices, policy} } }
        price_map = (pdata.get("prices") or {}).get("0") or {}

    results = []
    for rt in room_types:
        best = _cheapest_sellable_rate(rt, price_map)
        if not best:
            continue
        total = float(best["price"])
        results.append({
            "name": rt.get("name"),
            "meal_plan": _meal_plan_label(rt.get("meal_plan_code"), rt.get("meal_plan")),
            "total": total,
            "per_night": round(total / nights, 2) if nights else total,
            "currency": CURRENCY,
            "availability": rt.get("availability"),
            "refundable": bool(best.get("refundable")),
            "rate_name": best.get("rate_name"),
        })

    results.sort(key=lambda x: x["total"])

    if not results:
        return {
            "available": False, "checkin": checkin, "checkout": checkout, "nights": nights,
            "link": link, "rooms": [],
            "message": _msg_unavailable(checkin, checkout, rooms),
        }

    return {
        "available": True, "checkin": checkin, "checkout": checkout, "nights": nights,
        "link": link, "rooms": results,
        "message": _msg_available(checkin, checkout, rooms, nights, results),
    }


def _cheapest_sellable_rate(room_type: dict, price_map: dict) -> dict | None:
    """Oda tipinin satılabilir rate'leri içinde en ucuzu (fiyatı prices.json'dan)."""
    rate_details = room_type.get("rate_details") or {}
    best = None
    for rid in (room_type.get("available_rate_ids") or []):
        rid_s = str(rid)
        rd = rate_details.get(rid_s) or {}
        if not rd.get("sell_online", True):
            continue
        priced = price_map.get(rid_s)
        if not priced or priced.get("price") in (None, 0):
            continue
        price = float(priced["price"])
        if best is None or price < best["price"]:
            best = {
                "rate_id": rid_s,
                "price": price,
                "rate_name": rd.get("name"),
                "refundable": rd.get("refundable") and not rd.get("non_refundable", False),
            }
    return best


# --------------------------------------------------------------------------- #
# Mesaj metinleri (deterministik — LLM gerekmez)                              #
# --------------------------------------------------------------------------- #
_TR_MONTHS = ["", "Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran",
              "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]


def _fmt_date(d: str) -> str:
    dt = datetime.strptime(d, "%Y-%m-%d").date()
    return f"{dt.day} {_TR_MONTHS[dt.month]} {dt.year}"


def _guest_summary(rooms: list[dict]) -> str:
    a = sum(r["adult_count"] for r in rooms)
    c = sum(r["child_count"] for r in rooms)
    parts = [f"{a} yetişkin"]
    if c:
        parts.append(f"{c} çocuk")
    if len(rooms) > 1:
        parts.append(f"{len(rooms)} oda")
    return ", ".join(parts)


def _msg_available(checkin: str, checkout: str, rooms: list[dict], nights: int,
                   results: list[dict]) -> str:
    head = (f"{_fmt_date(checkin)} - {_fmt_date(checkout)} ({nights} gece), "
            f"{_guest_summary(rooms)} için müsait odalar:")
    lines = []
    for r in results:
        meal = f" ({r['meal_plan']})" if r["meal_plan"] else ""
        lines.append(f"- {r['name']}{meal}: {format_try(r['total'])} ({nights} gece, toplam)")
    return head + "\n" + "\n".join(lines)


def _msg_unavailable(checkin: str, checkout: str, rooms: list[dict]) -> str:
    return (f"{_fmt_date(checkin)} - {_fmt_date(checkout)} tarihlerinde "
            f"{_guest_summary(rooms)} için müsait oda bulunmuyor.")


# --------------------------------------------------------------------------- #
# CLI test                                                                     #
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    import sys
    ci = sys.argv[1] if len(sys.argv) > 1 else "2026-08-20"
    co = sys.argv[2] if len(sys.argv) > 2 else "2026-08-22"
    ad = int(sys.argv[3]) if len(sys.argv) > 3 else 2
    res = quote(ci, co, [{"adult_count": ad, "child_count": 0, "child_ages": []}])
    print(json.dumps(res, ensure_ascii=False, indent=2))
