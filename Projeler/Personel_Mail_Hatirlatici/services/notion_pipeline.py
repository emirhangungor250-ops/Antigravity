"""
Opsiyonel: Bir Notion pipeline DB'sinden "hareket bekleyen" kartları çeker.

Hedef: Bazı işler mail dışı kanaldan (WhatsApp, telefon vb.) gelip doğrudan
bir Notion pipeline DB'sine düşebilir. Mail digest'i bunları görmüyor. Bu modül
pipeline DB'sini sorgulayıp belirli status'lardaki kartları toplar.

Bu modül tamamen opsiyoneldir — NOTION_DB_PIPELINE set edilmemişse atlanır.

YAPILANDIRMA (kendi Notion şemana göre değiştir):
- NOTION_DB_PIPELINE: pipeline DB id'si
- PIPELINE_TARGET_STATUSES: hangi Status değerlerinin "hareket bekliyor" sayılacağı
  (virgülle ayrılmış; .env'de tanımlanır)
- PIPELINE_COLLAB_PROP: kartın "ilgili taraf" rich-text property adı
  (Notion DB'ndeki kolon adı — örn. "Müşteri", "Marka", "Taraf")
"""

import os
import json
import logging
import unicodedata
import urllib.request
import urllib.error
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

NOTION_API_BASE = "https://api.notion.com/v1"
NOTION_VERSION = "2022-06-28"

# TODO: Kendi pipeline DB'ndeki Status değerlerine göre düzenle.
# .env'de PIPELINE_TARGET_STATUSES="Hazır,Devam Ediyor,Onay Bekliyor" şeklinde override edilebilir.
TARGET_STATUSES = [
    s.strip()
    for s in os.environ.get(
        "PIPELINE_TARGET_STATUSES",
        "Hazır,Devam Ediyor,Onay Bekliyor",
    ).split(",")
    if s.strip()
]

# Notion DB'ndeki "ilgili taraf" kolonunun adı.
COLLAB_PROP = os.environ.get("PIPELINE_COLLAB_PROP", "Taraf")


def _token() -> Optional[str]:
    return os.environ.get("NOTION_TOKEN")


def _db_id() -> Optional[str]:
    return os.environ.get("NOTION_DB_PIPELINE")


def _headers() -> Dict[str, str]:
    return {
        "Authorization": f"Bearer {_token()}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json",
    }


def _request(method: str, path: str, payload: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
    if not _token():
        logger.warning("Notion token yok — pipeline tracker devre dışı")
        return None
    url = f"{NOTION_API_BASE}{path}"
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    for k, v in _headers().items():
        req.add_header(k, v)
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        logger.error(f"Notion pipeline {method} {path} {e.code}: {body[:300]}")
        return None
    except Exception as e:
        logger.error(f"Notion pipeline {method} {path} hata: {e}")
        return None


def normalize_brand(s: Optional[str]) -> str:
    """Brand karşılaştırması için: küçük harf, NFKD, harf-rakam dışı kaldır."""
    if not s:
        return ""
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode("ascii")
    return "".join(ch for ch in s.lower() if ch.isalnum())


def _get_title(props: Dict[str, Any], key: str) -> str:
    arr = (props.get(key) or {}).get("title", [])
    if not arr:
        return ""
    return "".join(b.get("text", {}).get("content", "") for b in arr)


def _get_rich_text(props: Dict[str, Any], key: str) -> str:
    arr = (props.get(key) or {}).get("rich_text", [])
    if not arr:
        return ""
    return "".join(b.get("text", {}).get("content", "") for b in arr)


def _get_select(props: Dict[str, Any], key: str) -> Optional[str]:
    s = (props.get(key) or {}).get("select")
    return s.get("name") if s else None


def _parse_card(page: Dict[str, Any]) -> Dict[str, Any]:
    props = page.get("properties", {})
    return {
        "_page_id": page.get("id"),
        "page_url": page.get("url"),
        "name": _get_title(props, "Name"),
        # COLLAB_PROP env'inden okunur — kendi Notion DB'ndeki kolon adına göre ayarla.
        "collab": _get_rich_text(props, COLLAB_PROP),
        "status": _get_select(props, "Status"),
    }


def query_active_brands() -> List[Dict[str, Any]]:
    """TARGET_STATUSES içindeki status'lardaki tüm pipeline kartlarını döner."""
    db_id = _db_id()
    if not db_id:
        logger.info("NOTION_DB_PIPELINE set edilmemiş — pipeline tarama atlandı")
        return []

    or_filters = [{"property": "Status", "select": {"equals": s}} for s in TARGET_STATUSES]
    results: List[Dict[str, Any]] = []
    cursor = None
    while True:
        payload: Dict[str, Any] = {
            "filter": {"or": or_filters},
            "page_size": 100,
        }
        if cursor:
            payload["start_cursor"] = cursor
        res = _request("POST", f"/databases/{db_id}/query", payload)
        if not res:
            break
        for page in res.get("results", []):
            results.append(_parse_card(page))
        if not res.get("has_more"):
            break
        cursor = res.get("next_cursor")

    logger.info(f"Pipeline: {len(results)} aktif kart")
    return results
