# -*- coding: utf-8 -*-
"""Inbound Teklif Yanıt — bağımsız denetim cron'u (output audit).

Otomasyonun canlı çıktısını alır, aynı kaynağa BAĞIMSIZ bakar, hata arar.
Sadece SORUN bulursa sahibine tek mail atar; temizse sessiz kalır (sadece log).

İki ana kontrol:
1. Yanlış otomatik gönderim: her OTOMATİK tanıştırılan thread'i yeniden niteler;
   gerçek-yeni-iyi collab değilse ya da zaten-aktif-partnerse işaretler.
2. Kaçırılan iş birliği: işlenmemiş (etiketsiz), >2 saatlik, son mesajı markadan
   gelen thread'leri ön-filtresiz yeniden niteler; collab ise "kaçırıldı" der.
   (Bu aynı zamanda canlılık sinyali: cron ölürse mailler birikir, burada yakalanır.)

Uyarı maili OPSİYONELdir: ALERT_EMAIL_TO + RESEND_API_KEY + ALERT_EMAIL_FROM env'leri
verilmezse uyarı atılmaz (loga yazılır). Resend yerine başka bir gönderim de bağlayabilirsin.
"""
import time, traceback
import config
from services import gmail_ops as G, llm
from core import pipeline as P

ISSUES = []


def label_thread_ids(acc, name, maxn=30):
    g = G.service(acc)
    lid = None
    for lb in g.users().labels().list(userId="me").execute().get("labels", []):
        if lb["name"] == name:
            lid = lb["id"]; break
    if not lid:
        return None  # etiket hiç yok
    res = g.users().threads().list(userId="me", labelIds=[lid], maxResults=maxn).execute()
    return [t["id"] for t in res.get("threads", [])]


def audit_auto_sends():
    n = 0
    for acc in config.INBOUND_ACCOUNTS:
        tids = label_thread_ids(acc, config.LBL_AUTO_INTRO)
        for tid in (tids or []):
            try:
                th = G.get_thread(acc, tid); msgs = th["messages"]
                cp, _ = P._latest_external_from(msgs)
                text, _ = G.thread_text(acc, tid)
                q = llm.qualify(text, web_context=P._web_ctx(text))
                n += 1
                if (not q.is_collaboration) or q.collab_type != "new" or q.offer_quality != "good":
                    ISSUES.append(f"Otomatik tanıştırma şüpheli: {cp} — sağlam bir iş birliği teklifi olmayabilir.")
                elif P._already_active_partner(q.brand_name, cp):
                    ISSUES.append(f"Otomatik tanıştırma daha önce çalışılan bir markaya gitmiş olabilir: {q.brand_name}.")
            except Exception as e:
                print("audit_auto err", tid, e)
    return n


def audit_missed():
    now = time.time(); n = 0; metas = []   # metas döngü öncesi tanımlı: iki kutu da patlasa NameError/çökme yok
    for acc in config.INBOUND_ACCOUNTS:
        try:
            metas = G.search_threads(acc, f"in:inbox newer_than:2d -label:{config.LBL_HANDLED}", maxn=25)
        except Exception as e:
            print("missed search err", acc, e); continue
        checked = 0
        for meta in metas:
            if checked >= 15:   # kaçırılan-iş güvenlik ağını genişlet (meşgul kişisel gmail'de 8 azdı)
                break
            tid = meta["threadId"]
            try:
                th = G.get_thread(acc, tid); msgs = th["messages"]
                last_ms = int(msgs[-1].get("internalDate", "0")) / 1000
                if now - last_ms < 7200:   # 2 saatten yeni -> sonraki tur işleyebilir, atla
                    continue
                if G.is_internal(G.hdr(msgs[-1], "From")):
                    continue
                cp, _ = P._latest_external_from(msgs)
                if not cp or P._manager_in_thread(msgs):
                    continue
                checked += 1; n += 1
                text, _ = G.thread_text(acc, tid)
                q = llm.qualify(text, web_context=P._web_ctx(text))
                if q.is_collaboration and llm.decide_action(q) != "ignore":
                    ISSUES.append(f"Kaçırılmış olabilir: {cp} ({q.brand_name}) — iş birliği gibi ama otomasyon dokunmamış.")
            except Exception as e:
                print("missed err", tid, e)
    return n, metas


def main():
    auto_n = audit_auto_sends()
    missed_n, _ = audit_missed()

    # canlılık: hiçbir hesapta 'İşlendi' etiketi yoksa cron hiç çalışmamış demektir
    any_label = any(label_thread_ids(acc, config.LBL_HANDLED) is not None for acc in config.INBOUND_ACCOUNTS)
    if not any_label:
        ISSUES.append("Otomasyon hiç çalışmamış olabilir (işleme etiketi yok) — cron'u kontrol et.")

    print(f"denetim: auto_kontrol={auto_n} missed_kontrol={missed_n} sorun={len(ISSUES)}")

    if not ISSUES:
        print("temiz — bildirim yok")
        return 0

    body = ("Inbound teklif yanıt otomasyonunu denetledim, gözden geçirmen gereken bir şey çıktı:\n\n"
            + "\n".join(f"- {x}" for x in ISSUES[:8])
            + "\n\nSenin yapman gereken: yukarıdakilere bir bak. Otomasyonu durdurmak istersen DRY_RUN=1 yeter.")
    subj = "Inbound teklif yanıt — kontrol gerekiyor"
    if config.DRY_RUN:
        print("[DRY_RUN] alert atlanmadı:\n", body); return 0

    # Uyarı maili OPSİYONEL: Resend ile gönder. Doğrulanmış (DKIM) bir domain'den göndermek
    # spam/auth uyarılarını önler. Env yoksa uyarı atlanır (loga yazılır). İstersen bu bloğu
    # kendi gönderim yöntemine (SMTP, Gmail API, vb.) çevirebilirsin.
    import os as _os
    import requests as _rq
    api_key = _os.environ.get("RESEND_API_KEY", "")
    to_addr = _os.environ.get("ALERT_EMAIL_TO", "")     # uyarının gideceği adres
    from_addr = _os.environ.get("ALERT_EMAIL_FROM", "") # doğrulanmış gönderen, ör. "Alerts <alerts@yourdomain.com>"
    if not (api_key and to_addr and from_addr):
        print("ALERT_EMAIL_TO / ALERT_EMAIL_FROM / RESEND_API_KEY eksik, alert atılamadı")
        return 0
    r = _rq.post(
        "https://api.resend.com/emails",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={"from": from_addr, "to": [to_addr],
              "reply_to": to_addr, "subject": subj, "text": body},
        timeout=30,
    )
    if r.status_code >= 300:
        print(f"Resend hata: {r.status_code} {r.text[:200]}")
        return 0
    print(f"ALERT gönderildi (Resend {r.json().get('id', '?')}, {len(ISSUES)} sorun)")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SystemExit:
        raise
    except Exception:
        print("REVIEW CRASH\n", traceback.format_exc())
        raise SystemExit(1)
