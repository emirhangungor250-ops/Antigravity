"""Claude Opus 4.7 ile YouTube açıklaması üretimi.

Yaklaşım: structured output via tool_use (explicit schema).
Memory'deki "Claude Opus 4.7 prefill yok, permissive schema sarmalama tuzağı"
uyarısı için strict JSON schema + tool_choice kullanılır.
"""

import json
import os
import random
from pathlib import Path
from typing import Optional

from anthropic import Anthropic

ROOT = Path(__file__).resolve().parent.parent
STYLE_PATH = ROOT / "data" / "style_corpus.json"
AFFILIATE_PATH = ROOT / "data" / "brand_affiliates.json"

MODEL = "claude-opus-4-7"
FEW_SHOT_COUNT = 4

# Kanal sahibinin adı + organic videolarda kullanılacak sabit CTA link bloğu.
# Bunları .env'den doldurun (CREATOR_NAME, ORGANIC_CTA_BLOCK).
CREATOR_NAME = os.getenv("CREATOR_NAME", "Kanal sahibi")
# ORGANIC_CTA_BLOCK: organic (iş birliği olmayan) videolarda hero'ya eklenecek
# kendi sabit linkleriniz (topluluk, hizmet formu vb.). Çok satırlı olabilir.
ORGANIC_CTA_BLOCK = os.getenv("ORGANIC_CTA_BLOCK", "").strip()

_TOOL_SCHEMA = {
    "name": "video_aciklama_olustur",
    "description": (
        "Kanal sahibinin YouTube videosu için tam açıklamayı üretir. "
        "Çıktı: ana açıklama metni + saniye bazlı chapter listesi + iş birliği yapılan markanın anahtarı."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "ana_metin": {
                "type": "string",
                "description": (
                    "Açıklamanın gövdesi. Chapter listesi BURAYA YAZILMAZ, onu ayrı 'chapters' alanına koy. "
                    "Kanal sahibinin tarzında: kısa cümleler, 👇🏻 emojisi ile link blokları, organic CTA bloğu + "
                    "iş birliği markası gibi sabit linkler. Başlangıçta marka/CTA tanıtımı, "
                    "sonra video ne anlatıyor 2-4 paragraf. Em-dash YASAK. Maks 1500 karakter."
                ),
            },
            "chapters": {
                "type": "array",
                "description": (
                    "Saniye bazlı bölüm listesi. İlk chapter mutlaka saniye=0 (Giriş). Son chapter "
                    "videonun bitişine yakın (Kapanış). 4-10 chapter ideal. Başlıklar 2-6 kelime, "
                    "video transcript'iyle TUTARLI olmalı — uydurma yasak."
                ),
                "items": {
                    "type": "object",
                    "properties": {
                        "saniye": {"type": "integer", "minimum": 0},
                        "baslik": {"type": "string", "minLength": 2, "maxLength": 80},
                    },
                    "required": ["saniye", "baslik"],
                },
                "minItems": 3,
                "maxItems": 15,
            },
            "marka_anahtari": {
                "type": "string",
                "description": (
                    "İşbirliği yapılan markanın anahtar adı (brand_affiliates.json'daki anahtarlardan biri). "
                    "Verilen brand_affiliates listesinden biri olmalı. Markayı belirleyemiyorsan boş string döndür."
                ),
            },
        },
        "required": ["ana_metin", "chapters", "marka_anahtari"],
    },
}


def _load_style_corpus() -> list[dict]:
    if not STYLE_PATH.exists():
        return []
    with open(STYLE_PATH, encoding="utf-8") as f:
        return json.load(f)


def _load_affiliates() -> dict[str, str]:
    if not AFFILIATE_PATH.exists():
        return {}
    with open(AFFILIATE_PATH, encoding="utf-8") as f:
        return json.load(f)


def _format_seconds_for_chapter(s: int) -> str:
    """YouTube açıklamasında 4:31 / 1:02:11 formatı (saat 0'sız)."""
    s = max(0, int(s))
    h = s // 3600
    m = (s % 3600) // 60
    sec = s % 60
    if h > 0:
        return f"{h}:{m:02d}:{sec:02d}"
    return f"{m:02d}:{sec:02d}"


def _few_shot_block(corpus: list[dict], k: int = FEW_SHOT_COUNT) -> str:
    """En iyi tarz örneklerini sistem prompt'a injekte etmek için seç."""
    if not corpus:
        return ""
    sample = random.sample(corpus, min(k, len(corpus)))
    blocks = []
    for v in sample:
        blocks.append(
            f"### Örnek video: {v['title']}\n\n```\n{v['description']}\n```\n"
        )
    return "\n".join(blocks)


def _system_prompt(corpus: list[dict], affiliates: dict[str, str]) -> str:
    brands = ", ".join(k for k in affiliates.keys() if not k.startswith("_")) or "(boş)"
    organic_cta = ORGANIC_CTA_BLOCK or "(ORGANIC_CTA_BLOCK env değişkeni boş — organic videoda ek CTA linki ekleme)"
    return f"""Sen {CREATOR_NAME} adlı YouTube kanalının video açıklamalarını yazıyorsun.

Yazım kuralları (KESİN):
- Türkçe, sade dil. Jargon yok.
- Em-dash (—) YASAK. Tire (-) veya nokta kullan.
- Cümleler kısa. Max 15 kelime.
- 👇🏻 ✅ 🤝 😱 gibi emojiler kullan (kanalın tarzına uygun).
- Link blokları "Açıklama 👇🏻\\nURL" formatında, her link yeni satır.

İŞ BİRLİĞİ vs ORGANIC video formatı (KRİTİK fark):
- İş birliği videosu (marka_anahtari boş DEĞİLSE): ana_metin hero'da SADECE marka linki olur, "(iş birliği)" notu eklenir. Organic CTA bloğu EKLENMEZ. Sadece marka + 2-4 paragraf özet.
- Organic video (marka_anahtari BOŞ): hero'da aşağıdaki ORGANIC CTA bloğu yer alır. "(reklam değil, öneri)" notu uygun.
- Hero format'ı (iş birliği): "MarkaAdi ile <kısa pitch> 👇🏻\\n<marka_url> (iş birliği)"
- ORGANIC CTA bloğu (SADECE organic videoda kullan):
{organic_cta}

Chapter başlık kuralları (KESİN):
- Mastar fiil + jenerik kavram kullan. ✅ "Storyboard Üretmek", "Video Üretmek", "Prompt Vermek", "Kanalı Kopyalayalım"
- 2-4 kelime ideal. Eylem var, kavram var, marka adı yok.
- YASAKLI kelimeler (chapter başlıklarında geçmesi YASAK):
  * Marka adları (örn. araç/platform/model adları)
  * Sürüm/versiyon: V2, V3, 2.0, 3.0, Pro, Ultra, Plus, Premium
  * Teknik özellik adları: Multi-Scene, Reference Image, Agent Mode vb.
- ❌ "Agent V2 ile Video Üretmek" → ✅ "Video Üretmek"
- ❌ "Ultra Plan ve Fiyatlandırma" → ✅ "Sınırsız Üretim" veya "Fiyat ve Limitler"
- ❌ "Reference Image Eklemek" → ✅ "Atmosfer Eklemek" veya "Görsel Eklemek"

Sondaki affiliate link tekrarı YASAK, hero'da zaten var.

Aşağıdaki tam tarz örneklerini incele ve aynı tona sadık kal:

{_few_shot_block(corpus)}

Mevcut affiliate markaları (marka_anahtari sadece bunlardan biri olabilir): {brands}

Çıktıyı SADECE 'video_aciklama_olustur' tool'unu çağırarak ver. Tool dışı düz metin yazma.
"""


def _user_prompt(video_name: str, video_url: str, brief: str, transcript_with_timestamps: str, duration_sec: int) -> str:
    has_transcript = bool(transcript_with_timestamps and transcript_with_timestamps.strip())
    parts = [
        f"VİDEO ADI: {video_name}",
        f"YOUTUBE URL: {video_url}",
        f"TOPLAM SÜRE: ~{duration_sec // 60} dakika {duration_sec % 60} saniye",
    ]
    if brief:
        parts.append(
            f"\nNOTION SAYFA İÇERİĞİ (video brief'i + sahne sahne script + CTA, kanal sahibi buraya yazdı):\n{brief[:8000]}"
        )
    if has_transcript:
        parts.append(
            f"\nVİDEO TRANSCRIPT'İ (timestamp tag'leri ile, chapter saniyelerini bu tag'lerden çıkar):\n\n{transcript_with_timestamps[:18000]}"
        )
        parts.append(
            "\nGÖREV: Bu video için açıklama üret. "
            "ana_metin kanal sahibinin tarzında (link blokları + 2-4 paragraf özet, chapter LİSTESİ DEĞİL). "
            "chapters transcript'le tutarlı, saniye bazlı. "
            "marka_anahtari video konusuna en uygun affiliate marka veya boş."
        )
    else:
        parts.append(
            "\nÖNEMLİ: Bu video için YouTube transcript HENÜZ YOK (unlisted veya yeni yüklendi). "
            "Chapter saniyelerini Notion sayfasındaki SAHNE SIRALAMASINA göre orantılı dağıt. "
            "Toplam süre yukarıda. Sahnelerin uzunluğunu sayfa içeriğindeki anlatım yoğunluğundan tahmin et."
        )
        parts.append(
            "\nGÖREV: Bu video için açıklama üret. "
            "ana_metin kanal sahibinin tarzında (link blokları + 2-4 paragraf özet, chapter LİSTESİ DEĞİL). "
            "chapters sahne sırasına göre orantılı saniyelerle. "
            "marka_anahtari video konusuna en uygun affiliate marka veya boş."
        )
    return "\n".join(parts)


def build_description(
    *,
    video_name: str,
    video_url: str,
    brief: str,
    transcript_with_timestamps: str,
    duration_sec: int,
) -> dict:
    """Claude Opus 4.7 ile yapılandırılmış açıklama üret.

    Returns: {"ana_metin": str, "chapters": [{saniye, baslik}, ...], "marka_anahtari": str}
    """
    corpus = _load_style_corpus()
    affiliates = _load_affiliates()

    client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    resp = client.messages.create(
        model=MODEL,
        max_tokens=4096,
        system=_system_prompt(corpus, affiliates),
        tools=[_TOOL_SCHEMA],
        tool_choice={"type": "tool", "name": "video_aciklama_olustur"},
        messages=[
            {
                "role": "user",
                "content": _user_prompt(video_name, video_url, brief, transcript_with_timestamps, duration_sec),
            }
        ],
    )

    for block in resp.content:
        if getattr(block, "type", "") == "tool_use" and block.name == "video_aciklama_olustur":
            data = block.input
            data["chapters"] = sorted(data.get("chapters", []), key=lambda c: c["saniye"])
            return data
    raise RuntimeError("Claude tool_use bloğu döndürmedi.")


def assemble_final_description(
    *,
    ai_output: dict,
    affiliate_link: Optional[str],
) -> str:
    """Claude'un ürettiği ana_metin + chapters + (varsa) affiliate linki tek metne birleştir."""
    parts: list[str] = []
    body = ai_output.get("ana_metin", "").strip()
    if body:
        parts.append(body)

    chapters = ai_output.get("chapters", [])
    if chapters:
        parts.append("")  # boş satır
        for ch in chapters:
            ts = _format_seconds_for_chapter(int(ch.get("saniye", 0)))
            title = (ch.get("baslik") or "").strip()
            if title:
                parts.append(f"{ts} {title}")

    # İş birliği linki sonda TEKRAR EDİLMEZ — hero'da zaten var (system prompt kuralı).
    # Sadece marka_anahtari verildiği halde Claude hero'da URL'i unutursa ekle.
    if affiliate_link and affiliate_link not in body:
        parts.append("")
        parts.append(f"{affiliate_link} (iş birliği)")

    return "\n".join(parts).strip()
