# -*- coding: utf-8 -*-
"""Çok hesaplı Gmail operasyonları (scope-aware).

Her token'ı KENDİ scope'uyla yükler (hesapların scope'ları farklı olabilir; tek
bir merkezi scope listesi dayatmak refresh'i patlatabilir). Lokalde JSON dosyası
(`oauth/` klasörü), production'da (Railway) env var olarak okunur.

Token üretimi: her Gmail hesabı için Google Cloud Console'dan OAuth client oluştur,
`gmail.modify` + `gmail.send` scope'larıyla yetkilendir, çıkan token JSON'unu ya
`oauth/<dosya>.json` olarak kaydet ya da ilgili env var'a (tek satır JSON) koy.
"""
import os
import re
import json
import base64
import time
import html as _htmlmod
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header, decode_header, make_header
from email.utils import formataddr, parseaddr

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

import config

# Lokal OAuth token dosyalarının arandığı klasör (proje köküne göreli).
OAUTH_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "oauth")

TOKEN_FILES = {
    "inbox_primary": "gmail-primary-token.json",
    "manager": "gmail-manager-token.json",
    "inbox_personal": "gmail-personal-token.json",
}
TOKEN_ENV_VARS = {
    "inbox_primary": "GOOGLE_PRIMARY_TOKEN_JSON",
    "manager": "GOOGLE_MANAGER_TOKEN_JSON",
    "inbox_personal": "GOOGLE_PERSONAL_TOKEN_JSON",
}
_SERVICE_CACHE = {}


def _load_token_data(account):
    env_var = TOKEN_ENV_VARS[account]
    if os.environ.get(env_var):
        return json.loads(os.environ[env_var]), None
    path = os.path.join(OAUTH_DIR, TOKEN_FILES[account])
    if os.path.exists(path):
        return json.load(open(path)), path
    raise FileNotFoundError(f"{account}: token ne env ({env_var}) ne dosya ({path})")


def _creds(account):
    data, path = _load_token_data(account)
    scopes = data.get("scopes") or ["https://www.googleapis.com/auth/gmail.modify"]
    creds = Credentials.from_authorized_user_info(data, scopes)
    if not creds.valid:
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
            if path:  # yenilenen token'ı dosyaya yaz (lokal)
                data["token"] = creds.token
                data["expiry"] = creds.expiry.isoformat() + "Z" if creds.expiry else None
                json.dump(data, open(path, "w"), indent=2)
        else:
            raise RuntimeError(f"{account}: token geçersiz, yenilenemiyor")
    return creds


def service(account):
    if account not in _SERVICE_CACHE:
        _SERVICE_CACHE[account] = build("gmail", "v1", credentials=_creds(account),
                                        cache_discovery=False)
    return _SERVICE_CACHE[account]


# ── header / body yardımcıları ────────────────────────────
def hdr(msg, name):
    for h in msg.get("payload", {}).get("headers", []):
        if h["name"].lower() == name.lower():
            return h["value"]
    return ""


def _b64d(data):
    # Gmail web-safe base64'ü padding'siz dönebilir; strict decode 'Incorrect padding' ile
    # patlayıp thread'i sessizce düşürmesin diye eksik '='leri tamamla.
    b = (data or "").encode("utf-8")
    return base64.urlsafe_b64decode(b + b"=" * (-len(b) % 4)).decode("utf-8", "replace")


def extract_body(payload):
    plain, html = None, None

    def walk(p):
        nonlocal plain, html
        mt = p.get("mimeType", "")
        body = p.get("body", {})
        if mt == "text/plain" and body.get("data") and plain is None:
            plain = _b64d(body["data"])
        elif mt == "text/html" and body.get("data") and html is None:
            html = _b64d(body["data"])
        for part in p.get("parts", []) or []:
            walk(part)

    walk(payload)
    if plain:
        return plain
    if html:
        import html as _h
        txt = re.sub(r"<br\s*/?>", "\n", html)
        txt = re.sub(r"</p>", "\n\n", txt)
        txt = re.sub(r"<[^>]+>", "", txt)
        return _h.unescape(txt)
    return ""


def _clip_quotes(text):
    out = []
    for ln in text.split("\n"):
        s = ln.strip()
        if re.match(r"^(On .+ wrote:|.+ tarihinde .+ yazdı:|-{3,} ?Forwarded|-{3,} ?Yönlendirilen|From: .+@)", s):
            break
        if s.startswith(">"):
            continue
        out.append(ln)
    return "\n".join(out).strip()


def _decode_hdr(v):
    """RFC2047 encoded-word'u (=?UTF-8?...?=) okunur metne çevir; alıntı atıf satırında
    markanın Türkçe/yabancı adı düzgün gözüksün, ham '=?...?=' gibi değil."""
    try:
        return str(make_header(decode_header(v))) if v else (v or "")
    except Exception:
        return v or ""


_IMG_TAG_RE = re.compile(r"\[image:[^\]]*\]")


def _clean_quote_text(text):
    """Alıntı gövdesini sadeleştir: '[image: ...]' artıkları (HTML imzalı markaların düz-metin
    alternatifinden gelir), satır-sonu boşlukları ve 3+ ardışık boş satır. Alıntı çöp görünmesin."""
    t = _IMG_TAG_RE.sub("", text or "")
    t = "\n".join(ln.rstrip() for ln in t.split("\n"))
    return re.sub(r"\n{3,}", "\n\n", t).strip()


def quote_block(msg, language="tr", limit=4000):
    """Bir mesajı standart alıntı bloğuna çevirir (cevabın altına eklenir).
    NEDEN: CC'lenen kişi (Stage 1'de yönetici, Stage 2'de gönderen) markanın orijinal
    mailini ASLA göremez -> o mail karşının kutusunda yok, CC sadece tek bir maili
    (bizim cevabı) taşır. Cevap gövdesine alıntı koymazsak bağlam tamamen kaybolur.
    Programla kurulan mailde Gmail'in 'Yanıtla' alıntısı otomatik yapışmaz; biz koyarız."""
    frm = _decode_hdr(hdr(msg, "From"))
    date = _decode_hdr(hdr(msg, "Date"))
    body = _clean_quote_text(_clip_quotes(extract_body(msg["payload"])))[:limit].strip()
    header = (f"{date} tarihinde {frm} yazdı:" if language == "tr"
              else f"On {date}, {frm} wrote:")
    quoted = "\n".join("> " + ln for ln in body.split("\n"))
    return f"{header}\n{quoted}"


EMAIL_RE = re.compile(r"[\w.\-+]+@[\w.\-]+\.[A-Za-z]{2,}")


def emails_in(s):
    return EMAIL_RE.findall(s or "")


def is_internal(email):
    el = (email or "").lower()
    return any(x in el for x in config.INTERNAL_ADDRESSES)


def counterparty(*header_values):
    """Thread'deki dış (marka) adresini bul."""
    for hv in header_values:
        for e in emails_in(hv):
            if not is_internal(e):
                return e.lower()
    return ""


# ── arama / thread okuma ──────────────────────────────────
def search_threads(account, query, maxn=25):
    g = service(account)
    res = g.users().messages().list(userId="me", q=query, maxResults=maxn).execute()
    seen = []
    tids = set()
    for m in res.get("messages", []):
        full = g.users().messages().get(
            userId="me", id=m["id"], format="metadata",
            metadataHeaders=["From", "To", "Cc", "Subject", "Date"]).execute()
        tid = full["threadId"]
        if tid in tids:
            continue
        tids.add(tid)
        seen.append(full)
    return seen


def get_thread(account, tid):
    g = service(account)
    return g.users().threads().get(userId="me", id=tid, format="full").execute()


def thread_text(account, tid, clip=True, limit=6000):
    """Thread'in okunabilir metni (en yeni mesajlar dahil), LLM'e verilmek üzere."""
    th = get_thread(account, tid)
    parts = []
    for m in th["messages"]:
        body = extract_body(m["payload"])
        if clip:
            body = _clip_quotes(body)
        parts.append(
            f"--- [{hdr(m,'Date')}] FROM: {hdr(m,'From')} TO: {hdr(m,'To')} CC: {hdr(m,'Cc')}\n"
            f"SUBJECT: {hdr(m,'Subject')}\n{body.strip()}"
        )
    joined = "\n\n".join(parts)
    if len(joined) <= limit:
        return joined, th
    # Limit aşılırsa EN YENİ mesajı TAM koru (qualify en güncel teklifi/vazgeçmeyi görmeli),
    # kalan bütçeyi en eski bağlamdan doldur. Eskiden baştan kesiliyordu -> en yeni mesaj düşüyordu.
    last = parts[-1]
    if len(last) >= limit:
        return last[-limit:], th
    head = joined[: max(0, limit - len(last) - 5)]
    return f"{head}\n…\n{last}", th


def thread_messages(account, tid):
    return get_thread(account, tid)["messages"]


def rfc822_msgid(account, gmail_msg_id):
    g = service(account)
    meta = g.users().messages().get(userId="me", id=gmail_msg_id, format="metadata",
                                    metadataHeaders=["Message-Id"]).execute()
    return hdr(meta, "Message-Id")


def find_by_rfc822(account, msgid, tries=12, delay=2.0):
    g = service(account)
    q = f"rfc822msgid:{msgid.strip('<>').strip()}"
    for _ in range(tries):
        res = g.users().messages().list(userId="me", q=q).execute()
        if res.get("messages"):
            mid = res["messages"][0]["id"]
            return g.users().messages().get(userId="me", id=mid, format="metadata",
                    metadataHeaders=["Message-Id", "Subject", "From", "To", "Cc"]).execute()
        time.sleep(delay)
    return None


# ── etiket (idempotency) ──────────────────────────────────
def _label_id(account, name):
    g = service(account)
    for lb in g.users().labels().list(userId="me").execute().get("labels", []):
        if lb["name"] == name:
            return lb["id"]
    created = g.users().labels().create(userId="me", body={
        "name": name, "labelListVisibility": "labelShow",
        "messageListVisibility": "show"}).execute()
    return created["id"]


def add_label(account, tid, name):
    if config.DRY_RUN:
        return
    g = service(account)
    g.users().threads().modify(userId="me", id=tid,
                               body={"addLabelIds": [_label_id(account, name)]}).execute()


def thread_has_label(thread_obj, label_id):
    for m in thread_obj.get("messages", []):
        if label_id in m.get("labelIds", []):
            return True
    return False


# ── MIME / gönderim / taslak ──────────────────────────────
_URL_RE = re.compile(r"(https?://[^\s<>()\[\]]+)")
_URL_TRAIL = ".,;:!?’'\")]}>"   # URL'in parçası SAYILMAYAN sondaki noktalama


def _html_line(ln):
    """Satırı NORMAL render'a hazırla: URL'leri ham metinde yer-tutucuyla yakala (escape ÖNCESİ -> '<>()'
    dışlaması doğru çalışır), sondaki noktalamayı linkten ayır, kalanı HTML-escape et, sonra yer-tutucuyu
    tıklanır <a> ile değiştir. Böylece alıntıdaki '<https://...>' ve cümle sonu 'url.' link'i BOZULMAZ."""
    ln = (ln or "").replace("\x00", "")   # yer-tutucu sentinel'i (\x00) ham metinle çakışmasın
    placeholders = {}

    def _stash(m):
        url, trail = m.group(1), ""
        while url and url[-1] in _URL_TRAIL:   # cümle sonu noktalaması href'e girmesin (404 önler)
            trail = url[-1] + trail
            url = url[:-1]
        key = f"\x00U{len(placeholders)}\x00"
        placeholders[key] = url
        return key + trail

    escaped = _htmlmod.escape(_URL_RE.sub(_stash, ln))
    for key, url in placeholders.items():
        safe = _htmlmod.escape(url, quote=True)
        escaped = escaped.replace(key, f'<a href="{safe}">{safe}</a>')
    return escaped


def _text_to_html(text):
    """Düz-metin gövdeyi (selam + mesaj + '> ' alıntı bloğu) NORMAL görünen HTML'e çevir:
    linkler tıklanır, '> ' alıntısı tek seviye <blockquote> olur (Gmail'in kendi alıntısı gibi).
    NEDEN: yalnız text/plain göndermek HTML thread'inde 'normal mail gibi görünmez'
    (ham '>' yığını, tıklanmaz linkler). Artık multipart/alternative'in HTML part'ı bunu kurar."""
    out, quote = [], []

    def _flush():
        if quote:
            out.append('<blockquote style="margin:0 0 0 0.8ex;border-left:2px solid #ccc;'
                       'padding-left:1ex;color:#666">' + "<br>\n".join(quote) + "</blockquote>")
            quote.clear()

    for ln in (text or "").split("\n"):
        if ln.lstrip().startswith(">"):
            inner = re.sub(r"^\s*(>\s?)+", "", ln)            # iç içe '>' işaretlerini tek seviyeye indir
            quote.append(_html_line(inner) or "&nbsp;")
        else:
            _flush()
            out.append((_html_line(ln) + "<br>") if ln.strip() else "<br>")
    _flush()
    return ('<div style="font-family:Arial,Helvetica,sans-serif;font-size:14px;'
            'line-height:1.5;color:#222">' + "\n".join(out) + "</div>")


def build_raw(from_h, to_h, subject, body, cc_h=None, in_reply_to=None, references=None):
    # multipart/alternative: text/plain (her istemci) + text/html (normal mail görünümü).
    # Eskiden yalnız text/plain gidiyordu -> HTML thread'inde ham/garip görünüyordu (alıntı '>' yığını,
    # tıklanmaz linkler). HTML part Gmail'de normal zengin mail gibi render olur.
    msg = MIMEMultipart("alternative")
    msg.attach(MIMEText(body, "plain", "utf-8"))
    msg.attach(MIMEText(_text_to_html(body), "html", "utf-8"))   # son part = en zengin => istemci bunu seçer
    # From display adı Türkçe harf içerebilir (ör. 'Özçelik') -> compat32 TÜM header'ı (adresi de)
    # encoded-word'e çevirir ve adres okunamaz olur. formataddr+charset: adı RFC2047, adresi çıplak bırakır.
    _name, _addr = parseaddr(from_h)
    msg["From"] = formataddr((_name, _addr), charset="utf-8") if (_name and _addr) else from_h
    msg["To"] = to_h
    if cc_h:
        msg["Cc"] = cc_h
    msg["Subject"] = str(Header(subject, "utf-8"))
    if in_reply_to:
        msg["In-Reply-To"] = in_reply_to
    if references:
        msg["References"] = references
    return base64.urlsafe_b64encode(msg.as_bytes()).decode()


def send(account, raw, thread_id=None):
    g = service(account)
    body = {"raw": raw}
    if thread_id:
        body["threadId"] = thread_id
    sent = g.users().messages().send(userId="me", body=body).execute()
    return sent


def create_draft(account, raw, thread_id=None):
    g = service(account)
    msg = {"raw": raw}
    if thread_id:
        msg["threadId"] = thread_id
    return g.users().drafts().create(userId="me", body={"message": msg}).execute()


def display_from(account, name):
    return f"{name} <{config.ADDR[account]}>"
