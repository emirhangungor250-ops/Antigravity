# -*- coding: utf-8 -*-
"""Onay token'ı birim testi — AĞ YOK (HMAC make/verify saf).

Doğrular: geçerli token comment_id döndürür; bozuk imza reddedilir; süresi dolmuş reddedilir;
boş/biçimsiz reddedilir. Onay sayfası (web/app.py) bu doğrulamaya güvenir.
Kullanım (proje kökünden):  python tests/test_approval_token.py
"""
import os
import sys

os.environ.setdefault("YT_APPROVAL_SECRET", "test-secret-abc123")
os.environ.setdefault("YT_APPROVAL_BASE_URL", "https://onay.example.test")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core import mail_report as M


def _tok(url: str) -> str:
    return url.split("t=", 1)[1] if "t=" in url else ""


def main():
    good = _tok(M.make_reply_url("CID_ABC"))
    p, _, sig = good.partition(".")
    tampered = p + "." + ("0" * len(sig))
    expired = _tok(M.make_reply_url("CID_X", ttl_days=-1))

    checks = [
        ("geçerli token comment_id döndürür", M.verify_reply_token(good) == "CID_ABC"),
        ("bozuk imza reddedilir",             M.verify_reply_token(tampered) is None),
        ("süresi dolmuş token reddedilir",    M.verify_reply_token(expired) is None),
        ("boş token reddedilir",              M.verify_reply_token("") is None),
        ("noktasız token reddedilir",         M.verify_reply_token("abcdef") is None),
    ]
    fails = 0
    for name, ok in checks:
        print(f"  {'✅' if ok else '❌ HATA'} {name}")
        fails += 0 if ok else 1
    if fails:
        print(f"❌ {fails} kontrol başarısız")
        return 1
    print("✅ onay token'ı imza + süre doğrulaması sağlam (ağsız)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
