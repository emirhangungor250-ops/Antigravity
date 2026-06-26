"""TR resmi + dini tatil tarihleri — statik tablo (Calendarific dış bağımlılığı yok).

Sabit resmi tatiller kesindir. Dini bayramlar (Ramazan/Kurban) Diyanet'in yayımladığı
resmi tarihlerdir. Tabloda olmayan yıl/tatil için "tarih teyit edilemedi" döner ki ajan
yanlış tarih uydurmak yerine misafirden kesin tarih istesin (yanlış tarihle fiyat sorgusu olmasın).
"""

from __future__ import annotations

from datetime import date, datetime, timezone

# Sabit resmi tatiller: (ay, gün, ad). Her yıl aynı.
_FIXED = [
    (1, 1, "Yılbaşı"),
    (4, 23, "23 Nisan Ulusal Egemenlik ve Çocuk Bayramı"),
    (5, 1, "1 Mayıs Emek ve Dayanışma Günü"),
    (5, 19, "19 Mayıs Atatürk'ü Anma, Gençlik ve Spor Bayramı"),
    (7, 15, "15 Temmuz Demokrasi ve Millî Birlik Günü"),
    (8, 30, "30 Ağustos Zafer Bayramı"),
    (10, 29, "29 Ekim Cumhuriyet Bayramı"),
]

# Dini bayramlar: yıl -> {anahtar: (başlangıç, bitiş, görünen ad)}. Ramazan 3 gün, Kurban 4 gün.
# 2028-2030 tarihleri 2026-06-14'te eklendi: Ramazan iki bağımsız kaynakla (truecalendar +
# takvim.com) doğrulandı; truecalendar'ın 2027 değeri Diyanet çapamızla (10 Mart) birebir
# tuttuğu için Diyanet-tutarlı kabul edildi. Kurban tarihlerinde tüm kaynaklar hemfikir.
# NOT: Diyanet her yılı ~1 yıl önceden resmî kesinleştirir; yıl yaklaşınca ±1 gün teyit edilmeli.
_RELIGIOUS = {
    2026: {
        "ramazan": ("2026-03-20", "2026-03-22", "Ramazan Bayramı"),
        "kurban": ("2026-05-27", "2026-05-30", "Kurban Bayramı"),
    },
    2027: {
        "ramazan": ("2027-03-10", "2027-03-12", "Ramazan Bayramı"),
        "kurban": ("2027-05-16", "2027-05-19", "Kurban Bayramı"),
    },
    2028: {
        "ramazan": ("2028-02-27", "2028-02-29", "Ramazan Bayramı"),
        "kurban": ("2028-05-05", "2028-05-08", "Kurban Bayramı"),
    },
    2029: {
        "ramazan": ("2029-02-15", "2029-02-17", "Ramazan Bayramı"),
        "kurban": ("2029-04-24", "2029-04-27", "Kurban Bayramı"),
    },
    2030: {
        "ramazan": ("2030-02-05", "2030-02-07", "Ramazan Bayramı"),
        "kurban": ("2030-04-13", "2030-04-16", "Kurban Bayramı"),
    },
}

_TR_MONTHS = ["", "Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran",
              "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]


def _today() -> date:
    return datetime.now(timezone.utc).date()


def _fmt(d: str) -> str:
    dt = datetime.strptime(d, "%Y-%m-%d").date()
    return f"{dt.day} {_TR_MONTHS[dt.month]} {dt.year}"


def _match_religious(name: str) -> str | None:
    n = name.lower()
    if any(k in n for k in ("ramazan", "şeker", "seker", "eid al-fitr", "fitr")):
        return "ramazan"
    if any(k in n for k in ("kurban", "adha")):
        return "kurban"
    return None


def get_holiday(name: str) -> str:
    """Bir tatilin BUGÜNDEN SONRAKİ en yakın tarih aralığını döndürür."""
    today = _today()

    # 1) Dini bayram mı?
    rel = _match_religious(name)
    if rel:
        for year in sorted(_RELIGIOUS):
            entry = _RELIGIOUS[year].get(rel)
            if not entry:
                continue
            start, end, label = entry
            if datetime.strptime(end, "%Y-%m-%d").date() >= today:
                return f"{label} {year}: {_fmt(start)} - {_fmt(end)}."
        return (f"{name} için kesin tarihi şu an teyit edemiyorum. Lütfen gelmek istediğiniz "
                f"net tarihleri belirtin, müsaitlik ve fiyatı ona göre kontrol edeyim.")

    # 2) Sabit resmi tatil mi?
    n = name.lower()
    keys = {
        "yılbaşı": (1, 1), "yilbasi": (1, 1),
        "23 nisan": (4, 23), "çocuk": (4, 23), "cocuk": (4, 23),
        "1 mayıs": (5, 1), "emek": (5, 1),
        "19 mayıs": (5, 19), "gençlik": (5, 19), "genclik": (5, 19),
        "15 temmuz": (7, 15), "demokrasi": (7, 15),
        "30 ağustos": (8, 30), "zafer": (8, 30),
        "29 ekim": (10, 29), "cumhuriyet": (10, 29),
    }
    for kw, (mo, da) in keys.items():
        if kw in n:
            label = next(lbl for (m, d, lbl) in _FIXED if (m, d) == (mo, da))
            year = today.year if date(today.year, mo, da) >= today else today.year + 1
            return f"{label}: {da} {_TR_MONTHS[mo]} {year}."

    return (f"'{name}' tatilini tanıyamadım. Gelmek istediğiniz net tarihleri belirtirseniz "
            f"müsaitlik ve fiyatı kontrol edebilirim.")


TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "get_holiday",
        "description": "Bir resmi/dini tatilin (Ramazan Bayramı, Kurban Bayramı, 23 Nisan, "
                       "29 Ekim vb.) yaklaşan tarih aralığını öğrenmek için kullan. Misafir bir "
                       "bayramda gelmek istediğini söylerse önce bunu çağır, sonra o tarihlerle fiyat sor.",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Tatil adı, ör: 'Kurban Bayramı'."}
            },
            "required": ["name"],
        },
    },
}
