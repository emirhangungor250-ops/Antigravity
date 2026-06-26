"""Notion DB sayaçları.

İzlemek istediğin Notion DB'leri için "anlamlı tek sayı" üretir
(örn. kaç draft onay bekliyor, bugün kaç kayıt eklendi, bugün kaç hata).

TODO: Aşağıdaki `DB_SPECS` ve `DB_METRICS` yapılarını kendi Notion
DB'lerinle doldur. Pakette iki örnek DB tanımı bırakıldı.

Token: NOTION_SOCIAL_TOKEN birincil. Farklı bir workspace'teki
DB'ler için NOTION_API_TOKEN kullanılabilir.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import requests

from ._env import get as env_get

NOTION_API = "https://api.notion.com/v1"
HEADERS_VERSION = "2022-06-28"


def _query_db(token: str, db_id: str, body: dict | None = None) -> dict[str, Any]:
    if not db_id:
        return {"results": [], "has_more": False}
    r = requests.post(
        f"{NOTION_API}/databases/{db_id}/query",
        headers={
            "Authorization": f"Bearer {token}",
            "Notion-Version": HEADERS_VERSION,
            "Content-Type": "application/json",
        },
        json=body or {"page_size": 100},
        timeout=30,
    )
    if r.status_code != 200:
        raise RuntimeError(f"Notion {r.status_code}: {r.text[:200]}")
    return r.json()


def _today_iso() -> str:
    return datetime.now(timezone.utc).date().isoformat()


def _row_status(row: dict, property_name: str = "Status") -> str | None:
    props = row.get("properties") or {}
    prop = props.get(property_name)
    if not prop:
        return None
    if prop.get("type") == "status":
        return (prop.get("status") or {}).get("name") or "Yok"
    if prop.get("type") == "select":
        return (prop.get("select") or {}).get("name") or "Yok"
    if prop.get("type") == "rich_text":
        chunks = prop.get("rich_text") or []
        return chunks[0]["plain_text"] if chunks else "Yok"
    return None


def _count_by_status(rows: list[dict], property_name: str = "Status") -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        name = _row_status(row, property_name)
        if name is None:
            continue
        counts[name] = counts.get(name, 0) + 1
    return counts


def _count_by_status_today(rows: list[dict], property_name: str = "Status") -> dict[str, int]:
    """Sadece bugün oluşturulan satırların status kırılımı."""
    today = _today_iso()
    counts: dict[str, int] = {}
    for row in rows:
        if not (row.get("created_time") or "").startswith(today):
            continue
        name = _row_status(row, property_name)
        if name is None:
            continue
        counts[name] = counts.get(name, 0) + 1
    return counts


def _new_today(rows: list[dict]) -> int:
    today = _today_iso()
    return sum(1 for r in rows if (r.get("created_time") or "").startswith(today))


MAX_PAGES = 10  # 1000 satır cap


def _safe_db(
    token: str,
    db_id: str,
    label: str,
    status_property: str = "Status",
) -> dict[str, Any]:
    """Bir DB'yi sorgula ve sayım çıkar. Hata olursa hatalı kayıt döner."""
    if not db_id:
        return {"ok": False, "error": f"{label} DB ID yok", "label": label}
    if not token:
        return {"ok": False, "error": f"{label} token yok", "label": label}
    try:
        results: list[dict] = []
        cursor: str | None = None
        truncated = False
        for page_idx in range(MAX_PAGES):
            body: dict = {"page_size": 100}
            if cursor:
                body["start_cursor"] = cursor
            data = _query_db(token, db_id, body)
            results.extend(data.get("results") or [])
            if not data.get("has_more"):
                break
            cursor = data.get("next_cursor")
            if page_idx == MAX_PAGES - 1 and data.get("has_more"):
                truncated = True
        return {
            "ok": True,
            "label": label,
            "total": len(results),
            "truncated": truncated,
            "new_today": _new_today(results),
            "status_counts": _count_by_status(results, status_property),
            "today_status_counts": _count_by_status_today(results, status_property),
            "rows": results,  # render layer ihtiyaca göre kullanır
        }
    except Exception as e:
        return {"ok": False, "label": label, "error": str(e)}


# Her DB için "anlamlı tek sayı" tanımı.
# Anlamlı = aksiyon gerektiren ya da bugünkü hareketi gösteren sayı.
# Kümülatif DB toplamı (sadece büyüyen, aksiyon anlamı olmayan) KULLANILMAZ.
#
# Desteklenen metrik tipleri (öncelik sırasıyla):
#   primary_status: tek bir status adının sayısı
#   status_match:   status adında bu alt-dizgelerden biri geçenlerin toplamı
#   today_status_match: aynısı ama sadece bugünkü kayıtlar
#   use_today:      bugün eklenen kayıt sayısı (new_today)
# label: o sayının ne anlama geldiği (ürün dilinde)
# show_failed: True ise "Failed" status sayısı ayrıca gösterilir
#
# TODO: Aşağıdaki anahtarları (DB_SPECS'teki label'larla aynı olmalı)
# kendi DB'lerine göre doldur. İki örnek bırakıldı.
DB_METRICS = {
    "Örnek Onay Listesi": {"primary_status": "Draft", "label": "draft, onay bekliyor"},
    "Örnek Log DB": {
        "today_status_match": ["error", "warn", "hata", "uyar", "fail"],
        "label": "bugün hata/uyarı",
    },
}

# Per-DB status property name override (default "Status")
STATUS_PROPERTY = {
    # ör: "Örnek Onay Listesi": "Durum",
}


def _sum_status_match(counts: dict[str, int], needles: list[str]) -> int:
    return sum(
        n for name, n in counts.items()
        if any(needle in name.lower() for needle in needles)
    )


def _db_metric(item: dict) -> dict:
    """Sade 'anlamlı tek sayı' üretir.

    Kümülatif total kullanmaz — her DB için aksiyon ya da günlük hareket
    anlamı taşıyan bir sayı seçer. Metrik 0 ise bugünkü üretime düşer.
    """
    label_key = item.get("label", "")
    cfg = DB_METRICS.get(label_key, {})
    sc = item.get("status_counts") or {}
    tsc = item.get("today_status_counts") or {}
    new_today = item.get("new_today", 0)

    primary = 0
    label = cfg.get("label", "kayıt")

    if cfg.get("primary_status"):
        primary = sc.get(cfg["primary_status"], 0)
    elif cfg.get("status_match"):
        primary = _sum_status_match(sc, cfg["status_match"])
        if primary == 0 and not sc:
            # Status alanı hiç yok — bugünkü üretime düş
            primary = new_today
            label = "bugün üretildi"
    elif cfg.get("today_status_match"):
        primary = _sum_status_match(tsc, cfg["today_status_match"])
    elif cfg.get("use_today"):
        primary = new_today

    return {
        "primary": primary,
        "label": label,
        "failed_count": sc.get("Failed", 0) if cfg.get("show_failed") else 0,
    }


def collect() -> dict[str, Any]:
    social_token = env_get("NOTION_SOCIAL_TOKEN")
    api_token = env_get("NOTION_API_TOKEN")

    # TODO: İzlemek istediğin Notion DB'lerini buraya ekle.
    # Her satır: (görünen label, DB ID'sini taşıyan env var adı, token).
    # label değeri DB_METRICS sözlüğündeki anahtarla aynı olmalı.
    # İki örnek satır bırakıldı.
    DB_SPECS = [
        ("Örnek Onay Listesi", "NOTION_DB_ORNEK_ONAY", social_token),
        ("Örnek Log DB", "NOTION_DB_ORNEK_LOG", social_token),
    ]

    items = []
    for label, env_key, token in DB_SPECS:
        db_id = env_get(env_key)
        status_prop = STATUS_PROPERTY.get(label, "Status")
        result = _safe_db(token, db_id, label, status_prop)
        result.pop("rows", None)
        result["env_key"] = env_key
        result["db_id"] = db_id
        if db_id:
            clean_id = db_id.replace("-", "")
            result["notion_url"] = f"https://www.notion.so/{clean_id}"
        if result.get("ok"):
            result["patron_metric"] = _db_metric(result)
        items.append(result)

    ok_count = sum(1 for x in items if x.get("ok"))
    return {
        "ok": ok_count > 0,
        "items": items,
        "ok_count": ok_count,
        "total_count": len(items),
    }


if __name__ == "__main__":
    import json
    print(json.dumps(collect(), indent=2, default=str))
