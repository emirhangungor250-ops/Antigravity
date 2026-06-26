"""Canlı Demo başlatıcı — chat-trigger ana akış.

Kullanım:
    python _skills/canli-demo/start.py <proje_klasoru>

Örnek:
    python _skills/canli-demo/start.py Projeler/eCom_Reklam_Otomasyonu

Akış:
    1. Proje dashboard entegrasyonu var mı (stages.py + core/run_state.py + dashboard/) doğrula
    2. cloudflared kurulu mu kontrol et
    3. Railway servisini bul; çalışıyorsa replicas=0 ile stop et (polling collision'ı önlemek için)
    4. Boş port bul, cloudflared quick tunnel başlat
    5. DASHBOARD_ENABLED=1 ile proje'nin main.py'sini başlat
    6. Paylaşılabilir URL'i ekrana yaz
    7. Ctrl+C → main.py kill, cloudflared kill, Railway start (replicas=1)
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import signal
import socket
import ssl
import sys
import urllib.request
from pathlib import Path

try:
    import certifi  # type: ignore
    _SSL_CTX = ssl.create_default_context(cafile=certifi.where())
except Exception:
    _SSL_CTX = ssl.create_default_context()

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent / "resources"))

from tunnel import cloudflared_available, start_quick_tunnel  # noqa: E402


RAILWAY_GRAPHQL = "https://backboard.railway.com/graphql/v2"


def load_railway_token() -> str | None:
    env_path = ROOT / "_knowledge" / "credentials" / "master.env"
    if not env_path.exists():
        return os.getenv("RAILWAY_TOKEN")
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if line.startswith("RAILWAY_TOKEN=") or line.startswith("RAILWAY_API_TOKEN="):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    return os.getenv("RAILWAY_TOKEN")


def railway_graphql(token: str, query: str, variables: dict | None = None) -> dict:
    req = urllib.request.Request(
        RAILWAY_GRAPHQL,
        data=json.dumps({"query": query, "variables": variables or {}}).encode(),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=20, context=_SSL_CTX) as resp:
        return json.loads(resp.read().decode())


def slugify(folder_name: str) -> str:
    s = folder_name.lower()
    out = []
    for ch in s:
        if ch.isalnum():
            out.append(ch)
        elif ch in ("_", "-", " "):
            out.append("-")
    return "".join(out).strip("-")


def find_railway_service(token: str, project_folder: str) -> dict | None:
    """Folder adına en yakın Railway servisini bul."""
    query = """
    query {
      me {
        projects {
          edges {
            node {
              id
              name
              services {
                edges {
                  node {
                    id
                    name
                    serviceInstances {
                      edges {
                        node {
                          id
                          environmentId
                          numReplicas
                          latestDeployment {
                            id
                            status
                          }
                        }
                      }
                    }
                  }
                }
              }
            }
          }
        }
      }
    }
    """
    try:
        result = railway_graphql(token, query)
    except Exception as e:
        print(f"[uyarı] Railway sorgusu başarısız: {e}", file=sys.stderr)
        return None

    slug = slugify(project_folder)
    best: dict | None = None
    for proj_edge in (result.get("data", {}).get("me", {}) or {}).get("projects", {}).get("edges", []):
        proj = proj_edge["node"]
        for svc_edge in (proj.get("services") or {}).get("edges", []):
            svc = svc_edge["node"]
            svc_slug = slugify(svc["name"])
            if svc_slug == slug:
                # Tam eşleşme
                instances = (svc.get("serviceInstances") or {}).get("edges", [])
                inst = instances[0]["node"] if instances else {}
                return {
                    "project_id": proj["id"],
                    "project_name": proj["name"],
                    "service_id": svc["id"],
                    "service_name": svc["name"],
                    "environment_id": inst.get("environmentId"),
                    "num_replicas": inst.get("numReplicas"),
                    "status": (inst.get("latestDeployment") or {}).get("status"),
                }
            if slug in svc_slug or svc_slug in slug:
                instances = (svc.get("serviceInstances") or {}).get("edges", [])
                inst = instances[0]["node"] if instances else {}
                best = {
                    "project_id": proj["id"],
                    "project_name": proj["name"],
                    "service_id": svc["id"],
                    "service_name": svc["name"],
                    "environment_id": inst.get("environmentId"),
                    "num_replicas": inst.get("numReplicas"),
                    "status": (inst.get("latestDeployment") or {}).get("status"),
                }
    return best


def set_railway_replicas(token: str, service: dict, replicas: int) -> bool:
    mutation = """
    mutation($input: ServiceInstanceUpdateInput!) {
      serviceInstanceUpdate(input: $input)
    }
    """
    variables = {
        "input": {
            "serviceId": service["service_id"],
            "environmentId": service["environment_id"],
            "numReplicas": replicas,
        }
    }
    try:
        result = railway_graphql(token, mutation, variables)
        if result.get("errors"):
            print(f"[uyarı] Replica güncelleme hatası: {result['errors']}", file=sys.stderr)
            return False
        return True
    except Exception as e:
        print(f"[uyarı] Replica güncelleme isteği başarısız: {e}", file=sys.stderr)
        return False


def find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def is_polling_project(project_path: Path) -> bool:
    main_py = project_path / "main.py"
    if not main_py.exists():
        return False
    try:
        content = main_py.read_text(errors="replace")
    except Exception:
        return False
    needles = ("run_polling", "start_polling", "infinity_polling")
    return any(n in content for n in needles)


def validate_demo_integration(project_path: Path) -> list[str]:
    missing = []
    for rel in ("stages.py", "core/run_state.py", "dashboard_server.py", "dashboard/index.html", "dashboard/app.js"):
        if not (project_path / rel).exists():
            missing.append(rel)
    return missing


async def run_demo(project_path: Path, args: argparse.Namespace) -> int:
    missing = validate_demo_integration(project_path)
    if missing:
        print(
            "❌ Bu projeye canlı demo entegre değil. Eksik dosyalar:",
            file=sys.stderr,
        )
        for m in missing:
            print(f"   - {m}", file=sys.stderr)
        print(
            f"\nÖnce şu komutla şablonu kopyala:\n"
            f"   python _skills/canli-demo/sync.py {project_path.relative_to(ROOT)}\n",
            file=sys.stderr,
        )
        return 2

    if not cloudflared_available() and not args.no_tunnel:
        print(
            "❌ cloudflared bulunamadı. Yükleme:\n   brew install cloudflared\n",
            file=sys.stderr,
        )
        return 3

    token = load_railway_token() if not (args.skip_railway or args.mock) else None
    service = None
    if token:
        service = find_railway_service(token, project_path.name)
        if service:
            print(
                f"📡 Railway servisi bulundu: {service['service_name']} "
                f"(replicas={service.get('num_replicas')}, "
                f"status={service.get('status')})"
            )
        else:
            print(f"ℹ️  Railway'de '{project_path.name}' için servis bulunamadı.")
            if is_polling_project(project_path):
                print(
                    "   ⚠️  POLLING COLLISION RİSKİ: Bu proje Telegram polling tabanlı; "
                    "Railway servisi durdurulamadığı için lokal main.py prod ile aynı anda "
                    "polling yapacak. Önce Railway dashboard'tan stop et, sonra --skip-railway ile yeniden çalıştır."
                )

    stopped_for_demo = False
    if service and is_polling_project(project_path):
        current_replicas = service.get("num_replicas") or 0
        if current_replicas >= 1:
            print(f"🛑 Polling tabanlı servis stop ediliyor (collision önlenir)…")
            ok = set_railway_replicas(token, service, 0)
            if ok:
                stopped_for_demo = True
                print("   ✓ Replicas=0")
            else:
                print(
                    "   ⚠️  Stop başarısız. Demo başlatılıyor ama prod ile collision olabilir."
                )

    port = find_free_port()
    print(f"🌐 Lokal port: {port}")

    tunnel_proc = None
    tunnel_url: str | None = None
    if not args.no_tunnel:
        print("🚇 cloudflared quick tunnel başlatılıyor…")
        try:
            tunnel_proc, tunnel_url = await start_quick_tunnel(port)
            print(f"   ✓ {tunnel_url}")
        except Exception as e:
            print(f"   ❌ {e}", file=sys.stderr)
            if stopped_for_demo:
                print("🔄 Railway servisini geri açıyorum…")
                set_railway_replicas(token, service, 1)
            return 4

    env = os.environ.copy()
    env["DASHBOARD_ENABLED"] = "1"
    env["DASHBOARD_PORT"] = str(port)
    env["DASHBOARD_HOST"] = "127.0.0.1"
    if tunnel_url:
        env["DASHBOARD_PUBLIC_URL"] = tunnel_url

    env_file = project_path / ".env"
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            env.setdefault(k.strip(), v.strip().strip('"').strip("'"))

    if args.mock:
        mock_script = Path(__file__).resolve().parent / "mock.py"
        print(f"🎭 MOCK MODE — gerçek pipeline tetiklenmiyor (cwd={project_path.name})…")
        main_proc = await asyncio.create_subprocess_exec(
            sys.executable,
            str(mock_script),
            str(project_path.relative_to(ROOT)),
            "--port",
            str(port),
            cwd=str(ROOT),
            env=env,
        )
    else:
        print(f"🎬 main.py başlatılıyor (cwd={project_path.name})…")
        main_proc = await asyncio.create_subprocess_exec(
            sys.executable,
            "main.py",
            cwd=str(project_path),
            env=env,
        )

    public_url = tunnel_url or f"http://localhost:{port}"
    mode_tag = "MOCK" if args.mock else "LIVE"
    clipboard_msg = ""
    try:
        clip_proc = await asyncio.create_subprocess_exec(
            "pbcopy",
            stdin=asyncio.subprocess.PIPE,
        )
        await clip_proc.communicate(public_url.encode())
        if clip_proc.returncode == 0:
            clipboard_msg = "  📋 URL clipboard'a kopyalandı"
    except FileNotFoundError:
        pass
    print()
    print("━" * 60)
    print(f"🎬 Demo aktif ({mode_tag}): {public_url}")
    print(f"📺 Lokal: http://localhost:{port}")
    if clipboard_msg:
        print(clipboard_msg)
    print("⏹  Ctrl+C ile kapat (Railway otomatik geri açılır)")
    print("━" * 60)
    print()

    stop_requested = False
    loop = asyncio.get_event_loop()

    def _handle_signal() -> None:
        nonlocal stop_requested
        stop_requested = True
        if main_proc.returncode is None:
            main_proc.terminate()

    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, _handle_signal)
        except (NotImplementedError, RuntimeError):
            pass

    try:
        await main_proc.wait()
    finally:
        if tunnel_proc and tunnel_proc.returncode is None:
            tunnel_proc.terminate()
            try:
                await asyncio.wait_for(tunnel_proc.wait(), timeout=5)
            except asyncio.TimeoutError:
                tunnel_proc.kill()

        if stopped_for_demo and token and service:
            print("🔄 Railway servisini geri açıyorum…")
            ok = set_railway_replicas(token, service, 1)
            print("   ✓ Replicas=1" if ok else "   ⚠️  Replicas geri alınamadı; Railway dashboard'tan kontrol et.")

    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Antigravity canlı demo başlatıcı")
    parser.add_argument("project", help="Proje klasör yolu (örn. Projeler/eCom_Reklam_Otomasyonu)")
    parser.add_argument("--no-tunnel", action="store_true", help="cloudflared tunnel açma (sadece lokal)")
    parser.add_argument("--skip-railway", action="store_true", help="Railway stop/start adımını atla")
    parser.add_argument("--mock", action="store_true", help="main.py yerine mock event üreticisini başlat (gerçek pipeline tetiklenmez)")
    args = parser.parse_args()

    project_path = (ROOT / args.project).resolve()
    if not project_path.exists() or not project_path.is_dir():
        print(f"❌ Proje klasörü bulunamadı: {project_path}", file=sys.stderr)
        return 1

    return asyncio.run(run_demo(project_path, args))


if __name__ == "__main__":
    sys.exit(main())
