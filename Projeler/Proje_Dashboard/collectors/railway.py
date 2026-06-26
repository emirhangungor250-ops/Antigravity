"""Railway collector.

Workspace altındaki tüm projeler + servislerin son 30 günlük CPU/RAM
kullanımını çeker ve vCPU·sn + GB·sn formülüyle USD'ye çevirir.

Birim notu: Railway `usage` query'si CPU_USAGE değerini vCPU·minute,
MEMORY_USAGE_GB değerini GB·minute olarak döndürür (gözleme dayalı).
Her servis için birden çok satır gelir (deployment/environment kırılımı);
hepsi toplanır.
"""
from __future__ import annotations

import json
import os
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import requests

GRAPHQL_URL = "https://backboard.railway.com/graphql/v2"

CPU_USD_PER_VCPU_SECOND = 0.00000772
RAM_USD_PER_GB_SECOND = 0.00000386
SECONDS_PER_MINUTE = 60


def _read_railway_token() -> str | None:
    token = os.getenv("RAILWAY_TOKEN")
    if token:
        return token.strip()
    master = Path(__file__).resolve().parents[3] / "_knowledge" / "credentials" / "master.env"
    if not master.exists():
        return None
    for line in master.read_text().splitlines():
        if line.startswith("RAILWAY_TOKEN="):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    return None


def _gql(token: str, query: str, variables: dict[str, Any] | None = None) -> dict[str, Any]:
    payload: dict[str, Any] = {"query": query}
    if variables:
        payload["variables"] = variables
    resp = requests.post(
        GRAPHQL_URL,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


def _workspace_billing(token: str) -> dict[str, Any]:
    """Workspace'in resmi billing özeti — currentUsage + son faturalar."""
    query = """
    query Billing {
      me {
        workspaces {
          id
          name
          customer {
            currentUsage
            billingPeriod { start end }
            invoices {
              invoiceId
              amountDue
              amountPaid
              total
              status
              periodStart
              periodEnd
            }
          }
        }
      }
    }
    """
    try:
        data = _gql(token, query)
    except Exception as e:
        return {"ok": False, "error": str(e)}
    workspaces = (data.get("data") or {}).get("me", {}).get("workspaces") or []
    if not workspaces:
        return {"ok": False, "error": "Workspace yok"}
    ws = workspaces[0]
    cust = ws.get("customer") or {}
    invoices_raw = cust.get("invoices") or []
    invoices = []
    for inv in invoices_raw:
        invoices.append(
            {
                "invoice_id": inv.get("invoiceId"),
                "total_usd": (inv.get("total") or 0) / 100,
                "paid_usd": (inv.get("amountPaid") or 0) / 100,
                "due_usd": (inv.get("amountDue") or 0) / 100,
                "status": inv.get("status"),
                "period_start": inv.get("periodStart"),
                "period_end": inv.get("periodEnd"),
            }
        )
    invoices.sort(key=lambda i: i.get("period_end") or "", reverse=True)
    return {
        "ok": True,
        "current_usage_usd": round(float(cust.get("currentUsage") or 0), 2),
        "billing_period": cust.get("billingPeriod") or {},
        "invoices": invoices,
    }


def _list_workspace_projects(token: str) -> tuple[str | None, list[dict[str, Any]]]:
    query = """
    query Me {
      me {
        workspaces {
          id
          name
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
                    }
                  }
                }
                environments {
                  edges {
                    node {
                      id
                      name
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
    data = _gql(token, query)
    workspaces = (data.get("data") or {}).get("me", {}).get("workspaces") or []
    if not workspaces:
        return None, []
    ws = workspaces[0]
    projects: list[dict[str, Any]] = []
    for proj_edge in (ws.get("projects") or {}).get("edges") or []:
        proj = proj_edge["node"]
        envs = [e["node"] for e in (proj.get("environments") or {}).get("edges") or []]
        production_env = next(
            (e for e in envs if e["name"].lower() == "production"),
            envs[0] if envs else None,
        )
        services = [s["node"] for s in (proj.get("services") or {}).get("edges") or []]
        projects.append(
            {
                "id": proj["id"],
                "name": proj["name"],
                "environment_id": production_env["id"] if production_env else None,
                "services": services,
            }
        )
    return ws["id"], projects


def _usage_by_service(
    token: str,
    workspace_id: str,
    start: datetime,
    end: datetime,
) -> dict[str, dict[str, float]]:
    query = """
    query Usage(
      $measurements: [MetricMeasurement!]!
      $startDate: DateTime!
      $endDate: DateTime!
      $workspaceId: String!
    ) {
      usage(
        measurements: $measurements
        startDate: $startDate
        endDate: $endDate
        workspaceId: $workspaceId
        groupBy: [SERVICE_ID]
      ) {
        measurement
        value
        tags {
          serviceId
        }
      }
    }
    """
    variables = {
        "measurements": ["CPU_USAGE", "MEMORY_USAGE_GB"],
        "startDate": start.isoformat().replace("+00:00", "Z"),
        "endDate": end.isoformat().replace("+00:00", "Z"),
        "workspaceId": workspace_id,
    }
    data = _gql(token, query, variables)
    rows = (data.get("data") or {}).get("usage") or []
    agg: dict[str, dict[str, float]] = defaultdict(lambda: {"cpu_min": 0.0, "ram_gbmin": 0.0})
    for row in rows:
        sid = (row.get("tags") or {}).get("serviceId")
        if not sid:
            continue
        m = row.get("measurement")
        v = float(row.get("value") or 0)
        if m == "CPU_USAGE":
            agg[sid]["cpu_min"] += v
        elif m == "MEMORY_USAGE_GB":
            agg[sid]["ram_gbmin"] += v
    return dict(agg)


def _latest_deployment(
    token: str, service_id: str, environment_id: str | None
) -> dict[str, Any] | None:
    if not environment_id:
        return None
    query = """
    query Deployments($serviceId: String!, $environmentId: String!) {
      deployments(
        first: 1
        input: { serviceId: $serviceId, environmentId: $environmentId }
      ) {
        edges {
          node {
            id
            status
            createdAt
          }
        }
      }
    }
    """
    try:
        data = _gql(
            token,
            query,
            {"serviceId": service_id, "environmentId": environment_id},
        )
    except Exception:
        return None
    edges = ((data.get("data") or {}).get("deployments") or {}).get("edges") or []
    if not edges:
        return None
    return edges[0]["node"]


def collect() -> dict[str, Any]:
    token = _read_railway_token()
    if not token:
        return {"ok": False, "error": "RAILWAY_TOKEN bulunamadı", "services": []}

    # Resmi billing (gerçek dolar)
    billing = _workspace_billing(token)

    try:
        workspace_id, projects = _list_workspace_projects(token)
    except Exception as e:
        return {"ok": False, "error": f"Workspace alınamadı: {e}", "services": []}

    if not workspace_id:
        return {"ok": False, "error": "Workspace bulunamadı", "services": []}

    # Billing period'a hizala (rolling 30 gün yerine)
    period = billing.get("billing_period") or {}
    try:
        start = datetime.fromisoformat((period.get("start") or "").replace("Z", "+00:00"))
        end = datetime.now(timezone.utc)
    except Exception:
        end = datetime.now(timezone.utc)
        start = end - timedelta(days=30)

    try:
        usage_map = _usage_by_service(token, workspace_id, start, end)
    except Exception as e:
        return {"ok": False, "error": f"Usage alınamadı: {e}", "services": []}

    enriched: list[dict[str, Any]] = []
    total_usd = 0.0
    for project in projects:
        for svc in project["services"]:
            sid = svc["id"]
            usage = usage_map.get(sid, {"cpu_min": 0.0, "ram_gbmin": 0.0})
            cpu_usd = usage["cpu_min"] * SECONDS_PER_MINUTE * CPU_USD_PER_VCPU_SECOND
            ram_usd = usage["ram_gbmin"] * SECONDS_PER_MINUTE * RAM_USD_PER_GB_SECOND
            monthly_usd = cpu_usd + ram_usd
            total_usd += monthly_usd
            deployment = _latest_deployment(token, sid, project["environment_id"])
            enriched.append(
                {
                    "service_id": sid,
                    "service_name": svc["name"],
                    "project_id": project["id"],
                    "project_name": project["name"],
                    "environment_id": project["environment_id"],
                    "monthly_usd": round(monthly_usd, 2),
                    "cpu_usd": round(cpu_usd, 2),
                    "ram_usd": round(ram_usd, 2),
                    "cpu_min": round(usage["cpu_min"], 2),
                    "ram_gbmin": round(usage["ram_gbmin"], 2),
                    "latest_deployment": deployment,
                }
            )

    enriched.sort(key=lambda s: -s["monthly_usd"])

    # Resmi billing toplam ile servis tahminleri arası fark (network/volume payı)
    official_total = billing.get("current_usage_usd", 0.0) if billing.get("ok") else None
    estimated_total = round(total_usd, 2)
    delta = round((official_total or 0) - estimated_total, 2) if official_total else None

    return {
        "ok": True,
        "workspace_id": workspace_id,
        "services": enriched,
        "estimated_total_usd": estimated_total,  # servis-bazlı CPU+RAM tahmini
        "official_current_usd": official_total,  # Railway'in kendi tutarı
        "billing_period": period,
        "invoices": billing.get("invoices") or [],
        "estimate_vs_official_delta": delta,
        "window_start": start.isoformat(),
        "window_end": end.isoformat(),
    }


if __name__ == "__main__":
    result = collect()
    print(json.dumps(result, indent=2, default=str))
