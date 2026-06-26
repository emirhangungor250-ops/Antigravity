"""Instagram caption writer.

Memory kuralları:
  - Em-dash YASAK
  - Kısa cümle (max 15 kelime)
  - Marka/ürün adı caption'da geçmesin (kategori adı kullan)
  - Claude Code öncelikli (uygunsa)

Format:
  - Hook (1 cümle, max 12 kelime)
  - 3-5 satır bullet (• yok, yeni satır + 1-2 sözcük)
  - Soru (engagement)
  - 5-8 hashtag (Türkçe + İngilizce, AI/otomasyon ekosistem)

Max 2200 karakter (Instagram limiti).
"""

from typing import Optional

import anthropic

from config import settings
from core.style import SlidePlan
from ops_logger import get_ops_logger

ops = get_ops_logger("IG_Carousel_Cron", "Caption")


SYSTEM_PROMPT = """Sen bir Instagram caption yazarısısın. Türkçe içerik üretirsin.

KURALLAR (kesinlikle ihlal yok):
1. Em-dash (—) YASAK. Tire (-) ya da virgül kullan.
2. Cümle max 15 kelime.
3. Marka / ürün / şirket adı CAPTION'DA GEÇMESİN. Kategori adı kullan (örn "AI ses üretim aracı", "no-code platform").
4. "Reklam değil, öneri." opsiyonel olarak son satıra ekleyebilirsin.
5. Emoji minimal (max 2 toplam, hook'ta veya soruda).
6. Genel yapı:
   [HOOK — vurucu açılış, max 12 kelime]

   [boş satır]

   [3-5 madde — her madde tek satır, • yok, sadece yeni satır]

   [boş satır]

   [SORU — engagement, max 12 kelime]

   [boş satır]

   [HASHTAGLER — 5-8 adet, başında # ile, boşlukla ayrılmış]

7. Toplam max 1800 karakter (rezerv).
8. CTA örnek: "Detayları bio'daki linke yazdım." veya "Tüm carousel'i kaydet." gibi.

Sen ASLA tool_use dışında bir şey yazma. Tüm çıktın `write_caption` tool çağrısı olacak.
"""


CAPTION_TOOL = {
    "name": "write_caption",
    "description": "Instagram carousel için caption metni döndür.",
    "input_schema": {
        "type": "object",
        "properties": {
            "caption": {
                "type": "string",
                "description": "Tam Instagram caption (hook + bullets + soru + hashtag).",
            },
            "hashtags": {
                "type": "array",
                "items": {"type": "string"},
                "minItems": 5,
                "maxItems": 8,
                "description": "Caption'da geçen hashtag listesi (raporlama için, # dahil).",
            },
        },
        "required": ["caption", "hashtags"],
    },
}


def write(content: dict, slides: list[SlidePlan]) -> Optional[str]:
    """Tweet/thread + slide planından Instagram caption üret."""
    if settings.IS_DRY_RUN:
        ops.info("[DRY-RUN] Caption yazımı atlandı")
        return "[DRY-RUN] caption placeholder.\n\n#yapayzeka #otomasyon #ai #kobi #verimlilik"

    if settings.LLM_PROVIDER != "anthropic":
        ops.error("Şimdilik sadece anthropic destekleniyor", message=settings.LLM_PROVIDER)
        return None

    client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

    slides_summary = "\n".join(
        f"  Slide {s.index} ({s.role}): {s.overlay_text}" for s in slides
    )
    user_msg = (
        f"Kaynak: {content.get('source', '?')}\n"
        f"Başlık: {content.get('title', '')}\n\n"
        f"--- Carousel Slide Hook'ları ---\n{slides_summary}\n\n"
        f"--- Tweet/Thread Metni ---\n"
        f"{content.get('tweet_text') or content.get('thread') or content.get('linkedin_text', '')}\n\n"
        f"Görev: Bu carousel için Instagram caption yaz. `write_caption` tool'unu çağır."
    )

    try:
        response = client.messages.create(
            model=settings.WRITER_MODEL,
            max_tokens=2048,
            system=SYSTEM_PROMPT,
            tools=[CAPTION_TOOL],
            tool_choice={"type": "tool", "name": "write_caption"},
            messages=[{"role": "user", "content": user_msg}],
        )
    except Exception as e:
        ops.error("Anthropic caption exception", exception=e)
        return None

    for block in response.content:
        if getattr(block, "type", None) == "tool_use" and getattr(block, "name", "") == "write_caption":
            caption = (block.input.get("caption") or "").strip()
            if "—" in caption:
                ops.warning("Caption'da em-dash bulundu, replace ediliyor")
                caption = caption.replace("—", "-")
            if len(caption) > 2200:
                caption = caption[:2197] + "..."
            ops.success(f"Caption hazır ({len(caption)} char)")
            return caption

    ops.error("Caption tool_use bloğu yok")
    return None
