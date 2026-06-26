"""Mesaj birleştirme / burst coalesce (D1) — abone-başı kuyruk + tek worker.

Sorun: Misafir tek düşünceyi 3-4 ayrı mesaj olarak peş peşe atar ("merhaba" / "fiyat" /
"2 yetişkin" / "20 ağustos"). Her birine ayrı ayrı cevap vermek hem maliyetli hem doğal değil.
Çözüm: İlk mesaj geldiğinde kısa bir pencere açılır; o pencerede gelen artçı mesajlar toplanır,
TEK işleme + TEK cevaba birleştirilir.

Mimari (Railway gerçeği): numReplicas=1, sleepApplication=false → tek worker, in-process state
GÜVENLİ. Coalesce worker'ları KENDİ ayrılmış ThreadPoolExecutor'unda koşar (anyio'nun ortak
webhook/Phase-1 thread havuzunu açlığa düşürmez).

Bu modül SADECE zamanlama yapar (LLM maliyeti YOK). Medya çözümü + ajan + teslim, dışarıdan
verilen `process_fn(user_id, platform, raw_messages)` callback'inde yapılır → test edilebilir,
main.py'ın iş mantığı buraya sızmaz.

Doğruluk modeli (yarış güvenliği):
  Tek paylaşılan kilit `_registry_lock` HEM kuyrukları HEM "bu abone için worker aktif mi"
  bayrağını korur. "Worker başlat" kararı (enqueue) ile "worker'ı emekli et" kararı (worker
  finally) AYNI kritik bölümde kuyruk-boş-mu kontrolüyle birlikte alınır. Böylece eski tasarımın
  TOCTOU açıkları kapanır:
    - Devir boşluğu: worker kuyruğu "boş" görüp emekli olurken araya giren mesaj kaybolmaz —
      worker bayrağı kaldırma kararını kuyruk gerçekten boşken aynı lock altında verir; boş
      değilse emekli OLMAZ, döngüye geri döner.
    - Yetim kilit: worker ömrü artık tek bağlama (worker thread'inin kendisi) bağlı. Kilit ayrı
      bir bağlamda (enqueue) alınıp başka bağlamda bırakılmıyor. Worker thread'i çalışmaya
      başlamadan AKTİF işaretlenir; bir submit başarısız olursa enqueue bayrağı geri alır.
    - Sınırsız bellek: emekli olurken kuyruk gerçekten boşsa `_queues`/`_active` girdileri AYNI
      kritik bölümde silinir.
"""

from __future__ import annotations

import logging
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Callable

from config import CONFIG

log = logging.getLogger("hotel-chat.coalesce")

# İşleme callback'i imzası: (user_id, platform, raw_messages: list[str]) -> None
ProcessFn = Callable[[str, str, list], None]

# Abone-başı durum. _registry_lock HEM _queues HEM _active'i korur (tek kritik bölüm).
# _active[user_id] = True → o abone için bir coalesce worker şu an çalışıyor (yeni webhook
# sadece kuyruğa ekler). Bayrak yoksa/False → bu webhook worker rolünü üstlenir.
_queues: dict[str, list[str]] = {}
_active: dict[str, bool] = {}
_registry_lock = threading.Lock()

# Coalesce worker'ları için AYRILMIŞ havuz: anyio'nun webhook gövde-ayrıştırma ve /price
# sync thread'lerini paylaşan ortak havuzunu (40 token) tüketmez. Worker uzun süre bloklar
# (pencere bekleme + whisper/vision/Supabase/ManyChat ağ çağrıları) — bu yüzden ayrı havuz.
_EXECUTOR = ThreadPoolExecutor(
    max_workers=max(1, CONFIG.coalesce_pool_size),
    thread_name_prefix="coalesce",
)


def _initial_sec() -> float:
    return CONFIG.coalesce_initial_ms / 1000.0


def _straggler_sec() -> float:
    return CONFIG.coalesce_straggler_ms / 1000.0


def _drain_queue_locked(user_id: str) -> list[str]:
    """Kuyruğu atomik boşalt, içeriği döndür. ÇAĞIRAN _registry_lock'u tutmalı."""
    q = _queues.get(user_id)
    if not q:
        return []
    items = q[:]
    q.clear()
    return items


def enqueue(user_id: str, platform: str, message: str,
            process_fn: ProcessFn, background_add=None) -> None:
    """Webhook'tan çağrılır. Mesajı kuyruğa ekler; o abone için coalesce worker
    çalışmıyorsa worker'ı ayrılmış havuzda başlatır, çalışıyorsa SADECE kuyruğa bırakır.

    background_add: test'te worker'ı başlatacak fonksiyon (fn, *args). None ise modülün
    kendi ayrılmış ThreadPoolExecutor'u kullanılır (production). "Worker başlat" kararı ile
    "kuyruğa ekle" kararı tek kritik bölümde alınır → devir yarışı yok.
    """
    start_worker = False
    with _registry_lock:
        q = _queues.setdefault(user_id, [])
        q.append(message)
        n = len(q)
        if not _active.get(user_id):
            # Bu webhook worker rolünü üstlenir. Bayrağı thread başlamadan ÖNCE, lock
            # altında set et: başka bir webhook araya girip ikinci worker başlatamasın.
            _active[user_id] = True
            start_worker = True

    if not start_worker:
        log.info("[coalesce] burst — kuyruğa eklendi (user=%s queue_len=%d)", user_id, n)
        return

    log.info("[coalesce] worker başlatılıyor (user=%s)", user_id)
    try:
        if background_add is not None:
            background_add(_worker, user_id, platform, process_fn)
        else:
            _EXECUTOR.submit(_worker, user_id, platform, process_fn)
    except Exception as e:
        # Worker başlatılamadı: aktif bayrağını geri al, yoksa abone sonsuza dek tıkanır
        # (kimse worker değil ama bayrak 'aktif' kalır). Kuyruk durur; sonraki webhook
        # tekrar worker olmayı dener (self-healing).
        log.exception("[coalesce] worker başlatılamadı user=%s: %s", user_id, e)
        with _registry_lock:
            _active[user_id] = False


def _worker(user_id: str, platform: str, process_fn: ProcessFn) -> None:
    """Coalesce worker (ayrılmış havuzda senkron koşar).

    1) İlk pencere bekle → kuyruğu boşalt → topla
    2) Artçı döngü: STRAGGLER bekle, yeni geldiyse tekrar topla (max_iter)
    3) Toplanan ham mesajları process_fn'e TEK seferde ver (medya çöz + ajan + teslim orada)
    4) Cevap sonrası kuyrukta mesaj varsa dış döngüde tekrar işle
    Emeklilik (finally): kuyruk-boş kontrolü + bayrak kaldırma + girdi silme TEK kritik bölümde.
    """
    max_iter = max(1, CONFIG.coalesce_max_iter)
    try:
        outer_iter = 0
        while outer_iter < max_iter:
            collected: list[str] = []

            # === İç toplama döngüsü: ilk pencere + artçı pencereler ===
            gather_iter = 0
            while gather_iter < max_iter:
                wait = _initial_sec() if gather_iter == 0 else _straggler_sec()
                if wait > 0:
                    time.sleep(wait)
                with _registry_lock:
                    batch = _drain_queue_locked(user_id)
                if batch:
                    collected.extend(batch)
                    gather_iter += 1
                    continue
                # Bu pencerede yeni mesaj yok. İlk turda boşsa (collected boş) bir kez daha
                # bekleme; ama elimizde mesaj VARSA bir artçı penceresi daha denedik demektir → dur.
                if collected:
                    break
                gather_iter += 1

            if not collected:
                # Hiç mesaj toplanmadı → bu turda işlenecek bir şey yok. Emeklilik kontrolüne
                # düş (finally değil; dış döngü bitişinde aşağıdaki atomik kontrol karar verir).
                break

            if len(collected) > 1:
                log.info("[coalesce] birleştirildi user=%s total=%d", user_id, len(collected))

            # === TEK işleme: medya çözümü + ajan + teslim callback'te ===
            try:
                process_fn(user_id, platform, collected)
            except Exception as e:
                log.exception("[coalesce] process_fn hata user=%s: %s", user_id, e)

            # === Cevap sonrası artçı kontrolü ===
            with _registry_lock:
                pending_after = bool(_queues.get(user_id))
            if not pending_after:
                break
            outer_iter += 1

        if outer_iter >= max_iter:
            log.warning("[coalesce] dış döngü üst sınırına ulaşıldı (user=%s)", user_id)
    finally:
        _retire(user_id, platform, process_fn)


def _retire(user_id: str, platform: str, process_fn: ProcessFn) -> None:
    """Worker'ı atomik emekli et: kuyruk gerçekten boşsa bayrağı kaldır + girdileri sil;
    BOŞ DEĞİLSE worker'ı sürdür (devir boşluğu kapanır, mesaj strand olmaz).

    Tek kritik bölümde 'kuyruk boş mu + bayrağı bırak' kararı verilir. Kuyruk boş değilken
    araya giren mesaj kaybolmaz: ya kalan işlenir (worker döngüye döner) ya da bayrak set
    kalır ve aynı thread tekrar işler. Bu döngü için güvenli üst sınır var (kalan boşalana dek).
    """
    while True:
        with _registry_lock:
            leftover = _drain_queue_locked(user_id)
            if not leftover:
                # Kuyruk gerçekten boş → emekli ol, girdileri temizle (bellek sızıntısı yok).
                _active.pop(user_id, None)
                _queues.pop(user_id, None)
                return
        # Kilit dışında işle (process_fn bloklayan ağ çağrıları yapar; lock'u tutma).
        log.info("[coalesce] emeklilikte artçı işleniyor user=%s n=%d", user_id, len(leftover))
        try:
            process_fn(user_id, platform, leftover)
        except Exception as e:
            log.exception("[coalesce] emeklilik process_fn hata user=%s: %s", user_id, e)
        # Döngü başına dön: işleme sırasında yeni mesaj gelmiş olabilir → tekrar kontrol et.
