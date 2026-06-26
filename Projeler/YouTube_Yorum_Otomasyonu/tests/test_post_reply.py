# -*- coding: utf-8 -*-
"""post_reply birim testi — AĞ YOK (requests.post + token refresh mock'lu).

Doğrular: doğru endpoint (/comments), parentId + textOriginal gövdesi, Bearer token,
dönen cevap id'si. YouTube'a gerçek istek atılmaz.
Kullanım (proje kökünden):  python tests/test_post_reply.py
"""
import json
import os
import sys
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core import youtube_client as YT


class _Resp:
    def __init__(self, status, payload):
        self.status_code = status
        self._p = payload
        self.text = json.dumps(payload)

    def json(self):
        return self._p


def main():
    captured = {}

    def fake_post(url, **kw):
        captured["url"] = url
        captured["headers"] = kw.get("headers", {})
        captured["body"] = json.loads(kw.get("data", "{}"))
        return _Resp(200, {"id": "NEWREPLY123"})

    with mock.patch.object(YT, "_forcessl_access_token", return_value="FAKE_TOKEN"), \
         mock.patch.object(YT.requests, "post", side_effect=fake_post):
        rid = YT.post_reply("PARENT_ABC", "Teşekkürler, çok haklısın!")

    checks = [
        ("dönen cevap id'si doğru",   rid == "NEWREPLY123"),
        ("comments endpoint çağrıldı", "/comments" in captured.get("url", "")),
        ("parentId gönderildi",        captured["body"]["snippet"]["parentId"] == "PARENT_ABC"),
        ("textOriginal gönderildi",    captured["body"]["snippet"]["textOriginal"] == "Teşekkürler, çok haklısın!"),
        ("Bearer token başlığı",       captured["headers"].get("Authorization") == "Bearer FAKE_TOKEN"),
    ]
    fails = 0
    for name, ok in checks:
        print(f"  {'✅' if ok else '❌ HATA'} {name}")
        fails += 0 if ok else 1
    if fails:
        print(f"❌ {fails} kontrol başarısız")
        return 1
    print("✅ post_reply doğru endpoint + gövde ile çağırıyor (ağsız)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
