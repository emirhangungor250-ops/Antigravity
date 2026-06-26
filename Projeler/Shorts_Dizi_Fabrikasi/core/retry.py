"""
Retry Utility — Merkezi Yeniden Deneme Mekanizmasi
=====================================================
Tum API cagrilari icin exponential backoff ile retry.
Gecici hatalar (timeout, 429, 5xx) otomatik yeniden denenir.
Kalici hatalar (403, 404) aninda firlatilir.
"""

import time
import functools
import logging
from typing import Optional

import requests

log = logging.getLogger("Retry")

# Yeniden denenecek HTTP status kodlari
# NOT: 401 dahil — bazi servisler gecici 401 donebiliyor
# NOT: 512 dahil — Kie AI reverse proxy upstream asiri yuklenme kodu
RETRYABLE_STATUS_CODES = {401, 408, 429, 500, 502, 503, 504, 512}


class RateLimitError(Exception):
    """
    Rate limit (HTTP 429) hatasi icin ozel exception.

    HTTPError firlatamayan servisler bu exception'i firlatarak retry
    decorator'unun Retry-After bilincli backoff mantigindan yararlanir.
    """

    def __init__(self, message: str = "Rate limit exceeded", retry_after: Optional[float] = None):
        super().__init__(message)
        self.retry_after = retry_after


# Yeniden denenecek exception turleri
RETRYABLE_EXCEPTIONS = (
    requests.exceptions.Timeout,
    requests.exceptions.ConnectionError,
    ConnectionResetError,
    TimeoutError,
    OSError,  # Network unreachable vb.
    RateLimitError,
)


def retry_api_call(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 30.0,
    backoff_factor: float = 2.0,
    operation_name: str = "",
):
    """
    API cagrilari icin retry decorator.

    Args:
        max_retries: Maximum deneme sayisi (ilk deneme dahil DEGIL)
        base_delay: Ilk bekleme suresi (saniye)
        max_delay: Maximum bekleme suresi (saniye)
        backoff_factor: Her denemede bekleme carpani
        operation_name: Log'larda gorunecek operasyon adi
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            op = operation_name or func.__qualname__
            last_exception = None

            for attempt in range(1, max_retries + 2):  # +2: ilk deneme + retry'lar
                try:
                    return func(*args, **kwargs)
                except requests.exceptions.HTTPError as e:
                    status = e.response.status_code if e.response is not None else 0
                    # Retryable kontrol: sabit liste VEYA genel 5xx araligi
                    is_retryable = status in RETRYABLE_STATUS_CODES or (500 <= status <= 599)
                    if not is_retryable:
                        raise
                    last_exception = e
                    if attempt <= max_retries:
                        delay = min(base_delay * (backoff_factor ** (attempt - 1)), max_delay)
                        # 429 rate limit → Retry-After header varsa onu kullan
                        if status == 429 and e.response is not None:
                            retry_after = e.response.headers.get("Retry-After")
                            if retry_after:
                                try:
                                    delay = min(float(retry_after), max_delay)
                                except ValueError:
                                    log.warning("Retry-After header parse edilemedi", exc_info=True)
                        log.warning(
                            f"{op}: HTTP {status}, retry {attempt}/{max_retries} "
                            f"({delay:.1f}s sonra)"
                        )
                        time.sleep(delay)
                    else:
                        raise
                except RETRYABLE_EXCEPTIONS as e:
                    last_exception = e
                    if attempt <= max_retries:
                        delay = min(base_delay * (backoff_factor ** (attempt - 1)), max_delay)
                        retry_after = getattr(e, "retry_after", None)
                        if retry_after is not None:
                            try:
                                delay = min(float(retry_after), max_delay)
                            except (ValueError, TypeError):
                                log.warning("retry_after attribute parse edilemedi", exc_info=True)
                        log.warning(
                            f"{op}: {type(e).__name__}, retry {attempt}/{max_retries} "
                            f"({delay:.1f}s sonra)"
                        )
                        time.sleep(delay)
                    else:
                        raise
                except Exception:
                    # Bilinmeyen/kalici hata — retry yapma
                    raise

            if last_exception:
                raise last_exception

        return wrapper
    return decorator
