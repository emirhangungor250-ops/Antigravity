"""Tesis bilgi tabanı — yerel JSON dosyaları + kategori yönlendirme.

Bilgi tabanı knowledge_data/ altındaki JSON dosyalarıdır; başlangıçta belleğe yüklenir.
Ajan tek bir get_hotel_info(category) aracıyla doğru kategoriyi seçer (yönlendirme
matrisi = tool açıklaması).

KENDİ TESİSİN: knowledge_data/*.json dosyalarının içini kendi tesisinizin bilgisiyle
doldurun (oda tipleri, havuz/spa, yeme-içme, konum, politikalar). Şablon dosyalar
"buraya kendi bilginizi yazın" yapısıyla gelir; yapı korunur, içerik sizin olur.
"""

from __future__ import annotations

import json
from pathlib import Path

_DATA_DIR = Path(__file__).resolve().parent / "knowledge_data"

# kategori -> dosya
_FILES = {
    "overview_policies": "overview_and_policies.json",
    "rooms_facilities": "rooms_and_facilities.json",
    "pools_spa_kids": "pools_spa_kids.json",
    "meetings_events": "meetings_events.json",
    "location_transport": "location_transport.json",
    "dining": "dining__yeme_icme_canli_muzik.json",
    "transport_bus": "ulasim.json",
}

_CACHE: dict[str, str] = {}


def _load() -> None:
    if _CACHE:
        return
    for cat, fn in _FILES.items():
        p = _DATA_DIR / fn
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            _CACHE[cat] = json.dumps(data, ensure_ascii=False)
        except Exception:
            _CACHE[cat] = "{}"


def get_hotel_info(category: str) -> str:
    """Bir kategori için ham bilgi JSON'unu (string) döndürür."""
    _load()
    return _CACHE.get(category, f"Bilinmeyen kategori: {category}. Geçerli: {', '.join(_FILES)}")


# Ajanın doğru kategoriyi seçmesi için yönlendirme matrisi. Anahtar kelimeler ÖRNEKTİR —
# kendi tesisinizin terimlerine göre (varsa özel etkinlik/sanatçı adları, semt isimleri,
# havalimanı adı vb.) güncelleyebilirsiniz.
ROUTING_HINT = (
    "Kategoriler ve örnek anahtarlar:\n"
    "- dining: canlı müzik, müzik, akşam eğlencesi, program, yılbaşı, yılbaşı programı, 31 Aralık, "
    "brunch, sıra gecesi, restoran, yemek saatleri, bar, içecek, pansiyon tipi.\n"
    "- pools_spa_kids: havuz, termal, spa, hamam, sauna, buhar, aquapark, kaydırak, mini club, çocuk, "
    "aile kabini, family cabin, günübirlik, day use, günlük havuz, günlük giriş, dışarıdan havuz, "
    "dışarıdan spa, havuz ücreti, spa ücreti, termal fiyat, bone (bone zorunluluğu).\n"
    "- rooms_facilities: oda, aile odası, kapasite, housekeeping, fitness, aktivite.\n"
    "- meetings_events: toplantı, balo, salon, konferans, etkinlik salonu, tiyatro düzeni, ekipman.\n"
    "- location_transport: konum, ulaşım, havalimanı, km, mesafe, transfer, özel araç, adres.\n"
    "- transport_bus: otobüs, toplu taşıma ile geliş.\n"
    "- overview_policies: genel bilgi, check-in/out, yıldız, konsept, politika, sigara, evcil hayvan, "
    "iptal, değişiklik, kampanya, promosyon, paket, taksit, telefon, iletişim.\n"
    "\nÇAKIŞMA: Birden çok kategori uyuyorsa EN SPESİFİK alanı seç (ör. 'canlı müzik' veya 'yılbaşı "
    "programı' geçiyorsa daima dining). Tek seferde yalnızca 1 kategori çağır."
)

# Groq/OpenAI tool şeması
TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "get_hotel_info",
        "description": "Tesis hakkında bilgi (oda, havuz/spa, yeme-içme, toplantı, konum, "
                       "politika, ulaşım) almak için kullan. " + ROUTING_HINT,
        "parameters": {
            "type": "object",
            "properties": {
                "category": {
                    "type": "string",
                    "enum": list(_FILES.keys()),
                    "description": "Bilgi kategorisi.",
                }
            },
            "required": ["category"],
        },
    },
}
