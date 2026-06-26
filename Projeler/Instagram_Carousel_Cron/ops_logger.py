"""ops_logger — Twitter_Text_Paylasim/ops_logger.py'den birebir kopya.

Tüm Antigravity projelerinde aynı pattern; merkezi Notion Operations Log'a yazar.
"""

import os
import sys
import logging
import requests
import traceback
import threading
import queue
from datetime import datetime, timezone


def _get_env(key, default=""):
    val = os.environ.get(key)
    if val:
        return val
    try:
        from env_loader import get_env as _loader_get
        return _loader_get(key, default)
    except ImportError:
        pass
    return default


NOTION_TOKEN = _get_env("NOTION_SOCIAL_TOKEN") or _get_env("NOTION_API_TOKEN")
NOTION_DB_OPS_LOG = _get_env("NOTION_DB_OPS_LOG", "")


class _NotionLogWorker(threading.Thread):
    def __init__(self, log_queue, token, db_id):
        super().__init__(daemon=True)
        self.log_queue = log_queue
        self.token = token
        self.db_id = db_id
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Notion-Version": "2022-06-28",
            "Content-Type": "application/json",
        }

    def run(self):
        while True:
            try:
                log_data = self.log_queue.get()
                if log_data is None:
                    break
                self._send_to_notion(log_data)
                self.log_queue.task_done()
            except Exception as e:
                print(f"[OpsLogger Error] Notion'a log gönderilemedi: {e}", file=sys.stderr)
                try:
                    self.log_queue.task_done()
                except ValueError:
                    pass

    def _send_to_notion(self, log_data):
        title = (log_data.get("title") or "")[:250]
        message = (log_data.get("message") or "")[:1990]
        level = log_data.get("level", "INFO")
        component = log_data.get("component", "Pipeline")
        project = log_data.get("project", "Unknown")
        details = (log_data.get("details") or "")[:1990]

        payload = {
            "parent": {"database_id": self.db_id},
            "properties": {
                "Title": {"title": [{"text": {"content": title}}]},
                "Message": {"rich_text": [{"text": {"content": message}}]},
                "Zaman": {"date": {"start": datetime.now(timezone.utc).isoformat()}},
                "Level": {"select": {"name": level}},
                "Component": {"select": {"name": component}},
                "Project": {"select": {"name": project}},
            },
        }

        if details:
            payload["properties"]["Details"] = {
                "rich_text": [{"text": {"content": details}}]
            }

        response = requests.post(
            "https://api.notion.com/v1/pages",
            headers=self.headers,
            json=payload,
            timeout=15,
        )
        response.raise_for_status()


class OpsLogger:
    def __init__(self, project_name: str, component: str = "Pipeline"):
        self.project_name = project_name
        self.component = component
        self.token = NOTION_TOKEN
        self.db_id = NOTION_DB_OPS_LOG

        self._queue = queue.Queue()
        self._worker = None

        if self.token and self.db_id:
            self._worker = _NotionLogWorker(self._queue, self.token, self.db_id)
            self._worker.start()
        else:
            print(
                f"[OpsLogger] ⚠️ NOTION token/DB ID eksik — sadece console. "
                f"(token={'var' if self.token else 'YOK'}, db={'var' if self.db_id else 'YOK'})"
            )

        self._std = logging.getLogger(f"OpsLog_{project_name}_{component}")
        if not self._std.handlers:
            handler = logging.StreamHandler(sys.stdout)
            formatter = logging.Formatter(
                "%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
            handler.setFormatter(formatter)
            self._std.addHandler(handler)
            self._std.setLevel(logging.INFO)
            # Watchdog FP fix: root logger'a propagate etme — basicConfig stderr handler'ına çift düşmesin
            self._std.propagate = False

    def _enqueue(self, level, title, message="", details=""):
        if self._worker:
            self._queue.put({
                "level": level,
                "title": title,
                "message": message,
                "component": self.component,
                "project": self.project_name,
                "details": details,
            })

    def info(self, title, message=""):
        self._std.info(f"{title}: {message}" if message else title)
        self._enqueue("INFO", title, message)

    def success(self, title, message=""):
        self._std.info(f"✅ {title}: {message}" if message else f"✅ {title}")
        self._enqueue("SUCCESS", title, message)

    def warning(self, title, message="", details=""):
        self._std.warning(f"⚠️ {title}: {message}" if message else f"⚠️ {title}")
        self._enqueue("WARNING", title, message, details=details)

    def error(self, title, exception=None, message=""):
        details = ""
        if exception:
            details = "".join(
                traceback.format_exception(type(exception), exception, exception.__traceback__)
            )
        self._std.error(f"❌ {title}: {message}\n{details}" if details else f"❌ {title}: {message}")
        self._enqueue("ERROR", title, message, details=details)

    def wait_for_logs(self):
        if self._worker:
            self._queue.join()


_instances: dict = {}


def get_ops_logger(project_name: str, component: str = "Pipeline") -> OpsLogger:
    key = f"{project_name}_{component}"
    if key not in _instances:
        _instances[key] = OpsLogger(project_name, component)
    return _instances[key]


def wait_all_loggers():
    for key, logger in _instances.items():
        logger.wait_for_logs()
