"""Ana akış: yeni gizli video → eşleştir → transkript+sözlük → açıklama + kapak → haber.

Cron girişi (Railway, saatlik 09–22). Varsayılan KURU çalışma (DRY_RUN=1):
mail atmaz, Drive'a yazmaz, kapak motorunu çalıştırmaz; ne yapacağını gösterir.
Canlı: DRY_RUN=0 (veya --live).
"""
import argparse
import sys
import tempfile

import config
from core import cover, describe, glossary, notify, state, youtube_owner
from core import notion_match as nm


def log(msg=""):
    print(msg, flush=True)


def process_video(v: dict, rows: list[dict], dry: bool, force: bool = False):
    vid, title = v["id"], v["title"]
    log(f"\n=== VIDEO: {title}  ({vid}) ===")

    # 1) Transkript (sahip yetkisi, bedava). Henüz hazır/eksikse sonraki tura bırak.
    # Yeni yüklenen videoda ASR altyazısı birkaç dakika-saat sonra tamamlanır; erken
    # davranıp eksik metinle yanlış "eşleşmedi" dememek için süreye göre alt sınır koy.
    tr = youtube_owner.fetch_transcript(vid)
    dur = v.get("duration_sec", 0)
    min_chars = max(300, dur * 6)  # ~6 karakter/sn altı = altyazı muhtemelen tamamlanmadı
    # (TR konuşma ~12-15 kar/sn; 6 güvenli alt sınır. Konuşması çok az video nadir.)
    if not tr["has_captions"] or len(tr["text"]) < min_chars:
        log(f"  • Altyazı hazır değil/eksik ({len(tr.get('text', ''))} kar, ≥{min_chars} bekleniyor) "
            "— sonraki turda tekrar denerim.")
        return "no_captions"

    # 2) Sözlükle düzelt
    fixed, applied = glossary.apply_glossary(tr["text"])
    if applied:
        log("  • Sözlük düzeltmeleri: " + ", ".join(f"{w}→{c}({n})" for w, c, n in applied))
    log(f"  • Transkript: {len(fixed)} karakter")

    # 3) Notion'da doğru satır
    m = nm.match(title, fixed, rows)
    if not m["row"]:
        log("  • Notion'da YouTube ikonlu satır bulunamadı.")
        return "no_rows"
    r = m["row"]
    log(f"  • Eşleşme: '{r['name']}' (başlık {m['title_sim']:.0%}, içerik {m['content']:.0%}, "
        f"toplam {m['score']:.0%}, 2.aday {m['second']:.0%})")

    if not m["confident"] and force:
        log("  • Skor güven barının kıl payı altında ama bu eşleşme onaylandı → devam.")
    if not m["confident"] and not force:
        log("  • BELİRSİZ → körlemesine yazmıyorum. Yöneticiye sorulacak.")
        if not dry:
            admin = config.ADMIN_EMAIL or (config.NOTIFY_EMAILS[0] if config.NOTIFY_EMAILS else None)
            notify.send(
                f"Yeni video eşleştirilemedi: {title}",
                f"<p>Yeni gizli video çıktı ama Notion'da hangi satıra ait olduğundan emin olamadım: "
                f"<b>{title}</b></p><p>En yakın tahmin: {r['name']} (%{int(m['score']*100)}). "
                f"Doğru satırı söylersen ben devam ederim.</p>",
                to=[admin] if admin else None)
            state.mark_seen(vid, {"status": "ambiguous", "guess": r["name"]})
        return "ambiguous"

    if not r["drive"]:
        log("  • Eşleşen satırda Drive klasörü yok — atlanıyor (yöneticiye sorulmalı).")
        return "no_drive"

    # 3.5) Kalıcı dedup: Drive'da açıklama + kapak zaten varsa tekrar yapma
    if cover.already_done(r["drive"]):
        log("  • Açıklama + kapak Drive'da zaten var — bu video daha önce işlenmiş, atlanıyor.")
        if not dry:
            state.mark_seen(vid, {"status": "already_done", "row": r["name"]})
        return "already_done"

    # 4) Açıklama (bedava gpt-5.4; kuru çalışmada Drive'a yazmaz, sadece üretir)
    log("  • Açıklama üretiliyor...")
    desc = describe.generate_description(
        video_name=title, video_url=f"https://youtu.be/{vid}",
        brief=r["script"], transcript=fixed, duration_sec=v.get("duration_sec", 0),
        drive_folder_url=r["drive"], dry_run=dry,
        doc_name=f"Aciklama_Taslagi_{title[:40]}")
    if not desc.get("ok"):
        log("  ✗ Açıklama üretilemedi: " + str(desc.get("error"))[:300])
        return "desc_failed"
    log(f"  ✓ Açıklama üretildi (tip: {desc.get('video_type')}, {len(desc['description_text'])} karakter)")
    if dry:
        log("  ----- AÇIKLAMA ÖNİZLEME -----")
        log(desc["description_text"][:1600])
        log("  ----- (önizleme kesildi) -----")

    if dry:
        log("  • [KURU] Kapak motoru çalıştırılmaz, mail atılmaz, Drive'a yazılmaz.")
        return "dry_ok"

    # 5) Kapak: videoyu Drive'a app-sahipli koy + motoru tetikle
    log("  • Video indirilip Drive'a konuyor, kapak motoru tetikleniyor...")
    with tempfile.TemporaryDirectory() as wd:
        cover.ensure_video_in_drive(vid, title, r["drive"], wd)
        eng = cover.trigger_cover_engine()
    log(f"  • Kapak motoru: {'tamam' if eng['ok'] else 'hata'}")

    # 6) Haber
    subj, body = notify.ready_email(title, r["drive"], desc.get("doc_link"))
    notify.send(subj, body)
    log("  ✓ Ekibe haber gönderildi.")

    state.mark_seen(vid, {"status": "done", "row": r["name"], "doc_link": desc.get("doc_link")})
    return "done"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--video", help="Sadece bu video id'sini işle (test için)")
    ap.add_argument("--live", action="store_true", help="Canlı çalış (mail/Drive/kapak gerçekten)")
    ap.add_argument("--force", action="store_true", help="Skor barın altında olsa da eşleşmeyi onayla (insan teyit etti)")
    ap.add_argument("--show-all", action="store_true", help="İşlenmiş olsa da göster")
    args = ap.parse_args()

    from core.local_env import load_local_env
    load_local_env()

    dry = config.DRY_RUN and not args.live
    log(f"## YT Unlisted Otomasyonu — {'KURU ÇALIŞMA' if dry else 'CANLI'} ##")

    unlisted = youtube_owner.list_unlisted()
    log(f"Kanaldaki gizli video sayısı: {len(unlisted)}")

    if args.video:
        unlisted = [v for v in unlisted if v["id"] == args.video]
        if not unlisted:
            log(f"'{args.video}' gizli videolar arasında yok.")
            return 0

    targets = unlisted if (args.show_all or dry or args.video) else [v for v in unlisted if not state.is_seen(v["id"])]
    if not targets:
        log("İşlenecek yeni gizli video yok.")
        return 0

    rows = nm.youtube_rows()
    log(f"Notion'da YouTube ikonlu satır: {len(rows)}")

    summary = {}
    for v in targets:
        res = process_video(v, rows, dry, force=args.force)
        summary[res] = summary.get(res, 0) + 1
    log("\n## ÖZET: " + ", ".join(f"{k}={n}" for k, n in summary.items()) + " ##")
    return 0


if __name__ == "__main__":
    sys.exit(main())
