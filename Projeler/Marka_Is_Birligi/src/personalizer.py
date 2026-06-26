#!/usr/bin/env python3
"""
Personalizer modülü — OpenAI GPT-4.1 ile marka bazlı email kişiselleştirme.

İlk outreach ve follow-up mailler için markaya özel, doğal Türkçe/İngilizce
email metinleri üretir.

Outreach gönderen kişinin tüm bilgileri config/creator_profile.json'dan
okunur — bu dosyaya KENDİ profilini yaz.
"""

import json
import os
import re
import requests

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# ── Creator profili — config/creator_profile.json'dan yüklenir ─────────────
def _load_creator_profile():
    path = os.path.join(BASE_DIR, "config", "creator_profile.json")
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"[PERSONALIZER] ⚠️ creator_profile.json okunamadı ({e}); minimal default kullanılıyor.")
        return {
            "name": "",
            "tagline": "",
            "email": "",
            "website": "",
            "instagram": "",
            "tiktok": "",
            "youtube": "",
            "total_views": "",
            "country": "",
            "recent_collabs": "",
            "top_results": [],
        }


CREATOR_PROFILE = _load_creator_profile()


def _build_signature_text(p):
    lines = [f"\n—\n{p.get('name','')}", p.get("tagline", "")]
    if p.get("email"):
        lines.append(f"📧 {p['email']}")
    if p.get("website"):
        lines.append(f"🌐 {p['website']}")
    if p.get("instagram"):
        lines.append(f"📸 {p['instagram']}")
    if p.get("youtube"):
        lines.append(f"▶️ {p['youtube']}")
    if p.get("tiktok"):
        lines.append(f"🎵 {p['tiktok']}")
    return "\n".join(lines) + "\n"


def _build_signature_html(p):
    website = p.get("website", "")
    website_link = (
        f'  <a href="https://{website}" '
        'style="color: #555; text-decoration: none;">'
        f'{website}</a>\n'
        if website else ""
    )
    return (
        '\n<br><br>\n'
        '<p style="font-size: 13px; color: #555; border-top: 1px solid #ddd; '
        'padding-top: 10px; margin-top: 16px;">\n'
        f'  <strong>{p.get("name","")}</strong><br>\n'
        f'  {p.get("tagline","")}<br>\n'
        f'{website_link}'
        '</p>\n'
    )


EMAIL_SIGNATURE_TEXT = _build_signature_text(CREATOR_PROFILE)
EMAIL_SIGNATURE_HTML = _build_signature_html(CREATOR_PROFILE)

# Fallback kullanım istatistikleri
_fallback_count = 0
_total_generated = 0


def _get_openai_key():
    """OpenAI API key'ini al (Railway env veya master.env)."""
    key = os.environ.get("OPENAI_API_KEY")
    if key:
        return key
    try:
        from env_loader import get_env as _ge
        return _ge("OPENAI_API_KEY") or None
    except ImportError:
        return None


def _call_openai(prompt, system_prompt=None, model="gpt-4.1-nano", json_mode=False):
    """OpenAI API çağrısı yapar.

    `json_mode=True` ise `response_format={"type":"json_object"}` set edilir —
    model garanti JSON döner, parse fallback'e ihtiyaç azalır.
    """
    api_key = _get_openai_key()
    if not api_key:
        print("[PERSONALIZER] ⚠️ OpenAI API key bulunamadı, template kullanılacak.")
        return None

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 800,
    }
    if json_mode:
        payload["response_format"] = {"type": "json_object"}

    try:
        resp = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print(f"[PERSONALIZER] OpenAI hatası: {e}")
        return None


# ═══════════════════════════════════════════════════════════════════════════
# İLK OUTREACH
# ═══════════════════════════════════════════════════════════════════════════

_CREATOR_NAME = CREATOR_PROFILE.get("name") or "the creator"
_CREATOR_VIEWS = CREATOR_PROFILE.get("total_views") or "a large"
_CREATOR_COUNTRY = CREATOR_PROFILE.get("country") or "their country"

OUTREACH_SYSTEM_PROMPT = f"""You are writing a cold outreach email from {_CREATOR_NAME}, a content creator
with {_CREATOR_VIEWS} organic views in {_CREATOR_COUNTRY}, to a brand for a potential collaboration.

Rules:
- Write in English (most brands are global)
- DO NOT write a single thick block of text. You MUST format the email with proper line breaks (`\\n`) and paragraphs.
- Use bullet points for listing platforms (Instagram, TikTok, YouTube) and concrete metrics.
- Format the email very similar to this structure:
  Hi [Brand Name] team,
  I'm [Creator], a content creator... [hook]
  My profiles:
  - Instagram ...
  I've collaborated with brands like [Brand names]...
  - [X] views with [Brand]
  I have a viral campaign idea that could make [Your Brand] stand out 🚀
  If you're interested...
- Emojis are ALLOWED and ENCOURAGED in the subject and body to make it stand out (e.g. 🥺, 😢, 🚀).
- Subject line: Creative, curiosity-driving. Max 60 chars.
- `body_html` MUST use `<p>`, `<br>`, `<ul>`, `<li>` tags so it renders beautifully in email clients.
- `body_text` must use `\\n` for line breaks and `-` for lists.
- Be specific about the brand's product/niche!
- End with a low-pressure CTA.

Output format (JSON):
{{"subject": "...", "body_text": "...", "body_html": "..."}}
"""

def generate_outreach_email(brand_info):
    """
    Markaya özel outreach emaili üretir.

    Args:
        brand_info: dict with marka_adi, instagram_handle, website, sirket_aciklamasi

    Returns:
        dict: {subject, body_text, body_html} or fallback template
    """
    brand_name = brand_info.get("marka_adi", "Brand")
    handle = brand_info.get("instagram_handle", "")
    website = brand_info.get("website", "")
    description = brand_info.get("sirket_aciklamasi", "their product")
    collab_context = brand_info.get("caption_samples", [])

    top_results = CREATOR_PROFILE.get("top_results", [])
    results_summary = ", ".join(
        f"{r.get('brand','')} ({r.get('views','')})" for r in top_results
    ) or "(profil dosyasına ekle)"

    prompt = f"""Write an outreach email to {brand_name} (@{handle}).

Brand info:
- Website: {website}
- Description: {description}
- They work with influencers (found via competitor analysis)
- Sample captions mentioning them: {json.dumps(collab_context[:2], ensure_ascii=False)}

Creator's profile:
- {_CREATOR_VIEWS} organic views across Instagram/TikTok/YouTube in {_CREATOR_COUNTRY}
- Top results: {results_summary}
- Recent collaborations: {CREATOR_PROFILE.get('recent_collabs','')}
- Links: {json.dumps(top_results, ensure_ascii=False)}

Write a personalized email that references what {brand_name} does specifically."""

    global _total_generated, _fallback_count
    _total_generated += 1

    result = _call_openai(prompt, OUTREACH_SYSTEM_PROMPT, json_mode=True)

    if result:
        parsed = _safe_parse_json(result)
        if parsed and "subject" in parsed:
            # Signature ekle
            parsed = _append_signature(parsed)
            return parsed

    # Fallback template
    _fallback_count += 1
    print(f"  ⚠️ GPT parse başarısız, fallback kullanılıyor ({_fallback_count}/{_total_generated} toplam fallback)")
    return _fallback_outreach(brand_name, handle)


def _safe_parse_json(text):
    """GPT çıktısından JSON parse etmeyi dener, regex fallback ile."""
    # 1. Direk parse
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        import logging
        logging.getLogger(__name__).warning("Fallback: JSON decode hatası (1)", exc_info=e)

    # 2. ```json ... ``` bloğunu çıkar
    match = re.search(r'```(?:json)?\s*\n?(\{.*?\})\s*```', text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError as e:
            import logging
            logging.getLogger(__name__).warning("Fallback: JSON decode hatası (2)", exc_info=e)

    # 3. İlk { ... } bloğunu bul
    match = re.search(r'(\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\})', text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError as e:
            import logging
            logging.getLogger(__name__).warning("Fallback: JSON decode hatası (3)", exc_info=e)

    return None


def _append_signature(email_dict):
    """Email dict'ine profesyonel signature ekler."""
    if "body_text" in email_dict:
        email_dict["body_text"] = email_dict["body_text"].rstrip() + EMAIL_SIGNATURE_TEXT
    if "body_html" in email_dict:
        email_dict["body_html"] = email_dict["body_html"].rstrip() + EMAIL_SIGNATURE_HTML
    return email_dict


def _fallback_outreach(brand_name, handle):
    """OpenAI çalışmazsa kullanılacak şablon."""
    first_name = (CREATOR_PROFILE.get("name") or "").split(" ")[0] or "there"
    top_results = CREATOR_PROFILE.get("top_results", [])
    collabs = CREATOR_PROFILE.get("recent_collabs", "")

    subject = f"A collaboration idea for {brand_name} 🚀"

    results = "\n".join(
        f"- {r.get('views','')} views with {r.get('brand','')}"
        for r in top_results
    )
    results_html = "".join(
        f"<li><strong>{r.get('views','')} views</strong> with {r.get('brand','')}</li>"
        for r in top_results
    )
    collabs_line = (
        f"I’ve collaborated with brands like {collabs}.\n\n" if collabs else ""
    )
    collabs_line_html = (
        f"<p>I’ve collaborated with brands like {collabs}.</p>\n" if collabs else ""
    )

    body_text = f"""Hi {brand_name} team,

I’m {first_name}, a content creator focused on tech and digital tools. My videos have reached over {_CREATOR_VIEWS} organic views in {_CREATOR_COUNTRY}.

My profiles:
- Instagram
- TikTok
- YouTube

{collabs_line}{results}

I have a viral campaign idea that could make {brand_name} stand out 🚀

If you’re interested, just reply to this email. I’d love to share the details with you!

Best,
{first_name}
{EMAIL_SIGNATURE_TEXT}"""

    body_html = f"""<p>Hi {brand_name} team,</p>

<p>I’m {first_name}, a content creator focused on tech and digital tools. My videos have reached over <strong>{_CREATOR_VIEWS} organic views</strong> in {_CREATOR_COUNTRY}.</p>

<p>My profiles:</p>
<ul>
  <li><a href="{CREATOR_PROFILE.get('instagram','#')}">Instagram</a></li>
  <li><a href="{CREATOR_PROFILE.get('tiktok','#')}">TikTok</a></li>
  <li><a href="{CREATOR_PROFILE.get('youtube','#')}">YouTube</a></li>
</ul>

{collabs_line_html}<ul>
{results_html}
</ul>

<p>I have a viral campaign idea that could make <strong>{brand_name}</strong> stand out 🚀</p>

<p>If you’re interested, just reply to this email. I’d love to share the details with you!</p>

<p>Best,<br>{first_name}</p>
{EMAIL_SIGNATURE_HTML}"""

    return {"subject": subject, "body_text": body_text, "body_html": body_html}


# ═══════════════════════════════════════════════════════════════════════════
# FOLLOW-UP (Seçenek A — Web + Sosyal Medya Analizi)
# ═══════════════════════════════════════════════════════════════════════════

FOLLOWUP_SYSTEM_PROMPT = f"""You are writing a follow-up email for {_CREATOR_NAME}'s brand collaboration outreach.
This email must be a REPLY to a previous email that got no response.

Rules:
- Keep it VERY SHORT — max 80 words
- Reference something SPECIFIC about the brand (from the context provided)
- Add NEW VALUE — something not in the first email (new result, new idea, new angle)
- Tone: Casual, not pushy. Like bumping a message to a friend.
- Do NOT repeat the full pitch from the first email
- Do NOT apologize for following up
- End with a simple question or soft CTA
- Write in English

Output format (JSON):
{{"body_text": "...", "body_html": "..."}}
"""


def generate_followup_email(brand_info, brand_context=None):
    """
    Follow-up emaili üretir. Markaya özel kişiselleştirme yapar.

    Args:
        brand_info: dict with marka_adi, instagram_handle, website etc.
        brand_context: dict with recent_posts, website_info (from research)

    Returns:
        dict: {body_text, body_html}
    """
    brand_name = brand_info.get("marka_adi", "Brand")
    handle = brand_info.get("instagram_handle", "")
    website = brand_info.get("website", "")

    context_str = ""
    if brand_context:
        if brand_context.get("recent_posts"):
            context_str += f"\nRecent Instagram posts: {json.dumps(brand_context['recent_posts'][:3], ensure_ascii=False)}"
        if brand_context.get("website_summary"):
            context_str += f"\nWebsite summary: {brand_context['website_summary']}"

    top_results = CREATOR_PROFILE.get("top_results", [])
    latest_result = (
        f"{top_results[0].get('brand','')} content now at {top_results[0].get('views','')} views."
        if top_results else "a recent campaign performed well."
    )

    prompt = f"""Write a follow-up email to {brand_name} (@{handle}).

Previous email was a collaboration pitch sent 1 week ago with no reply.

Brand context:{context_str if context_str else " No additional context available."}
Brand website: {website}

Creator's latest highlight: {latest_result}

Write a short, specific follow-up that gives them a reason to reply NOW."""

    result = _call_openai(prompt, FOLLOWUP_SYSTEM_PROMPT, json_mode=True)

    if result:
        parsed = _safe_parse_json(result)
        if parsed and "body_text" in parsed:
            parsed = _append_signature(parsed)
            return parsed

    # Fallback follow-up
    return _fallback_followup(brand_name)


def _fallback_followup(brand_name):
    """Fallback follow-up template."""
    body_text = f"""Hi again,

Quick follow-up on my previous email — I recently wrapped up a campaign that generated great engagement.

I'd love to create something similar for {brand_name}. Would you be open to a quick chat this week?
{EMAIL_SIGNATURE_TEXT}"""

    body_html = f"""<p>Hi again,</p>

<p>Quick follow-up on my previous email — I recently wrapped up a campaign that generated great engagement.</p>

<p>I'd love to create something similar for <strong>{brand_name}</strong>. Would you be open to a quick chat this week?</p>
{EMAIL_SIGNATURE_HTML}"""

    return {"body_text": body_text, "body_html": body_html}


def research_brand_for_followup(brand_info):
    """Follow-up kişiselleştirmesi için markanın son aktivitelerini araştırır.

    Instagram son paylaşımları için src/scraper.scrape_profile_posts'u
    reuse eder (token rotasyonu + tek noktada Apify config). Web özeti
    için OpenAI'a kısa prompt atar.

    Returns:
        dict: {recent_posts, website_summary}
    """
    from src.scraper import scrape_profile_posts

    handle = brand_info.get("instagram_handle", "")
    website = brand_info.get("website", "")
    context = {"recent_posts": [], "website_summary": ""}

    if handle:
        print(f"  📱 @{handle} son paylaşımları çekiliyor...")
        posts = scrape_profile_posts(handle, limit=5)
        context["recent_posts"] = [
            {"caption": (p.get("caption") or "")[:150], "likes": p.get("likes_count", 0)}
            for p in posts
        ]
        if posts:
            print(f"  ✅ {len(posts)} paylaşım bulundu.")

    if website:
        summary_prompt = (
            f"Visit {website} mentally and describe in 1 sentence what this company does. "
            "Be specific about their product."
        )
        summary = _call_openai(summary_prompt)
        if summary:
            context["website_summary"] = summary

    return context


if __name__ == "__main__":
    # Test outreach
    test_brand = {
        "marka_adi": "Test AI",
        "instagram_handle": "test_ai",
        "website": "https://test.ai",
        "sirket_aciklamasi": "AI testing tool",
    }
    result = generate_outreach_email(test_brand)
    print(json.dumps(result, indent=2, ensure_ascii=False))
