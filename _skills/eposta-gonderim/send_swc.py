"""
Ornek toplu outreach gonderici (SABLON)
=======================================
Bu dosya, listeden okunan alicilara kisisellestirilmis outreach maili gonderen
basit bir ornektir. Orijinalde skill sahibinin gercek kampanya verisi vardi;
paylasim paketinde jenerik sablona indirildi.

Kendi kampanyaniz icin: alicilari, gonderen kimligini ve body_template'i degistirin.
Gmail baglantisi merkezi token sistemi uzerinden kurulur (_knowledge/credentials/oauth/).
"""

import os
import sys
import base64
from email.mime.text import MIMEText

# Add _knowledge to path
_antigravity_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(_antigravity_root, "_knowledge", "credentials", "oauth"))
from google_auth import get_gmail_service


def send_email(service, to, subject, body):
    try:
        message = MIMEText(body, 'plain')
        message['to'] = to
        message['subject'] = subject
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()

        sent_message = service.users().messages().send(
            userId='me',
            body={'raw': raw}
        ).execute()
        return True, sent_message['id']
    except Exception as e:
        return False, str(e)


def main():
    # get_gmail_service argumani, hangi merkezi token'in kullanilacagini secer.
    service = get_gmail_service("outreach")

    # TODO: Kendi alici listenizle degistirin.
    emails_to_send = [
        {"creator": "Ornek Kisi", "first_name": "Ornek", "email": "ornek@example.com"},
    ]

    # TODO: Kendi marka/kampanya metninizle degistirin.
    body_template = """Hi {first_name},

I'm <GONDEREN_ADI> from <MARKA_ADI>. We've been following your content and love your style.

We'd love to collaborate with you on a short piece of content for our brand.

Could you let us know if you're open to this, along with your rates?

Best regards,
<GONDEREN_ADI>
<MARKA_ADI>"""

    for target in emails_to_send:
        subject = f"Collaboration Inquiry: <MARKA_ADI> x {target['creator']}"
        body = body_template.format(first_name=target['first_name'])

        success, res = send_email(service, target['email'], subject, body)
        if success:
            print(f"Sent to {target['creator']} ({target['email']}) - ID: {res}")
        else:
            print(f"Failed to send to {target['creator']} ({target['email']}) - Error: {res}")


if __name__ == "__main__":
    main()
