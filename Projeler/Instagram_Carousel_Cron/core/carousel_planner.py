"""Carousel Planner — tweet/thread metnini N slide'lık carousel'a böler.

LLM: Anthropic Claude Opus 4.7 (memory: prefill yok, temperature deprecate;
permissive schema'da sarmalama riski → explicit input_schema + tool_use kullan).

Çıktı (validated): list[SlidePlan]
"""

import json
from typing import Optional

import anthropic

from config import settings
from core.style import (
    SLIDE_ROLE,
    SlidePlan,
    SCENE_PHOTOREALISTIC_PREAMBLE,
    SCENE_NEGATIVE_PROMPT,
    SCENE_BOTTOM_THIRD_RULE,
    SCENE_COLOR_PALETTE_HINT,
    BRAND_MARK_TEXT,
)
from ops_logger import get_ops_logger

ops = get_ops_logger("IG_Carousel_Cron", "Planner")


SYSTEM_PROMPT = """Sen bir Instagram carousel planlamacısısın. Türkçe içerik üretirsin.
Kullanıcı sana bir Tweet/X thread metni verir. Sen bunu Instagram için 5-9 slide'lık \
"kaydırmalı post"a (carousel) dönüştürürsün.

Carousel'in AMACI: kullanıcıyı durduran kapak (slide 1) + her slide'da BİR ŞEY ÖĞRETMEK \
(slide 2..N-1) + harekete geçirme (son slide). Kapak fotoğrafı değil — bilgilendirici post.

═══════════════════════════════════════════════════
KURALLAR
═══════════════════════════════════════════════════

1. SLAYT YAPISI:
   - Slide 1 = HOOK (kapak mantığı, dev metin, max 4 kelime, sadece dikkat çek)
   - Slide 2..N-1 = ARGÜMAN (KÜÇÜK BAŞLIK + UZUN BİLGİLENDİRİCİ PARAGRAF)
   - Slide N = CTA (soru + bio yönlendirme, kapak gibi orta uzunluk)

2. HOOK SLIDE (slide 1):
   - overlay_text: Türkçe BÜYÜK HARF, 1-4 kelime (örn: "AJANSA VEDA", "15 BİN TL ÇÖPE")
   - body_text: BOŞ (hook görseli + dev metin yeterli)
   - Em-dash yasak, kategorik dil
   - **SCENE_DESCRIPTION KRİTİK — ABSÜRT/AGRESİF/SHOCK metafor zorunlu:**
     * Sıradan portrait YASAK (kafede oturan adam, telefonuna bakan kişi → ÇÖPE).
     * Aksiyon dolu, freeze-frame, movie poster anı: yıkım, öfke, fırlatma, alev,
       yumruk, parodi, beklenmedik kaos, dramatik isyan, fiziksel komedi.
     * Örnek doğru hook sahneleri:
       - "Adam ajansın camdan tabela penceresine sandalye fırlatıyor, an'da yakalanan freeze frame"
       - "Yüzlerce fatura kâğıdı kar gibi uçuyor, ortada öfkeli figür havaya yumruk atmış"
       - "Adam fatura yığınını benzin döküp ateşe vermiş, alevler arkadan yükseliyor, sırtı dönük"
       - "Adam ofis camından koca bir bilgisayar atıyor, parçalar havada"
       - "Adam ajansın önünde dramatic protest pose, elinde yırtılmış sözleşme parçaları"
     * Sahne **VURUCU + viral-shock + absürt** olmalı, scroll-stopping 0.5sn'de.
     * Reels learnings #10: klişe = skor 0. "Person at laptop" = anında redde tabidir.

3. ARGÜMAN SLIDE'LAR (slide 2..N-1) — EN KRİTİK KISIM:
   - overlay_text: Türkçe BÜYÜK HARF küçük başlık, 2-5 kelime (örn: "MALIYET 600 KAT DÜŞTÜ", "5 DAKİKADA HAZIR")
   - body_text: 3-5 KISA CÜMLE, 250-500 karakter, Türkçe normal yazım (NOT all-caps).
     * Somut, sayısal, hikayeli. Klişe yok.
     * Her cümle max 14 kelime.
     * Em-dash (—) YASAK.
     * Marka/ürün adı geçmesin → kategori adı kullan.
     * Örnek body_text:
       "Eskiden ajansa 15.000 TL veriyordu. Şimdi aylık 25 dolar bir araç kullanıyor.
       Yıllık fark 175.000 TL'yi aşıyor. Aynı bütçeyle 50 farklı kampanya test edebiliyor."
   - sub_text: BOŞ (body_text yeterli)

4. CTA SLIDE (son slide):
   - overlay_text: Türkçe BÜYÜK HARF soru, 4-9 kelime (örn: "SEN HÂLÂ ÖDÜYOR MUSUN?")
   - body_text: BOŞ veya 1-2 cümle yönlendirme (opsiyonel)
   - sub_text: "Bio'daki linke dokun" gibi micro-CTA (opsiyonel)

5. SCENE_DESCRIPTION (İngilizce, Kie AI'a gider):
   - PHOTOREALISTIC editorial photography. Illustration / 3D / cartoon YASAK.
   - Tek odak nokta (single subject), dramatik composition.
   - SOMUT FİZİKSEL METAFOR (ör: "manual evrak yorgunluğu" → "kişi binlerce evrak arasında, masada uyumuş, gece 2 lamba ışığı altında")
   - "Person at laptop" klişesinden KAÇIN.
   - SAHNEDE HİÇBİR YAZI/SAYI/LOGO/TABELA OLMAMALI (overlay metin Pillow ile basılacak).
   - Renk paleti: deep navy / charcoal / warm cream / brass-gold (neon, pastel, mor YASAK).
   - **HOOK ve CTA slide:** Bottom third (alt %33) sakin olsun.
   - **ARGÜMAN slide:** UPPER THIRD (üst %33) subject + action; LOWER TWO THIRDS (alt %66) tamamen sakin/atmosferik/koyu (örn: koyu duvar, yumuşak lambaeli ışık, boş zemin) — body paragrafı oraya basılacak.
   - 80-120 kelime arası, somut detay (lokasyon, ışık, kamera açısı, nesne).

6. AKIŞ:
   - Hook → ilgi çek
   - 2-4 argüman → değer ver (her slide TEK bir öğreti, somut + sayısal + hikayeli)
   - Son argüman → "şimdi ne yapmalı"
   - CTA → soru + bio

Sen ASLA tool_use dışında bir şey yazma. Tüm çıktın `plan_carousel` tool çağrısı olacak.
"""


PLAN_TOOL = {
    "name": "plan_carousel",
    "description": "Verilen içeriği Instagram carousel slide'larına böl ve döndür.",
    "input_schema": {
        "type": "object",
        "properties": {
            "rationale": {
                "type": "string",
                "description": "Akış mantığı (1-2 cümle): neden bu yapı, hook neyi vaat ediyor.",
            },
            "slides": {
                "type": "array",
                "minItems": 5,
                "maxItems": 9,
                "items": {
                    "type": "object",
                    "properties": {
                        "index": {"type": "integer", "minimum": 1, "maximum": 9},
                        "role": {"type": "string", "enum": ["hook", "argument", "cta"]},
                        "overlay_text": {
                            "type": "string",
                            "description": "Slide üzerine basılacak Türkçe BÜYÜK HARF metin. Hook=1-4 kelime, Argument=2-5 kelime başlık, CTA=4-9 kelime soru.",
                        },
                        "body_text": {
                            "type": "string",
                            "description": "ARGUMENT slide için ZORUNLU 3-5 kısa cümle (250-500 char) bilgilendirici paragraf, Türkçe normal yazım. Hook ve CTA için BOŞ string.",
                        },
                        "sub_text": {
                            "type": "string",
                            "description": "Opsiyonel — sadece CTA için micro yönlendirme (örn 'Bio'daki linke dokun'). Diğerlerinde boş.",
                        },
                        "scene_description": {
                            "type": "string",
                            "description": "İngilizce, photorealistic, 80-120 kelime sahne tarifi. ARGUMENT için: subject ÜST 1/3'te, ALT 2/3 sakin/koyu.",
                        },
                    },
                    "required": ["index", "role", "overlay_text", "body_text", "scene_description"],
                },
            },
        },
        "required": ["rationale", "slides"],
    },
}


def _build_user_message(content: dict) -> str:
    """Notion satırından LLM input message'ı kur."""
    parts = []
    parts.append(f"Kaynak: {content.get('source', '?')} | Skor: {content.get('score', '?')}/10")
    parts.append(f"Başlık: {content.get('title', '')}")
    if content.get("tweet_text"):
        parts.append(f"\n--- X Tweet ---\n{content['tweet_text']}")
    if content.get("thread"):
        parts.append(f"\n--- X Thread ---\n{content['thread']}")
    if content.get("linkedin_text"):
        parts.append(f"\n--- LinkedIn (uzun-form) ---\n{content['linkedin_text']}")
    if content.get("source_url"):
        parts.append(f"\nKaynak URL: {content['source_url']}")
    parts.append(
        f"\nGörev: Bu içerikten Instagram carousel planı çıkar. "
        f"Slide sayısı: {settings.SLIDE_COUNT} (içerik kısaysa 5'e in, çok zenginse 9'a çık). "
        f"`plan_carousel` tool'unu çağır."
    )
    return "\n".join(parts)


def plan(content: dict) -> Optional[list[SlidePlan]]:
    """Notion content row'undan SlidePlan listesi üret."""
    if settings.LLM_PROVIDER != "anthropic":
        ops.error("Şimdilik sadece anthropic destekleniyor", message=settings.LLM_PROVIDER)
        return None

    client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
    user_msg = _build_user_message(content)

    try:
        response = client.messages.create(
            model=settings.WRITER_MODEL,
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            tools=[PLAN_TOOL],
            tool_choice={"type": "tool", "name": "plan_carousel"},
            messages=[{"role": "user", "content": user_msg}],
        )
    except Exception as e:
        ops.error("Anthropic plan exception", exception=e)
        return None

    # tool_use bloğunu yakala
    tool_input = None
    for block in response.content:
        if getattr(block, "type", None) == "tool_use" and getattr(block, "name", "") == "plan_carousel":
            tool_input = block.input
            break

    if not tool_input:
        ops.error("Plan tool_use bloğu yok", message=str(response.content)[:300])
        return None

    raw_slides = tool_input.get("slides", [])
    if not raw_slides:
        ops.error("Plan slides boş")
        return None

    total = len(raw_slides)
    plans: list[SlidePlan] = []
    for s in raw_slides:
        body = (s.get("body_text") or "").strip()
        # Em-dash yasak (memory)
        body = body.replace("—", "-")
        plans.append(SlidePlan(
            index=int(s.get("index") or len(plans) + 1),
            total=total,
            role=s.get("role") or SLIDE_ROLE.ARGUMENT,
            overlay_text=(s.get("overlay_text") or "").strip(),
            body_text=body,
            sub_text=(s.get("sub_text") or "").strip(),
            scene_description=(s.get("scene_description") or "").strip(),
            cta_handle=BRAND_MARK_TEXT,
        ))

    ops.success(f"Plan hazır: {total} slide", message=tool_input.get("rationale", "")[:200])
    return plans


def enrich_scene_for_kie(slide: SlidePlan) -> str:
    """Slide.scene_description'ı style guide ile zenginleştirip Kie prompt'una çevir."""
    parts = [slide.scene_description.strip(), "", SCENE_PHOTOREALISTIC_PREAMBLE, SCENE_COLOR_PALETTE_HINT]

    if slide.role == SLIDE_ROLE.ARGUMENT:
        # Argüman slide: alt 2/3 tamamen sakin (uzun body metni oraya basılacak)
        parts.append(
            "CRITICAL composition rule: place subject and main action ONLY in the UPPER THIRD "
            "of the frame. The LOWER TWO-THIRDS must be visually quiet, dark, atmospheric, "
            "almost empty (e.g. dark wall, soft ambient lighting, minimal depth, blank floor). "
            "A long paragraph of overlay text will be placed in the lower two-thirds — it must "
            "be highly readable. Do not place any objects or strong details in the bottom 66%."
        )
    elif slide.role == SLIDE_ROLE.HOOK:
        # Hook = scroll-stopping shock. Absurd / aggressive / freeze-frame action.
        parts.append(
            "CRITICAL HOOK directive: this is the SCROLL-STOPPING cover. The scene MUST be "
            "absurd, aggressive, dramatic — a movie-poster freeze-frame of an extreme moment "
            "(destruction, fire, throwing, punching, protest, chaos, flying debris). Generic "
            "portraits, calm office scenes, 'person looking at phone' are FORBIDDEN. The "
            "viewer's eye should lock in 0.5 seconds because something visually shocking is "
            "frozen mid-action. Cinematic, dramatic lighting, motion blur acceptable on "
            "secondary elements but the subject pose must be crisp and dramatic."
        )
        parts.append(SCENE_BOTTOM_THIRD_RULE)
    else:
        # CTA: bottom-third sakin yeter
        parts.append(SCENE_BOTTOM_THIRD_RULE)

    parts.extend(["", SCENE_NEGATIVE_PROMPT])
    return "\n".join(parts)
