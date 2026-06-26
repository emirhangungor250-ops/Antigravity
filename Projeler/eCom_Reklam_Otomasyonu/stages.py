"""eCom Reklam Otomasyonu — canlı demo stage tanımları."""

from __future__ import annotations

META = {
    "title": "eCom Reklam Otomasyonu",
    "subtitle": "Telegram'dan ürün linki gir, reklam videosunu izle",
    "input_label_default": "Ürün bekleniyor",
    "input_label_running": "Ürün analiz ediliyor…",
}

STAGES: list[dict] = [
    {"id": "extract", "label": "Ürün analizi", "icon": "🔍"},
    {"id": "scenario", "label": "Senaryo üretimi", "icon": "🎬"},
    {
        "id": "produce",
        "label": "Video üretimi",
        "icon": "🎥",
        "sub_stages": [
            {"id": "assets", "label": "Karakter + dış ses", "icon": "🎭"},
            {"id": "scenes", "label": "Sahne renderları", "icon": "🎬"},
            {"id": "merge", "label": "Birleştirme + sync", "icon": "🎵"},
        ],
    },
    {"id": "caption", "label": "Caption + hashtag", "icon": "✍️"},
    {"id": "upload", "label": "Sosyal medyaya yükleme", "icon": "📤"},
]
