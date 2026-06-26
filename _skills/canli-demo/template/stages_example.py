"""Proje stage tanım dosyası — örnek şablon.

sync.py bu dosyayı sadece projede henüz yoksa kopyalar.
Projeye özgün stage'leri (id, label, icon, opsiyonel sub_stages) burada tanımla.

META → dashboard başlığı + alt başlık + input label'lar
STAGES → pipeline'ın görsel akışı (her stage emitter.start_stage(id) ile başlar)
"""

from __future__ import annotations

META = {
    "title": "Canlı Demo",
    "subtitle": "Pipeline durumu canlı izleniyor",
    "input_label_default": "Çalışma bekleniyor",
    "input_label_running": "Pipeline çalışıyor…",
}

STAGES: list[dict] = [
    {"id": "ornek_1", "label": "1. Adım", "icon": "📥"},
    {"id": "ornek_2", "label": "2. Adım", "icon": "⚙️"},
    {
        "id": "ornek_3",
        "label": "3. Adım (alt-akışlı)",
        "icon": "🎬",
        "sub_stages": [
            {"id": "sub_a", "label": "Alt iş A", "icon": "🅰️"},
            {"id": "sub_b", "label": "Alt iş B", "icon": "🅱️"},
        ],
    },
    {"id": "ornek_4", "label": "4. Adım", "icon": "✅"},
]
