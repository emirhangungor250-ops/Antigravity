# -*- coding: utf-8 -*-
"""İki aşamalı boru hattı.

Stage 1 (tespit): gönderenin gelen kutularında markanın İLK temasını bul,
  LLM ile nitele, EMIN ise tanıştırmayı otomatik gönder, ŞÜPHELI ise taslak bırak.
Stage 2 (teklif): yönetici kutusunda tanıştırma yapılmış (ya da markanın direkt
  yazdığı) thread'lere yöneticinin ağzından teklif TASLAĞI hazırla (asla otomatik
  göndermez).

Idempotency: Gmail etiketleri. Açık uçlu yargı: LLM (kör otomasyon yok).
"""
import traceback

import config
from services import gmail_ops as G
from services import llm
from services import notion_portfolio as NP
from services import brand_web as BW
from core import templates as T


def _web_ctx(text):
    """Marka site özeti (best-effort). Hata olursa boş -> niteleme yine çalışır."""
    try:
        return BW.summary_from_thread(text)
    except Exception:
        return ""

# outreach (kişisel gmail) çok büyük -> LLM yükünü azaltmak için kelime ön-filtresi.
# NOT: ön-filtre yalnızca ADAY daraltır; nihai yargı yine Claude'da. Yine de listede HİÇ token
# içermeyen bir teklif kaçabilir; review.py'deki günlük prefiltresiz denetim güvenlik ağıdır (TRANSPARENT).
COLLAB_PREFILTER = ('(collaboration OR collab OR kooperation OR sponsor OR sponsorship '
                    'OR partnership OR "iş birliği" OR işbirliği OR sponsorluk OR ortaklık OR reklam '
                    'OR "paid promo" OR "brand deal" OR "paid collab" OR "paid partnership" OR budget '
                    'OR colaboración OR colaboracion OR parceria OR partenariat OR collaborazione '
                    'OR patrocinio OR publicidad)')

# Sistem/bounce adresleri: tanıştırmanın alıcısı ya da alıntı kaynağı olamaz.
_JUNK_ADDR = ("postmaster@", "mailer-daemon", "mailerdaemon", "noreply", "no-reply",
              "donotreply", "do-not-reply", "bounce@", "@bounce.", "@bounces.")


def _is_junk_addr(s):
    s = (s or "").lower()
    return any(j in s for j in _JUNK_ADDR)


def _external_cc(msg, primary, *internal_addrs):
    """msg'in From+To+Cc'sinden dış (marka tarafı) katılımcıları topla: primary, iç adresler ve
    junk (bounce/no-reply) HARİÇ. Reply-all görünürlüğü için Cc'ye eklenir -> 2. marka kişisi/ajans
    sessizce konuşmadan düşmesin (CC bug sınıfı, bu sefer marka tarafı)."""
    seen = {(primary or "").lower()}
    for a in internal_addrs:
        for e in G.emails_in(a or ""):
            seen.add(e.lower())
    out = []
    for hn in ("From", "To", "Cc"):
        for e in G.emails_in(G.hdr(msg, hn)):
            el = e.lower()
            if el in seen or G.is_internal(e) or _is_junk_addr(el):
                continue
            seen.add(el)
            out.append(e)
    return out


def _cc_header(internal_addr, extra_external):
    """internal_addr (yönetici/gönderen) + dış katılımcıları tek Cc başlığında birleştir (case-insensitive dedup)."""
    seen, out = set(), []
    for p in [internal_addr] + list(extra_external):
        k = (p or "").lower()
        if p and k not in seen:
            seen.add(k)
            out.append(p)
    return ", ".join(out)


def _unanswered_brand_msgs(messages):
    """Son İÇ (bizim) mesajdan sonraki tüm dış marka mesajları. Marka cevap öncesi 2 ayrı mail
    attıysa (detaylı teklif + 'takipte miyiz?') İKİSİNİ de alıntılayabilmek için -> CC bağlamı eksik kalmasın."""
    out = []
    for m in messages:
        if G.is_internal(G.hdr(m, "From")):
            out = []
        elif not _is_junk_addr(G.hdr(m, "From")):
            out.append(m)
    return out or ([messages[-1]] if messages else [])


def _quote_all(messages, language):
    return "\n\n".join(G.quote_block(m, language) for m in messages)


def _person_first_name(cp_hdr, brand_name=""):
    """From display'inden GÜVENLİ kişi ön adı; marka/rol/sistem adı ya da markanın KENDİ adıysa None
    döner (selamlama nötr 'Merhaba,'/'Hi,' olur). 'PixelFlow Bey/Hanım' hitap bug sınıfını kökten kapatır."""
    fn = T.first_name_from(cp_hdr)
    if not fn:
        return None
    bn, f = (brand_name or "").lower(), fn.lower()
    if bn and (f in bn.split() or bn.startswith(f) or f == bn):
        return None
    return fn


def _intro_already_sent_to(cp):
    """Bu markaya (cp) zaten tanıştırma gitti mi? Yönetici kutusu ORTAK DEFTER: tanıştırma her zaman
    yöneticiyi CC'ler, From gönderenin kutularından biri olur. Marka iki gelen kutusuna birden
    yazdıysa ikinci bir otomatik tanıştırma (hesaplar-arası çift gönderim) gitmesini engeller;
    gönderim sonrası etiketleme patlasa bile bir sonraki tur çifti bu defterden görür."""
    acc = config.MANAGER_ACCOUNT
    q = (f'newer_than:{config.SCAN_WINDOW_DAYS}d to:{cp} '
         f'(from:{config.ADDR["inbox_primary"]} OR from:{config.ADDR["inbox_personal"]})')
    try:
        res = G.service(acc).users().messages().list(userId="me", q=q, maxResults=1).execute()
        return bool(res.get("messages"))
    except Exception:
        return False


def _subj_re(s):
    s = (s or "").strip()
    return s if s.lower().startswith("re:") else f"Re: {s}"


def _latest_external_from(messages):
    """En yeni dış (marka) gönderen adresi + display header'ı. Bounce/no-reply/postmaster
    atlanır -> tanıştırma yanlışlıkla bir teslimat-hatası/oto-yanıt adresine gitmesin."""
    for m in reversed(messages):
        frm = G.hdr(m, "From")
        for e in G.emails_in(frm):
            if not G.is_internal(e) and not _is_junk_addr(e):
                return e.lower(), frm
    return "", ""


def _manager_in_thread(messages):
    """Yönetici (Partnerships Manager) bu thread'e zaten dahil mi? (Stage 1'i tetiklemez ->
    Stage 2'nin işidir.) Yönetici e-postası config.ADDR['manager']'dan gelir."""
    mgr = (config.ADDR.get("manager") or "").lower()
    if not mgr:
        return False
    for m in messages:
        blob = " ".join([G.hdr(m, "From"), G.hdr(m, "To"), G.hdr(m, "Cc")]).lower()
        if mgr in blob:
            return True
    return False


def _someone_from(messages, email):
    email = email.lower()
    for m in messages:
        if email in G.hdr(m, "From").lower():
            return True
    return False


def _sender_addr_in_thread(messages):
    """Thread'de gönderenin HANGİ kutusu görünüyor? (Stage 2 teklif taslağını yöneticinin
    ağzından kurarken doğru gönderen-kutusunu CC'ler.) Bulamazsa birincil kutuya düşer."""
    primary = config.ADDR.get("inbox_primary", "")
    personal = config.ADDR.get("inbox_personal", "")
    blob = ""
    for m in messages:
        blob += " " + " ".join([G.hdr(m, "From"), G.hdr(m, "To"), G.hdr(m, "Cc")]).lower()
    if primary and primary.lower() in blob:
        return primary
    if personal and personal.lower() in blob:
        return personal
    return primary


def _references(messages):
    ids = [G.hdr(m, "Message-Id") for m in messages if G.hdr(m, "Message-Id")]
    return (ids[-1] if ids else None), (" ".join(ids) if ids else None)


def _already_active_partner(brand_name, counterparty):
    """Yönetici bu markayla/temsilciyle daha önce yazışmış mı? (zaten aktif partner)
    Varsa otomatik tanıştırma yerine taslağa düşürülür — gereksiz 'yeniden tanışma' önlenir.
    Yanlış-pozitif zararsız: auto -> draft sadece bir onay adımı ekler."""
    acc = config.MANAGER_ACCOUNT
    queries = [f"from:me {counterparty} newer_than:160d"]
    bn = (brand_name or "").strip()
    # Kısa/jenerik tek-kelime adda (Nova/Aha/Pro) from:me "ad" alakasız eski maillere çarpar (yanlış-pozitif).
    # Ad sorgusunu yalnız >=2 kelimeli ya da ayırt edici (>=6 harf) adlarda kullan; asıl sinyal counterparty (adres).
    if bn and (len(bn.split()) >= 2 or len(bn) >= 6):
        safe = bn.replace('"', "")
        queries.append(f'from:me "{safe}" newer_than:160d')
    for qy in queries:
        try:
            res = G.service(acc).users().messages().list(userId="me", q=qy, maxResults=1).execute()
            if res.get("messages"):
                return True
        except Exception:
            pass
    return False


def _refs_for_brand(q):
    plat = None
    ask = (q.brand_ask or "").lower()
    if "youtube" in ask or "long" in ask:
        plat = "YouTube"
    elif "instagram" in ask or "reel" in ask or "tiktok" in ask or "short" in ask:
        plat = "Instagram"
    return NP.select_references(q.portfolio_category, lang=q.language, platform_pref=plat, n=3)


def _offer_variants(q):
    """Yöneticiye bırakılacak N ayrı teklif draftı için fiyat yönergeleri.
    Markanın sorduğu kalemi ÖNCE verir. Sıra: odaklı -> paket -> menü. config.OFFER_VARIANTS kadar.
    Fiyatlar config.PRICE_* (ENV) üzerinden gelir -> kendi rate card'ına göre değiştir."""
    ask = (q.brand_ask or "").lower()
    ps, pl, bp = config.PRICE_SHORT, config.PRICE_LONG, config.PRICE_BUNDLE
    if "shorts" in ask:                       # YouTube Shorts = kısa-form (uzun video değil)
        primary = "short"
    elif any(k in ask for k in ("youtube", "long-form", "long form", "uzun")):
        primary = "youtube"
    else:                                     # reel/tiktok/instagram/short veya belirsiz -> kısa
        primary = "short"

    if primary == "youtube":
        focused = f"Sadece YouTube dedicated uzun video teklif et: {pl}. Tek kalem, net; başka paket/fiyat ekleme."
        bundle = (f"Markaya PAKET öner: YouTube dedicated uzun video + 1 kısa video (cross-post) BİRLİKTE {bp} "
                  f"(ayrı ayrı daha pahalı; birlikte avantajlı). Önce YouTube'u vurgula, tek paket fiyatı ver.")
        menu = (f"Kısa SEÇENEK MENÜSÜ sun (madde madde): (1) YouTube dedicated uzun video {pl}, "
                f"(2) kısa video paketi {ps}, (3) ikisi birlikte {bp}. YouTube en üstte; hangisi uygun diye sorarak bitir.")
    else:
        focused = f"Sadece kısa video paketi (IG Reel + Story + Gönderi, cross-post) teklif et: {ps}. Tek kalem, net."
        bundle = (f"Markaya PAKET öner: kısa video + YouTube dedicated uzun video BİRLİKTE {bp} "
                  f"(daha geniş erişim; birlikte avantajlı). Önce kısa videoyu ver, tek paket fiyatı.")
        menu = (f"Kısa SEÇENEK MENÜSÜ sun (madde madde): (1) kısa video paketi {ps}, "
                f"(2) YouTube dedicated uzun video {pl}, (3) ikisi birlikte {bp}. Hangisi uygun diye sorarak bitir.")
    return [("odaklı", focused), ("paket", bundle), ("menü", menu)][:config.OFFER_VARIANTS]


# ── STAGE 1 ───────────────────────────────────────────────
def stage1_detect(account, use_prefilter, sent_intro_to=None):
    log = []
    if sent_intro_to is None:
        sent_intro_to = set()
    q_parts = [f"in:inbox newer_than:{config.SCAN_WINDOW_DAYS}d", f"-label:{config.LBL_HANDLED}"]
    if use_prefilter:
        q_parts.append(COLLAB_PREFILTER)
    query = " ".join(q_parts)

    metas = G.search_threads(account, query, maxn=config.MAX_THREADS_PER_RUN)
    for meta in metas:
        tid = meta["threadId"]
        try:
            th = G.get_thread(account, tid)
            msgs = th["messages"]
            # Sadece "marka yeni yazdı, henüz cevap vermedik" tetikler:
            cp, cp_hdr = _latest_external_from(msgs)
            last_from = G.hdr(msgs[-1], "From")
            if not cp:
                continue
            if G.is_internal(last_from) or _is_junk_addr(last_from):  # son mesaj bizden ya da bounce/oto -> elle bak
                continue
            if _manager_in_thread(msgs):       # yönetici zaten bağlı -> Stage 2 işi
                continue
            if config.is_blocked_sender(cp, cp_hdr):   # kara liste (ör. Aha Creator) -> hiç dokunma
                G.add_label(account, tid, config.LBL_HANDLED)
                G.add_label(account, tid, config.LBL_SKIPPED)
                log.append(f"[S1/{account}] {cp}: kara liste -> atlandı")
                continue
            # Hesaplar-arası çift tanıştırma önlemi: marka iki kutuya birden yazdıysa 2. tanıştırma gitmesin.
            if cp in sent_intro_to or _intro_already_sent_to(cp):
                G.add_label(account, tid, config.LBL_HANDLED)
                log.append(f"[S1/{account}] {cp}: bu markaya zaten tanıştırma gitti -> atlandı (çift önlendi)")
                continue

            text, _ = G.thread_text(account, tid)
            q = llm.qualify(text, web_context=_web_ctx(text))
            action = llm.decide_action(q)
            # Emin olsak da: marka zaten aktif partner ise otomatik tanıştırma yerine taslak
            if action == "auto_intro" and _already_active_partner(q.brand_name, cp):
                action = "draft_intro"
                log.append(f"[S1/{account}] {cp} | {q.brand_name}: zaten aktif partner -> auto YERINE taslak")
            log.append(f"[S1/{account}] {cp} | {q.collab_type}/{q.confidence}/{q.offer_quality} -> {action} | {q.brand_name}")

            if action == "ignore":
                G.add_label(account, tid, config.LBL_HANDLED)
                G.add_label(account, tid, config.LBL_SKIPPED)
                continue

            irt, refs = _references(msgs)
            fname = _person_first_name(cp_hdr, q.brand_name)   # marka/rol/sistem adı -> None -> nötr selam
            # Kişisel tanıştırma = LLM (gönderenin ağzından). Patlarsa deterministik şablona düş
            # (auto_intro otomatik gider; mail asla boş kalmamalı).
            try:
                body = llm.write_intro(q.language, q.brand_name, q.brand_vertical, q.brand_ask,
                                       contact_name=fname, vertical_confident=q.vertical_confident)
                if not llm.looks_like_outbound_email(body, (config.SENDER_NAME,)):   # analiz/meta sızıntısı -> şablona düş
                    raise ValueError("intro LLM çıktısı e-posta değil (meta/analiz şüphesi)")
            except Exception as e:
                body = T.intro_body(q.language, fname)
                log.append(f"[S1/{account}] intro LLM->şablon fallback: {str(e)[:80]}")
            subj = _subj_re(G.hdr(msgs[-1], "Subject"))
            # Selamı DETERMINISTIK kur (LLM/şablon ikisinde de): büyük-harf 'ZEYNEP', uydurma 'Best',
            # düşen 'Bey' sınıfını kapatır. SONRA em-dash arındır + markanın cevap-öncesi TÜM maillerini
            # altına alıntıla -> CC'deki yönetici orijinal bağlamı görsün (yalnız son mail değil).
            body = llm.enforce_greeting(body, q.language, fname)
            body = llm.no_emdash(body) + "\n\n" + _quote_all(_unanswered_brand_msgs(msgs), q.language)
            # Reply-all: markanın diğer katılımcıları (2. kişi/ajans) da Cc'de kalsın.
            cc_value = _cc_header(config.ADDR["manager"], _external_cc(msgs[-1], cp, config.ADDR["manager"]))
            raw = G.build_raw(G.display_from(account, config.SENDER_NAME), cp, subj, body,
                              cc_h=cc_value, in_reply_to=irt, references=refs)

            if config.DRY_RUN:
                log.append(f"    [DRY_RUN] intro {action} atlanmadı (gönderilmedi)")
                continue

            if action == "auto_intro":
                G.send(account, raw, thread_id=tid)
                sent_intro_to.add(cp)   # gönderim sonrası HEMEN işaretle (etiketleme patlasa da çift önlenir)
                G.add_label(account, tid, config.LBL_HANDLED)
                G.add_label(account, tid, config.LBL_AUTO_INTRO)
            else:  # draft_intro -> gönderen onaylasın/silsin
                G.create_draft(account, raw, thread_id=tid)
                sent_intro_to.add(cp)
                G.add_label(account, tid, config.LBL_HANDLED)
                G.add_label(account, tid, config.LBL_DRAFT_INTRO)
        except Exception as e:
            log.append(f"[S1/{account}] HATA tid={tid}: {e}\n{traceback.format_exc()[:400]}")
    return log


# ── STAGE 2 ───────────────────────────────────────────────
def stage2_offers():
    log = []
    acc = config.MANAGER_ACCOUNT
    query = f"in:inbox newer_than:{config.SCAN_WINDOW_DAYS}d -label:{config.LBL_OFFER_READY}"
    metas = G.search_threads(acc, query, maxn=config.MAX_THREADS_PER_RUN)
    for meta in metas:
        tid = meta["threadId"]
        try:
            th = G.get_thread(acc, tid)
            msgs = th["messages"]
            cp, cp_hdr = _latest_external_from(msgs)
            if not cp:                                   # dış marka yok (iç/bildirim) -> atla
                continue
            if config.is_blocked_sender(cp, cp_hdr):     # kara liste -> teklif yazma
                log.append(f"[S2] kara liste -> atlandı: {cp}")
                G.add_label(acc, tid, config.LBL_OFFER_READY)
                continue
            if _someone_from(msgs, config.ADDR["manager"]):  # yönetici zaten cevaplamış -> atla
                continue
            if config.ADDR["manager"].lower() in G.hdr(msgs[-1], "From").lower():
                continue

            text, _ = G.thread_text(acc, tid)
            q = llm.qualify(text, web_context=_web_ctx(text))
            if not q.is_collaboration or q.collab_type == "not_collab":
                log.append(f"[S2] atla (collab değil): {cp} | {q.brand_name}")
                G.add_label(acc, tid, config.LBL_OFFER_READY)  # tekrar değerlendirme
                continue

            refs = _refs_for_brand(q)
            contact = _person_first_name(cp_hdr, q.brand_name)   # marka/rol/sistem adı -> None -> nötr selam
            # alan emin değilse boş geç -> writer uydurmak yerine genel uyum cümlesi kurar
            vertical = q.brand_vertical if q.vertical_confident else ""
            irt, refchain = _references(msgs)
            subj = _subj_re(G.hdr(msgs[-1], "Subject"))
            cc = _sender_addr_in_thread(msgs)
            # Reply-all: gönderen + markanın diğer katılımcıları (2. kişi/ajans) Cc'de kalsın.
            cc_value = _cc_header(cc, _external_cc(msgs[-1], cp, cc, config.ADDR["manager"]))
            # Markanın cevap-öncesi TÜM maillerini alıntıla -> CC'deki gönderen de bağlamı görsün.
            quoted = "\n\n" + _quote_all(_unanswered_brand_msgs(msgs), q.language)

            # Yöneticiye N AYRI hazır teklif draftı (odaklı/paket/menü) -> en uygununu seçip yollar.
            made, fallback_used, labeled = 0, False, False
            for tag, directive in _offer_variants(q):
                try:
                    offer = llm.write_offer(q.language, q.brand_name, vertical, q.brand_ask,
                                            q.collab_type, refs, contact_name=contact,
                                            pricing_directive=directive)
                    if not llm.looks_like_outbound_email(offer, (config.MANAGER_NAME,)):   # analiz/meta sızıntısı -> şablona düş
                        raise ValueError("LLM çıktısı e-posta değil (kısa/boş/meta-analiz)")
                except Exception as we:
                    if fallback_used:   # LLM erişilemiyor -> aynı şablonu 3 kez kopyalama, tek yeter
                        log.append(f"[S2] {tag} atlandı (LLM yok, fallback zaten kondu)")
                        continue
                    log.append(f"[S2] {tag} LLM fallback ({we})")
                    offer = T.offer_fallback(q.language, q.brand_name, refs)
                    fallback_used = True
                # Selamı DETERMINISTIK kur (büyük-harf/uydurma-isim/düşen-honorific kalkanı)
                offer = llm.enforce_greeting(offer, q.language, contact)
                raw = G.build_raw(G.display_from(acc, config.MANAGER_NAME), cp, subj,
                                  llm.no_emdash(offer) + quoted,
                                  cc_h=cc_value, in_reply_to=irt, references=refchain)
                if config.DRY_RUN:
                    log.append(f"    [DRY_RUN] {tag} teklif taslağı (yazılmadı)")
                    made += 1
                    continue
                G.create_draft(acc, raw, thread_id=tid)
                made += 1
                if not labeled:   # İLK taslakla birlikte etiketle: kısmi çökme ya da yöneticinin silmesi çift üretmesin
                    G.add_label(acc, tid, config.LBL_OFFER_READY)
                    labeled = True

            log.append(f"[S2] {made} teklif taslağı ({config.OFFER_VARIANTS} istendi) -> {cp} | "
                       f"{q.brand_name} | {q.collab_type}/{q.language} | {len(refs)} ref")
        except Exception as e:
            log.append(f"[S2] HATA tid={tid}: {e}\n{traceback.format_exc()[:400]}")
    return log


def run():
    out = []
    out.append(f"=== Inbound Teklif Yanıt | DRY_RUN={config.DRY_RUN} AUTO_INTRO={config.AUTO_SEND_INTRO} "
               f"window={config.SCAN_WINDOW_DAYS}d ===")
    sent_intro_to = set()   # hesaplar-arası çift tanıştırma önlemi (iki kutu aynı turda taranır)
    # Birincil kutu (iş kutusu) genelde temiz -> prefilter yok; kişisel kutu gürültülü -> prefilter aç.
    out += stage1_detect("inbox_primary", use_prefilter=False, sent_intro_to=sent_intro_to)
    out += stage1_detect("inbox_personal", use_prefilter=True, sent_intro_to=sent_intro_to)
    out += stage2_offers()
    return out
