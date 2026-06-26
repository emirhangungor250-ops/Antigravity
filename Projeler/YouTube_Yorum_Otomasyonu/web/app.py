# -*- coding: utf-8 -*-
"""Faz 2 onay servisi — maildeki 'Onayla ve Yayınla' butonu buraya gelir.

Akış:
  GET  /reply?t=<imzalı token>  -> taslağı DÜZENLENEBİLİR göster
  POST /reply/publish           -> YouTube'a yayınla + DB güncelle + corpus'a öğren
Güvenlik: HMAC imzalı + süreli token (mail_report.make_reply_url / verify_reply_token).
İç sayfa = koyu tema (CLAUDE.md kuralı).
"""
import html as _html
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse

from core import db as DB
from core import corpus as CORPUS
from core import mail_report
from core import youtube_client as YT
from core import llm

app = FastAPI(title="YouTube Yorum Onay")


def _page(title: str, body: str) -> str:
    return f"""<!DOCTYPE html><html lang="tr"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="dark"><title>{title}</title></head>
<body style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;
background:#0b1120;color:#e2e8f0;margin:0;padding:24px;">
<div style="max-width:620px;margin:0 auto;background:#1e293b;border:1px solid #334155;
border-radius:12px;padding:24px;">{body}</div></body></html>"""


@app.get("/health")
def health():
    return {"ok": True}


@app.get("/reply", response_class=HTMLResponse)
def reply_form(t: str = ""):
    cid = mail_report.verify_reply_token(t)
    if not cid:
        return HTMLResponse(_page("Geçersiz", "<h2>Bağlantı geçersiz ya da süresi dolmuş.</h2>"
                            "<p style='color:#94a3b8'>Mailden güncel bir bağlantıya tıkla.</p>"), status_code=400)
    try:
        row = DB.get_comment(cid)
    except Exception as e:
        return HTMLResponse(_page("Hata", f"<h2>Bir sorun oldu.</h2><p style='color:#94a3b8'>{_html.escape(str(e)[:160])}</p>"), status_code=502)
    if not row:
        return HTMLResponse(_page("Bulunamadı", "<h2>Yorum bulunamadı.</h2>"), status_code=404)
    if row.get("status") in ("approved", "auto_replied"):
        return HTMLResponse(_page("Yayınlandı", "<h2>Bu yoruma zaten cevap verildi. ✅</h2>"))

    draft = row.get("ai_draft") or ""
    comment = _html.escape(row.get("text", "")).replace("\n", "<br>")
    author = _html.escape(row.get("author", ""))
    vtitle = _html.escape(row.get("video_title") or "")
    conf = row.get("ai_confidence") or ""
    body = f"""
<div style="font-size:12px;color:#94a3b8;text-transform:uppercase;letter-spacing:1px;">Yorum cevabı · {conf} güven</div>
<div style="font-size:13px;color:#94a3b8;margin:6px 0;">📺 {vtitle}</div>
<div style="background:#0f172a;border:1px solid #334155;border-radius:8px;padding:12px;margin:10px 0;">
  <div style="font-size:12px;color:#94a3b8;margin-bottom:4px;">{author} yazdı:</div>
  <div style="font-size:15px;color:#f1f5f9;line-height:1.5;">{comment}</div></div>
<form method="post" action="/reply/publish">
  <input type="hidden" name="t" value="{_html.escape(t)}">
  <label style="font-size:13px;color:#94a3b8;">Cevabın (düzenleyebilirsin):</label>
  <textarea name="reply" rows="5" style="width:100%;box-sizing:border-box;margin-top:6px;
    background:#0f172a;color:#f1f5f9;border:1px solid #334155;border-radius:8px;padding:12px;
    font-size:15px;font-family:inherit;line-height:1.5;">{_html.escape(draft)}</textarea>
  <button type="submit" style="margin-top:14px;background:#16a34a;color:#fff;border:none;
    padding:12px 22px;border-radius:8px;font-size:15px;font-weight:600;cursor:pointer;">
    YouTube'da Yayınla</button>
</form>
<p style="font-size:12px;color:#64748b;margin-top:14px;">Yayınla'ya basınca cevap YouTube'da
senin adına görünür ve geri alınamaz.</p>"""
    return HTMLResponse(_page("Cevabı Onayla", body))


@app.post("/reply/publish", response_class=HTMLResponse)
def publish(t: str = Form(""), reply: str = Form("")):
    cid = mail_report.verify_reply_token(t)
    if not cid:
        return HTMLResponse(_page("Geçersiz", "<h2>Bağlantı geçersiz ya da süresi dolmuş.</h2>"), status_code=400)
    reply = (reply or "").strip()
    if not reply:
        return HTMLResponse(_page("Boş", "<h2>Cevap boş olamaz.</h2>"), status_code=400)
    try:
        row = DB.get_comment(cid)
    except Exception as e:
        return HTMLResponse(_page("Hata", f"<h2>Bir sorun oldu.</h2><p style='color:#94a3b8'>{_html.escape(str(e)[:160])}</p>"), status_code=502)
    if not row:
        return HTMLResponse(_page("Bulunamadı", "<h2>Yorum bulunamadı.</h2>"), status_code=404)
    if row.get("status") in ("approved", "auto_replied"):
        return HTMLResponse(_page("Zaten yayınlandı", "<h2>Bu yoruma zaten cevap verildi. ✅</h2>"))

    reply = llm._no_emdash(reply)
    try:
        YT.post_reply(cid, reply)
    except Exception as e:
        return HTMLResponse(_page("Hata", "<h2>Yayınlanamadı.</h2>"
                            f"<p style='color:#94a3b8'>{_html.escape(str(e)[:200])}</p>"), status_code=502)

    DB.update_comment(cid, {"status": "approved", "posted_reply": reply})
    # Öğrenme döngüsü: onayladığın final cevap yeni corpus örneği olur (ai_draft vs final = düzeltme sinyali)
    try:
        CORPUS.seed_pairs([{
            "comment_id": cid,
            "comment_text": row.get("text", ""),
            "reply_text": reply,
            "video_id": row.get("video_id"),
            "video_title": row.get("video_title"),
            "lang": row.get("lang"),
            "source": "approved",
            "ai_draft": row.get("ai_draft"),
        }])
    except Exception:
        pass

    return HTMLResponse(_page("Yayınlandı", "<h2>Cevabın yayınlandı. ✅</h2>"
        f"<div style='background:#0f172a;border:1px solid #334155;border-radius:8px;padding:12px;"
        f"margin-top:10px;color:#f1f5f9;line-height:1.5;'>{_html.escape(reply)}</div>"
        "<p style='color:#94a3b8;margin-top:10px;'>Bu sayfayı kapatabilirsin.</p>"))
