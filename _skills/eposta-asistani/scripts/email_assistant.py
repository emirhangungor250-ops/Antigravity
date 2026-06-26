"""
Antigravity — E-Posta Asistanı
================================
Gmail'deki okunmamış mailleri okur, AI ile analiz eder:
- Promosyon/gereksiz → okundu işaretler
- Yanıt gereken → taslak yanıt oluşturur

Kullanım:
    python email_assistant.py                    # Normal çalışma
    python email_assistant.py --dry-run          # Test modu (değişiklik yapmaz)
    python email_assistant.py --max-emails 10    # Maksimum 10 mail işle
    python email_assistant.py --account ikincil  # İkincil hesap
"""

import os
import sys
import json
import base64
import argparse
import re
from datetime import datetime
from email.mime.text import MIMEText
from html.parser import HTMLParser
import email.utils

# Windows konsolunda emoji yazdırırken alınan hatayı önlemek için:
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# ── Path Setup ──────────────────────────────────────────────
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_SKILL_DIR = os.path.dirname(_SCRIPT_DIR)
_ANTIGRAVITY_ROOT = os.path.abspath(os.path.join(_SKILL_DIR, "..", ".."))

# Merkezi OAuth modülü
sys.path.insert(0, os.path.join(_ANTIGRAVITY_ROOT, "_knowledge", "credentials", "oauth"))
from google_auth import get_gmail_service

# master.env'den API key yükle
_MASTER_ENV = os.path.join(_ANTIGRAVITY_ROOT, "_knowledge", "credentials", "master.env")


def load_env():
    """master.env'den environment değişkenlerini yükler."""
    env = {}
    if os.path.exists(_MASTER_ENV):
        with open(_MASTER_ENV, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, val = line.split("=", 1)
                    env[key.strip()] = val.strip().strip('"').strip("'")
    return env


# ── HTML Strip Utility ──────────────────────────────────────
class HTMLStripper(HTMLParser):
    """HTML'den plain text çıkaran parser."""

    def __init__(self):
        super().__init__()
        self.result = []
        self._skip = False

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style"):
            self._skip = True

    def handle_endtag(self, tag):
        if tag in ("script", "style"):
            self._skip = False

    def handle_data(self, data):
        if not self._skip:
            self.result.append(data)

    def get_text(self):
        return " ".join(self.result)


def strip_html(html: str) -> str:
    """HTML'i plain text'e çevirir."""
    stripper = HTMLStripper()
    stripper.feed(html)
    text = stripper.get_text()
    # Fazla boşlukları temizle
    text = re.sub(r"\s+", " ", text).strip()
    return text


# ── Gmail Helpers ───────────────────────────────────────────
def get_unread_emails(service, max_results: int = 50) -> list[dict]:
    """Okunmamış mailleri çeker."""
    print(f"📬 Okunmamış mailler çekiliyor (maks: {max_results})...")

    results = service.users().messages().list(
        userId="me",
        q="is:unread in:inbox -is:starred",
        maxResults=max_results,
    ).execute()

    messages = results.get("messages", [])
    print(f"   → {len(messages)} okunmamış mail bulundu")
    return messages


def get_email_detail(service, msg_id: str) -> dict:
    """Tek bir mailin detaylarını çeker."""
    msg = service.users().messages().get(
        userId="me", id=msg_id, format="full"
    ).execute()

    headers = {h["name"].lower(): h["value"] for h in msg["payload"].get("headers", [])}

    # Body çıkarma
    body = ""
    payload = msg["payload"]

    def extract_body(part):
        """Recursive body extraction."""
        mime_type = part.get("mimeType", "")
        
        def decode_data(data_str):
            # Padding eşitlemesi (Base64 decode hatalarını engellemek için)
            data_str += "=" * (-len(data_str) % 4)
            return base64.urlsafe_b64decode(data_str).decode("utf-8", errors="replace")

        # Priority 1: text/plain
        if mime_type == "text/plain" and part.get("body", {}).get("data"):
            return decode_data(part["body"]["data"])
            
        # Recursive search in parts
        for sub in part.get("parts", []):
            result = extract_body(sub)
            if result:
                return result
                
        # Fallback 1: text/html
        if mime_type == "text/html" and part.get("body", {}).get("data"):
            return decode_data(part["body"]["data"])
            
        # Ultimate Fallback: Sadece text/ ile başlayan içerikleri kabul et (binary sızıntısını önler)
        if mime_type.startswith("text/") and part.get("body", {}).get("data"):
            return decode_data(part["body"]["data"])
            
        return ""

    raw_body = extract_body(payload)

    # HTML ise strip et
    if "<html" in raw_body.lower() or "<div" in raw_body.lower():
        body = strip_html(raw_body)
    else:
        body = raw_body

    # Body'yi kısalt (token tasarrufu)
    if len(body) > 15000:
        body = body[:15000] + "... [kırpıldı]"

    return {
        "id": msg_id,
        "thread_id": msg.get("threadId"),
        "from": headers.get("from", ""),
        "to": headers.get("to", ""),
        "reply_to": headers.get("reply-to", ""),
        "subject": headers.get("subject", "(konu yok)"),
        "date": headers.get("date", ""),
        "body": body,
        "labels": msg.get("labelIds", []),
        "snippet": msg.get("snippet", ""),
        "message_id": headers.get("message-id", ""),
        "references": headers.get("references", ""),
    }


def mark_as_read(service, msg_id: str, dry_run: bool = False):
    """Maili okundu olarak işaretler."""
    if dry_run:
        print(f"   🔸 [DRY-RUN] Okundu işaretlenecekti: {msg_id}")
        return
    service.users().messages().modify(
        userId="me",
        id=msg_id,
        body={"removeLabelIds": ["UNREAD"]},
    ).execute()
    print(f"   ✅ Okundu işaretlendi: {msg_id}")


def mark_as_starred(service, msg_id: str, dry_run: bool = False):
    """Maili yıldızlı olarak işaretler (Kullanıcının dikkatini çekmek için)."""
    if dry_run:
        print(f"   🔸 [DRY-RUN] Yıldız eklenecekti: {msg_id}")
        return
    service.users().messages().modify(
        userId="me",
        id=msg_id,
        body={"addLabelIds": ["STARRED"]},
    ).execute()
    print(f"   ⭐ Yıldız eklendi: {msg_id}")


def create_draft(service, thread_id: str, to: str, subject: str, body: str, message_id: str = "", references: str = "", dry_run: bool = False) -> str | None:
    """Taslak yanıt oluşturur."""
    if dry_run:
        print(f"   🔸 [DRY-RUN] Taslak oluşturulacaktı: Re: {subject}")
        return None

    message = MIMEText(body, "plain", "utf-8")
    message["to"] = to
    message["subject"] = f"Re: {subject}" if not subject.lower().startswith("re:") else subject

    if message_id:
        message["In-Reply-To"] = message_id
        refs = f"{references} {message_id}".strip() if references else message_id
        message["References"] = refs

    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()

    draft = service.users().drafts().create(
        userId="me",
        body={
            "message": {
                "raw": raw,
                "threadId": thread_id,
            }
        },
    ).execute()

    draft_id = draft.get("id", "?")
    print(f"   📝 Taslak oluşturuldu: {draft_id}")
    return draft_id


# ── AI Analiz ───────────────────────────────────────────────
def analyze_email_with_ai(client, email_data: dict) -> dict:
    """OpenAI GPT-4o-mini ile maili analiz eder ve kategori + taslak yanıt üretir."""

    system_prompt = """Sen bir e-posta asistanısın. Gelen maili analiz et ve JSON formatında yanıt ver.

Kategoriler:
- PROMOSYON: Reklam, newsletter, pazarlama, indirim, kampanya maili
- BILDIRIM: Otomatik bildirimler (GitHub, banka, kargo, sosyal medya bildirimi vb.)
- GEREKSIZ: Spam benzeri, anket daveti, gereksiz liste mailleri
- ONEMLI_YANIT_GEREK: Bir insan tarafından yazılmış ve cevap bekleyen mail
- ONEMLI_BILGI: Önemli ama cevap gerektirmeyen (fatura, sözleşme, onay bildirimi vb.)

Kurallar:
1. JSON dışında bir şey yazma
2. Eğer kategori ONEMLI_YANIT_GEREK ise, "taslak_yanit" alanında profesyonel bir taslak yanıt yaz
3. Taslak yanıtı mailin dilinde yaz (Türkçe maile Türkçe, İngilizce maile İngilizce)
4. Taslak yanıt kısa, profesyonel ve doğal olsun — robot gibi yazma
5. "ozet" alanında mailin 1-2 cümlelik özetini yaz (her zaman Türkçe)

JSON formatı:
{
    "kategori": "PROMOSYON|BILDIRIM|GEREKSIZ|ONEMLI_YANIT_GEREK|ONEMLI_BILGI",
    "ozet": "Mailin kısa Türkçe özeti",
    "taslak_yanit": "Yanıt metni (sadece ONEMLI_YANIT_GEREK için, diğerleri null)",
    "oncelik": "dusuk|orta|yuksek",
    "neden": "Bu kategoriyi neden seçtiğinin kısa açıklaması"
}"""

    import datetime as dt
    now_str = dt.datetime.now().strftime('%d %B %Y, %A')
    user_message = f"""Bugünün Tarihi: {now_str}

Aşağıdaki e-postayı analiz et:

Gönderen: {email_data['from']}
Konu: {email_data['subject']}
Tarih: {email_data['date']}

İçerik:
{email_data['body']}"""

    import time
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message},
                ],
                temperature=0.3,
                max_tokens=1000,
                response_format={"type": "json_object"},
            )

            result = json.loads(response.choices[0].message.content)
            return result

        except Exception as e:
            if attempt < max_retries - 1:
                print(f"   ⚠️  AI analiz hatası (Deneme {attempt+1}/{max_retries}): {e}. 2 saniye sonra yeniden deneniyor...")
                time.sleep(2)
            else:
                print(f"   ⚠️  AI analiz hatası (Son Deneme): {e}")
                return {
                    "kategori": "ONEMLI_BILGI",
                    "ozet": f"AI analiz başarısız — manuel kontrol gerekli. Hata: {str(e)[:100]}",
                    "taslak_yanit": None,
                    "oncelik": "orta",
                    "neden": "AI hatası nedeniyle güvenli kategori atandı",
                }


# ── Ana Akış ────────────────────────────────────────────────
def run_email_assistant(
    account: str = "ikincil",
    max_emails: int = 50,
    dry_run: bool = False,
):
    """E-Posta Asistanı ana fonksiyonu."""

    print("=" * 60)
    print("📧 Antigravity E-Posta Asistanı")
    print(f"   Hesap: {account}")
    print(f"   Maks mail: {max_emails}")
    print(f"   Mod: {'🔸 DRY-RUN (değişiklik yapılmaz)' if dry_run else '🟢 CANLI'}")
    print(f"   Zaman: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # 1. OpenAI client
    env = load_env()
    openai_key = os.environ.get("OPENAI_API_KEY") or env.get("OPENAI_API_KEY")
    if not openai_key:
        print("❌ OPENAI_API_KEY bulunamadı (master.env kontrol edin)")
        sys.exit(1)

    from openai import OpenAI
    ai_client = OpenAI(api_key=openai_key)
    print("✅ OpenAI bağlantısı hazır")

    # 2. Gmail service
    try:
        gmail = get_gmail_service(account)
        print("✅ Gmail bağlantısı hazır")
    except Exception as e:
        print(f"❌ Gmail bağlantı hatası: {e}")
        sys.exit(1)

    # 3. Okunmamış mailleri çek
    messages = get_unread_emails(gmail, max_results=max_emails)

    if not messages:
        print("\n🎉 Tüm mailler okunmuş — yapacak bir şey yok!")
        return {"toplam": 0, "islenen": 0}

    # 4. Her maili işle
    rapor = {
        "tarih": datetime.now().isoformat(),
        "hesap": account,
        "dry_run": dry_run,
        "toplam_okunmamis": len(messages),
        "kategoriler": {
            "PROMOSYON": 0,
            "BILDIRIM": 0,
            "GEREKSIZ": 0,
            "ONEMLI_YANIT_GEREK": 0,
            "ONEMLI_BILGI": 0,
        },
        "okundu_isaretlenen": 0,
        "taslak_olusturulan": 0,
        "hatalar": 0,
        "detaylar": [],
    }

    for i, msg_ref in enumerate(messages, 1):
        msg_id = msg_ref["id"]
        print(f"\n{'─' * 50}")
        print(f"📧 [{i}/{len(messages)}] Mail ID: {msg_id}")

        try:
            # Detay çek
            email_data = get_email_detail(gmail, msg_id)
            print(f"   📩 Gönderen: {email_data['from']}")
            print(f"   📋 Konu: {email_data['subject']}")

            # AI analiz
            print("   🤖 AI analiz ediliyor...")
            analysis = analyze_email_with_ai(ai_client, email_data)
            kategori = analysis.get("kategori", "ONEMLI_BILGI").strip()
            print(f"   📊 Kategori: {kategori} (Öncelik: {analysis.get('oncelik', '?')})")
            print(f"   📝 Özet: {analysis.get('ozet', '-')}")

            # Kategori sayacı
            if kategori in rapor["kategoriler"]:
                rapor["kategoriler"][kategori] += 1

            # Aksiyonlar
            if kategori in ("PROMOSYON", "BILDIRIM", "GEREKSIZ"):
                mark_as_read(gmail, msg_id, dry_run=dry_run)
                rapor["okundu_isaretlenen"] += 1

            elif kategori == "ONEMLI_YANIT_GEREK":
                taslak_yanit = analysis.get("taslak_yanit")
                if taslak_yanit:
                    # Gönderen adresini çıkar
                    actual_reply_to = email_data.get("reply_to") or email_data.get("from", "")
                    # RFC 5322 adres ayrıştırması
                    _, reply_to_email = email.utils.parseaddr(actual_reply_to)
                    if not reply_to_email:
                        reply_to_email = actual_reply_to if actual_reply_to else "unknown@example.com"

                    draft_id = create_draft(
                        gmail,
                        thread_id=email_data["thread_id"],
                        to=reply_to_email,
                        subject=email_data["subject"],
                        body=taslak_yanit,
                        message_id=email_data.get("message_id", ""),
                        references=email_data.get("references", ""),
                        dry_run=dry_run,
                    )
                    rapor["taslak_olusturulan"] += 1
                else:
                    print("   ⚠️  AI taslak yanıt üretmedi — boş bırakıldı")
                
                # Tekrar döngüye girmesini önlemek için okundu yap ve göz önünde olsun diye yıldızla
                mark_as_read(gmail, msg_id, dry_run=dry_run)
                mark_as_starred(gmail, msg_id, dry_run=dry_run)

            else:
                # ONEMLI_BILGI → Dokunma/işlem yapma ama yıldızla ki tekrar okunmasın (loop engeli)
                # Not: Okundu (mark_as_read) yapılmaz, mail okunmamış kalır.
                mark_as_starred(gmail, msg_id, dry_run=dry_run)

            # Detay kaydet
            rapor["detaylar"].append({
                "id": msg_id,
                "from": email_data["from"],
                "subject": email_data["subject"],
                "kategori": kategori,
                "oncelik": analysis.get("oncelik"),
                "ozet": analysis.get("ozet"),
                "taslak_var": bool(analysis.get("taslak_yanit")),
            })

        except Exception as e:
            print(f"   ❌ Hata: {e}")
            rapor["hatalar"] += 1
            rapor["detaylar"].append({
                "id": msg_id,
                "hata": str(e),
            })
            # Sonsuz döngüyü önlemek için hatalı maili yıldızla
            try:
                mark_as_starred(gmail, msg_id, dry_run=dry_run)
            except Exception as inner_e:
                print(f"   ❌ Hatalı maili yıldızlarken de hata oluştu: {inner_e}")

    # 5. Rapor yazdır
    print("\n" + "=" * 60)
    print("📊 E-POSTA ASİSTANI RAPORU")
    print("=" * 60)
    print(f"Toplam okunmamış mail: {rapor['toplam_okunmamis']}")
    print(f"Promosyon/bildirim/gereksiz (okundu): {rapor['okundu_isaretlenen']}")
    print(f"Taslak yanıt oluşturulan: {rapor['taslak_olusturulan']}")
    print(f"Hatalar: {rapor['hatalar']}")
    print()
    for kat, sayi in rapor["kategoriler"].items():
        if sayi > 0:
            emoji = {"PROMOSYON": "📢", "BILDIRIM": "🔔", "GEREKSIZ": "🗑️",
                     "ONEMLI_YANIT_GEREK": "✉️", "ONEMLI_BILGI": "ℹ️"}.get(kat, "•")
            print(f"  {emoji} {kat}: {sayi}")

    # 6. Rapor dosyası kaydet
    log_dir = os.path.join(_SKILL_DIR, "logs")
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, f"rapor_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    with open(log_file, "w", encoding="utf-8") as f:
        json.dump(rapor, f, ensure_ascii=False, indent=2)
    print(f"\n📁 Rapor kaydedildi: {log_file}")

    return rapor


# ── CLI ─────────────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Antigravity E-Posta Asistanı")
    parser.add_argument("--account", default="all", help="Gmail hesabı (all/outreach/ikincil)")
    parser.add_argument("--max-emails", type=int, default=100, help="İşlenecek maksimum mail sayısı")
    parser.add_argument("--dry-run", action="store_true", help="Test modu — değişiklik yapmaz")

    args = parser.parse_args()

    if args.account.lower() == "all":
        try:
            from google_auth import _TOKEN_MAP
            accounts_to_run = list(_TOKEN_MAP.keys())
        except ImportError:
            accounts_to_run = ["outreach", "ikincil"]
        
        for acc in accounts_to_run:
            print(f"\n🚀 Başlatılıyor: Hesab -> {acc}")
            run_email_assistant(account=acc, max_emails=args.max_emails, dry_run=args.dry_run)
    else:
        run_email_assistant(
            account=args.account,
            max_emails=args.max_emails,
            dry_run=args.dry_run,
        )
