"""Koyu temali tek dosyalik seri kimlik karti (kimlik.html).

Repo ic-panel paleti: zemin #0b1120, panel #1e293b, kenar #334155,
baslik #f1f5f9, govde #e2e8f0, soluk #94a3b8.
"""
import html
import logging

from pipeline import state

log = logging.getLogger("IdentityCard")

_CSS = """
:root { color-scheme: dark; }
* { box-sizing: border-box; margin: 0; padding: 0; }
body { background: #0b1120; color: #e2e8f0; font-family: -apple-system, 'Segoe UI', Roboto, sans-serif;
       padding: 32px 20px; max-width: 1100px; margin: 0 auto; }
h1 { color: #f1f5f9; font-size: 30px; margin-bottom: 6px; }
h2 { color: #f1f5f9; font-size: 19px; margin: 36px 0 14px; border-bottom: 1px solid #334155; padding-bottom: 8px; }
.logline { color: #e2e8f0; font-size: 16px; margin-bottom: 10px; }
.muted { color: #94a3b8; font-size: 13px; }
.chips { margin-top: 10px; }
.chip { display: inline-block; background: #1e293b; border: 1px solid #334155; border-radius: 999px;
        padding: 3px 12px; margin: 0 6px 6px 0; font-size: 12px; color: #94a3b8; }
.grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(250px, 1fr)); gap: 16px; }
.card { background: #1e293b; border: 1px solid #334155; border-radius: 12px; padding: 16px; }
.card img { width: 100%; border-radius: 8px; border: 1px solid #334155; margin-bottom: 12px;
            aspect-ratio: 9/16; object-fit: cover; background: #0b1120; }
.card h3 { color: #f1f5f9; font-size: 16px; margin-bottom: 4px; }
.card p { font-size: 13px; margin-bottom: 8px; line-height: 1.45; }
.voice { background: #0b1120; border: 1px solid #334155; border-radius: 8px; padding: 10px; margin-top: 8px; }
.voice .preset { color: #f1f5f9; font-size: 12px; font-weight: 600; }
.voice .line { color: #94a3b8; font-size: 12px; font-style: italic; margin-top: 4px; }
.panel { background: #1e293b; border: 1px solid #334155; border-radius: 12px; padding: 18px; line-height: 1.6; font-size: 14px; }
ol.arc { margin-left: 22px; }
ol.arc li { margin-bottom: 8px; font-size: 14px; line-height: 1.5; }
"""


def _esc(value) -> str:
    return html.escape(str(value if value is not None else ""))


def _character_cards(bible: dict) -> str:
    cards = []
    for c in bible.get("characters", []):
        img = _esc(c.get("ref_image", {}).get("local_path", ""))
        voice = c.get("voice", {})
        cards.append(f"""
<div class="card">
  <img src="{img}" alt="{_esc(c.get('name'))}">
  <h3>{_esc(c.get('name'))} <span class="muted">({_esc(c.get('age'))})</span></h3>
  <p class="muted">{_esc(c.get('role'))}</p>
  <p>{_esc(c.get('personality'))}</p>
  <p class="muted">{_esc(c.get('speaking_style'))}</p>
  <div class="voice">
    <div class="preset">Ses: {_esc(voice.get('preset'))}</div>
    <div class="line">&ldquo;{_esc(voice.get('example_dialogue'))}&rdquo;</div>
  </div>
</div>""")
    return "\n".join(cards)


def _plate_cards(items: list, extra_key: str) -> str:
    cards = []
    for item in items:
        img = _esc(item.get("ref_image", {}).get("local_path", ""))
        extra = _esc(item.get(extra_key, ""))
        cards.append(f"""
<div class="card">
  <img src="{img}" alt="{_esc(item.get('name_tr'))}">
  <h3>{_esc(item.get('name_tr'))}</h3>
  <p class="muted">{extra}</p>
</div>""")
    return "\n".join(cards)


def generate_identity_card(bible: dict, slug: str) -> str:
    series = bible.get("series", {})
    style = bible.get("style", {})
    arc = bible.get("series_arc", {})
    narrator = bible.get("narrator", {})

    tone_chips = "".join(f'<span class="chip">{_esc(t)}</span>' for t in series.get("tone", []))
    arc_items = "".join(f"<li>{_esc(s)}</li>" for s in arc.get("episode_seeds_tr", []))
    narrator_html = ""
    if narrator.get("enabled"):
        narrator_html = (
            f'<p class="muted" style="margin-top:10px">Anlatici: {_esc(narrator.get("preset"))} '
            f'&mdash; &ldquo;{_esc(narrator.get("example_dialogue"))}&rdquo;</p>'
        )

    board_path = _esc(style.get("style_board", {}).get("local_path", ""))
    props_section = ""
    if bible.get("props"):
        props_section = (
            "<h2>Aksesuarlar</h2>\n<div class=\"grid\">"
            + _plate_cards(bible["props"], "story_role")
            + "</div>"
        )

    doc = f"""<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="utf-8">
<meta name="color-scheme" content="dark">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{_esc(series.get('title_tr'))} — Seri Kimlik Karti</title>
<style>{_CSS}</style>
</head>
<body>
<h1>{_esc(series.get('title_tr'))}</h1>
<p class="logline">{_esc(series.get('logline_tr'))}</p>
<p class="muted">Merkezi soru: {_esc(arc.get('central_question_tr'))}</p>
<div class="chips">{tone_chips}</div>
{narrator_html}

<h2>Karakterler</h2>
<div class="grid">{_character_cards(bible)}</div>

<h2>Ortamlar</h2>
<div class="grid">{_plate_cards(bible.get('environments', []), 'lighting_signature')}</div>

{props_section}

<h2>Sanat Stili</h2>
<div class="grid">
  <div class="card"><img src="{board_path}" alt="Stil panosu"><h3>Stil Panosu</h3></div>
  <div class="panel" style="grid-column: span 2;">{_esc(style.get('style_paragraph'))}</div>
</div>

<h2>8 Bolumluk Seri Arki</h2>
<div class="panel"><ol class="arc">{arc_items}</ol></div>

<p class="muted" style="margin-top:28px">Bu kart otomatik uretildi &mdash; Shorts Dizi Fabrikasi · seri: {_esc(slug)}</p>
</body>
</html>"""

    dest = state.series_dir(slug) / "kimlik.html"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(doc, encoding="utf-8")
    log.info(f"kimlik.html yazildi: {dest}")
    return str(dest)
