"""
Railway Log Checker — Akıllı Watchdog için Railway deployment log analizi.
Son N saatteki ERROR pattern'larını tarar, false-positive filtrelemesi yapar.
servis-izleyici skill'inden Akilli_Watchdog'a taşındı (2026-05-07).
"""
import re
import requests
from datetime import datetime, timezone, timedelta
from adapter_logger import get_logger

from config import Config

logger = get_logger(__name__)


ERROR_PATTERNS = re.compile(
    r"(ERROR|Exception|Traceback|FAILED|CRITICAL|panic|fatal|killed|OOMKilled|segfault)",
    re.IGNORECASE,
)

FALSE_POSITIVE_PATTERNS = re.compile(
    r"("
    r"Score is exceptionally high"
    r"|Accepting this as the final image"
    r"|exceptionally high.*accepting"
    r"|Successfully"
    r"|Critique:.*Excellent"
    r"|Critique:.*CRITICAL"
    r"|Excellent execution"
    r"|Log verisi alınamadı"
    r"|Using Prompt"
    r"|CRITICAL FACE IDENTITY"
    r"|telegram\.error\.Conflict"
    r"|terminated by other getUpdates"
    r"|only one bot instance"
    r"|No error handlers are registered.*logging exception"
    r"|1 sorun tespit edildi"
    r"|OpsLog_Akilli_Watchdog"
    r"|INFO:\s+(GET|POST|PUT|DELETE)\s+/[\w\-/]*(failed|error)"
    r"|/webhook/[\w\-]*(failed|error)"
    r"|daha önce Failed — yeniden denenecek"
    r"|Notion log yazıldı.*Failed\)"
    r"|\[wa-failed\]"
    r"|wa-failed"
    r"|reason.*Bana mesaj gonderme"
    r"|Telegram handler hatası:\s*(Bad Gateway|Timed out|NetworkError|httpx|Connection|Gateway Time-out|Service Unavailable)"
    r"|Telegram transient hatası"
    # Görsel üretim pipeline'ının normal retry/fallback davranışı
    r"|Self-review FAILED"
    r"|Review Passed: False"
    r"|Catbox upload failed"
    r"|Catbox network error"
    r"|Catbox invalid response"
    r"|Falling back to ImgBB"
    r"|Aborting because Catbox upload failed"
    # WhatsApp Onboarding — state machine'in info seviyesindeki status=error placeholder'ı
    r"|Placeholder kayıt yaratıldı"
    # YouTube transcript — Railway IP banlarında pipeline Notion script fallback'ına düşer
    r"|Transkript yok \("
    r"|Transkript IP-block"
    r"|youtube_transcript_api\._errors\.RequestBlocked"
    r"|Could not retrieve a transcript for the video"
    r"|Working around IP bans"
    r")",
    re.IGNORECASE,
)


def query_last_deployment(service_id: str) -> dict | None:
    """Son deployment'ın {id, status, createdAt} bilgisini döner."""
    if not Config.RAILWAY_TOKEN:
        return None

    query = """
    query($serviceId: String!) {
        deployments(input: { serviceId: $serviceId }, first: 1) {
            edges { node { id status createdAt } }
        }
    }
    """
    headers = {
        "Authorization": f"Bearer {Config.RAILWAY_TOKEN}",
        "Content-Type": "application/json",
    }
    try:
        resp = requests.post(
            Config.RAILWAY_GRAPHQL_URL,
            json={"query": query, "variables": {"serviceId": service_id}},
            headers=headers,
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
        edges = (((data.get("data") or {}).get("deployments") or {}).get("edges")) or []
        if edges:
            return edges[0].get("node")
    except Exception as e:
        logger.warning(f"Railway deployment sorgusu başarısız: {e}")
    return None


def query_deployment_logs(deployment_id: str, hours: int = 24, limit: int = 500) -> list[dict]:
    """
    Belirtilen deployment'ın son N saatteki loglarını çeker.
    Returns: List of log entries veya [] (sorun varsa).
    """
    if not Config.RAILWAY_TOKEN:
        return []

    start_date = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()
    query = """
    query($deploymentId: String!, $limit: Int, $startDate: DateTime) {
        deploymentLogs(deploymentId: $deploymentId, limit: $limit, startDate: $startDate) {
            message
            severity
            timestamp
        }
    }
    """
    headers = {
        "Authorization": f"Bearer {Config.RAILWAY_TOKEN}",
        "Content-Type": "application/json",
    }
    variables = {"deploymentId": deployment_id, "limit": limit, "startDate": start_date}
    try:
        resp = requests.post(
            Config.RAILWAY_GRAPHQL_URL,
            json={"query": query, "variables": variables},
            headers=headers,
            timeout=20,
        )
        resp.raise_for_status()
        data = resp.json()
        if "errors" in data:
            err = data["errors"][0].get("message", "GraphQL error")
            logger.warning(f"deploymentLogs sorgusu hata döndü: {err}")
            return []
        logs = (data.get("data") or {}).get("deploymentLogs") or []
        return logs if isinstance(logs, list) else []
    except Exception as e:
        logger.warning(f"deploymentLogs HTTP hatası: {e}")
        return []


def analyze_logs(logs: list[dict], hours: int = 24) -> dict:
    """
    Logları ERROR pattern'larına göre tarar, false-positive'leri filtreler.
    Returns: {"error_count": int, "errors": [str (son 10)], "warning_count": int}
    """
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    errors: list[str] = []
    warnings: list[str] = []

    for entry in logs:
        if not isinstance(entry, dict):
            continue
        msg = entry.get("message", "") or ""
        severity = (entry.get("severity") or "").upper()
        ts_str = entry.get("timestamp", "")
        ts = None
        if ts_str:
            try:
                ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
            except (ValueError, TypeError):
                ts = None
        if ts and ts < cutoff:
            continue

        if not ERROR_PATTERNS.search(msg):
            continue
        if FALSE_POSITIVE_PATTERNS.search(msg):
            continue

        # Severity açıkça INFO/DEBUG/NOTICE ise — message'ta "error" kelimesi
        # geçse bile (status=error gibi state field'ları) alarm çalma.
        # Sadece gerçek crash sinyali olan Exception/Traceback/panic/OOMKilled
        # varsa istisna olarak say.
        if severity in ("INFO", "DEBUG", "TRACE", "NOTICE"):
            if not re.search(r"(Exception|Traceback|panic|fatal|killed|OOMKilled|segfault)",
                             msg, re.IGNORECASE):
                continue

        if severity in ("ERROR", "CRITICAL", "FATAL"):
            errors.append(msg.strip()[:200])
        elif severity == "WARNING" or "warning" in msg.lower():
            warnings.append(msg.strip()[:200])
        else:
            errors.append(msg.strip()[:200])

    return {
        "error_count": len(errors),
        "errors": errors[-10:],
        "warning_count": len(warnings),
    }


def check_railway_logs(hours: int = 24) -> list[dict]:
    """
    Tüm izlenen Railway servislerinin son deployment'larını tarar,
    son N saatteki ERROR'ları toplar.

    Returns:
        list[dict]: [{"name", "service_id", "deploy_status", "error_count",
                      "errors": [str], "issue": str | None}]
    """
    if not Config.RAILWAY_TOKEN:
        logger.warning("⚠️ RAILWAY_TOKEN tanımlı değil, log tarama atlandı")
        return []

    services = Config.get_railway_service_ids()
    if not services:
        return []

    results: list[dict] = []
    for svc in services:
        name = svc["name"]
        sid = svc["service_id"]

        deployment = query_last_deployment(sid)
        if not deployment:
            results.append({
                "name": name,
                "service_id": sid,
                "deploy_status": "PROBE_ERROR",
                "error_count": 0,
                "errors": [],
                "issue": None,
            })
            continue

        deploy_status = deployment.get("status", "UNKNOWN")
        deployment_id = deployment.get("id")

        if not deployment_id:
            results.append({
                "name": name,
                "service_id": sid,
                "deploy_status": deploy_status,
                "error_count": 0,
                "errors": [],
                "issue": None,
            })
            continue

        logs = query_deployment_logs(deployment_id, hours=hours)
        analysis = analyze_logs(logs, hours=hours)
        err_count = analysis["error_count"]

        issue = None
        if err_count > 0:
            errs_preview = "\n".join(f"  • {e}" for e in analysis["errors"][:3])
            issue = (
                f"🚨 [{name}] Son {hours} saatte {err_count} hata:\n{errs_preview}"
            )

        logger.info(
            f"  {'⚠️' if err_count else '✅'} {name} → {deploy_status}, "
            f"son {hours}h: {err_count} hata"
        )

        results.append({
            "name": name,
            "service_id": sid,
            "deploy_status": deploy_status,
            "error_count": err_count,
            "errors": analysis["errors"],
            "issue": issue,
        })

    return results
