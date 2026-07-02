"""nyawa/event_bus.py — Global event queue untuk komunikasi antar modul.

Semua modul berkomunikasi lewat EventBus, bukan lewat import silang.
"""

from dataclasses import dataclass
from queue import Empty, Queue
from typing import Any, Optional


@dataclass
class Event:
    type: str  # Contoh: 'FACE_DETECTED', 'TOUCHED_HEAD'
    data: Any = None  # Payload opsional
    source: str = ""  # Modul pengirim


class EventBus:
    """Wrapper thread-safe di atas queue.Queue."""

    def __init__(self, maxsize: int = 100):
        self._queue: Queue = Queue(maxsize=maxsize)

    def publish(self, event: Event) -> None:
        self._queue.put(event)

    def subscribe(self) -> Event:
        """Blocking get — menunggu sampai ada event baru."""
        return self._queue.get()

    def subscribe_nowait(self) -> Optional[Event]:
        try:
            return self._queue.get_nowait()
        except Empty:
            return None

    def clear(self) -> None:
        with self._queue.mutex:
            self._queue.queue.clear()

    def qsize(self) -> int:
        return self._queue.qsize()
