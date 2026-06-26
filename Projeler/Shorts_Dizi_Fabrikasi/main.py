"""Shorts Dizi Fabrikasi CLI.

  python main.py kur   --senaryo senaryo.md --seri kahve-fali [--test]
  python main.py bolum --seri kahve-fali [--konu "..."] [--devam] [--test]
  python main.py durum --seri kahve-fali

Arg verilmezse MODE / SERI_SLUG env'lerinden okunur (Railway cron uyumu).
"""
import argparse
import logging
import sys

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-7s [%(name)s] %(message)s",
    datefmt="%H:%M:%S",
)

from core.config import settings  # noqa: E402  (logging once kurulsun)
from pipeline.setup_series import PipelineError  # noqa: E402


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="main.py", description="Tam otomatik AI mini dizi fabrikasi (Kie Gemini Omni)"
    )
    sub = parser.add_subparsers(dest="command")

    p_kur = sub.add_parser("kur", help="Senaryodan dizi kitabi + asset fabrikasi")
    p_kur.add_argument("--senaryo", required=True, help="Senaryo dosyasi (md/txt)")
    p_kur.add_argument("--seri", required=True, help="Seri slug'i (or. kahve-fali)")
    p_kur.add_argument("--test", action="store_true", help="Test modu (loglara TEST yazar)")

    p_bolum = sub.add_parser("bolum", help="Yeni bolum uret / yarim bolume devam et")
    p_bolum.add_argument("--seri", default="", help="Seri slug'i")
    p_bolum.add_argument("--konu", default="", help="Opsiyonel bolum konusu (yapimci notu)")
    p_bolum.add_argument("--devam", action="store_true", help="Yarim bolumden devam et")
    p_bolum.add_argument("--test", action="store_true",
                         help="Duman testi: 2 sahne, 4sn, 720p (hafiza/sayac guncellenmez)")

    p_durum = sub.add_parser("durum", help="Seri durumu + Kie bakiyesi")
    p_durum.add_argument("--seri", default="", help="Seri slug'i")

    return parser


def _resolve_seri(args) -> str:
    slug = getattr(args, "seri", "") or settings.SERI_SLUG
    if not slug:
        raise PipelineError("Seri belirtilmedi. --seri <slug> ver (veya SERI_SLUG env'i doldur).")
    return slug


def _mark(value) -> str:
    return "OK" if value else "--"


def cmd_kur(args) -> int:
    from pipeline.setup_series import run_setup
    from pipeline import state
    slug = _resolve_seri(args)
    bible = run_setup(args.senaryo, slug, test=args.test)
    print("\n" + "=" * 60)
    print(f"SERI KURULDU: {bible['series']['title_tr']}")
    print(f"  Karakter   : {len(bible['characters'])}")
    print(f"  Ortam      : {len(bible['environments'])}  Aksesuar: {len(bible['props'])}")
    print(f"  Kimlik kart: {state.series_dir(slug) / 'kimlik.html'}")
    print(f"  Siradaki   : python main.py bolum --seri {slug}" + (" --test" if args.test else ""))
    print("=" * 60 + "\n")
    return 0


def cmd_bolum(args) -> int:
    from pipeline.produce_episode import run_episode
    ep = run_episode(_resolve_seri(args), konu=args.konu, devam=args.devam, test=args.test)
    if ep.get("status") == "done":
        return 0
    if ep.get("status") == "failed":
        print(f"\n{ep.get('message', 'Bolum uretimi basarisiz.')}")
        return 1
    print(f"\n{ep.get('message', 'Bolum bekliyor, --devam ile surdur.')}")
    return 2


def _print_balance() -> None:
    from services.kie_omni import get_omni_client

    balance = get_omni_client().get_credit_balance()
    if balance is None:
        print("Kie bakiyesi: bilinmiyor" + (" (DRY_RUN)" if settings.IS_DRY_RUN else ""))
    else:
        usd = balance / settings.KIE_CREDITS_PER_USD if settings.KIE_CREDITS_PER_USD else 0
        print(f"Kie bakiyesi: {balance:.0f} kredi (~${usd:.2f})")


def cmd_durum(args) -> int:
    from pipeline import state
    from services.kie_omni import get_omni_client

    slug = (getattr(args, "seri", "") or settings.SERI_SLUG).strip()
    if not slug:
        # Seri verilmedi: mevcut serileri listele + bakiyeyi goster
        known = []
        if state.SERIES_ROOT.exists():
            known = sorted(d.name for d in state.SERIES_ROOT.iterdir() if (d / "bible.json").exists())
        print("Mevcut seriler: " + (", ".join(known) if known else "(henuz seri kurulmamis)"))
        _print_balance()
        return 0

    bible = state.load_bible(slug)
    if bible is None:
        known = []
        if state.SERIES_ROOT.exists():
            known = sorted(d.name for d in state.SERIES_ROOT.iterdir() if (d / "bible.json").exists())
        hint = f"Mevcut seriler: {', '.join(known)}" if known else "Henuz hic seri kurulmamis."
        raise PipelineError(f"'{slug}' diye bir seri yok. {hint}")

    series = bible.get("series", {})
    print("\n" + "=" * 64)
    print(f"SERI: {series.get('title_tr', slug)}  ({slug})")
    print(f"  {series.get('logline_tr', '')}")
    print("-" * 64)

    board = bible.get("style", {}).get("style_board", {})
    print(f"Stil panosu : {_mark(board.get('status') == 'ready')}")
    print("Karakterler :")
    for c in bible.get("characters", []):
        print(
            f"  - {c['name']:<20} foto:{_mark(c.get('ref_image', {}).get('public_url'))} "
            f"ses:{_mark(c.get('voice', {}).get('kie_audio_id'))} "
            f"karakter:{_mark(c.get('kie_character_id'))}"
        )
    narrator = bible.get("narrator", {})
    if narrator.get("enabled"):
        print(f"Anlatici    : ses:{_mark(narrator.get('kie_audio_id'))} ({narrator.get('preset')})")
    print("Ortamlar    : " + ", ".join(
        f"{e['name_tr']} {_mark(e.get('status') == 'ready')}" for e in bible.get("environments", [])
    ))
    if bible.get("props"):
        print("Aksesuarlar : " + ", ".join(
            f"{p['name_tr']} {_mark(p.get('status') == 'ready')}" for p in bible.get("props", [])
        ))
    drive = bible.get("drive", {})
    if drive.get("folder_url"):
        print(f"Drive       : {drive['folder_url']}")

    print("-" * 64)
    print(f"Bolumler (sayac: {bible.get('episodes', {}).get('counter', 0)}):")
    ep_root = state.episodes_dir(slug)
    found = False
    if ep_root.exists():
        for ep_dir in sorted(ep_root.iterdir()):
            ep = state.load_json(ep_dir / "episode.json")
            if not ep:
                continue
            found = True
            scenes = ep.get("scenes", [])
            done_n = sum(1 for s in scenes if s.get("status") == "completed")
            title = ep.get("script", {}).get("title_tr", "")
            dur = ep.get("final", {}).get("duration_s")
            extra = f"  {dur:.0f}sn" if dur else ""
            test_tag = " [TEST]" if ep.get("test") else ""
            print(f"  {ep['slug']:<12} {ep.get('status', '?'):<11} sahne {done_n}/{len(scenes)}{extra}  {title}{test_tag}")
            bad = [f"#{s['idx']}:{s['status']}" for s in scenes if s.get("status") not in ("completed",)]
            if bad and ep.get("status") != "done":
                print(f"               bekleyen sahneler: {', '.join(bad)}")
    if not found:
        print("  (henuz bolum yok)")

    print("-" * 64)
    _print_balance()
    print("=" * 64 + "\n")
    return 0


def main(argv=None) -> int:
    argv = list(sys.argv[1:]) if argv is None else list(argv)
    if not argv and settings.MODE:
        argv = [settings.MODE]
        if settings.SERI_SLUG:
            argv += ["--seri", settings.SERI_SLUG]

    parser = _build_parser()
    args = parser.parse_args(argv)
    if not args.command:
        parser.print_help()
        return 0

    handlers = {"kur": cmd_kur, "bolum": cmd_bolum, "durum": cmd_durum}
    try:
        return handlers[args.command](args)
    except PipelineError as e:
        print(f"\nHATA: {e}\n")
        return 1
    except KeyboardInterrupt:
        print("\nDurduruldu. Ayni komut (gerekirse --devam) kaldigi yerden surer.")
        return 130


if __name__ == "__main__":
    sys.exit(main())
