from threading import RLock
from typing import Generic, Optional, TypeVar

from cachetools import TTLCache


K = TypeVar("K")
V = TypeVar("V")


class ThreadSafeTTLCache(Generic[K, V]):
    """
    Thin wrapper over cachetools.TTLCache with a lock to keep access safe for
    multithreaded FastAPI workers.
    """

    def __init__(self, maxsize: int, ttl: float):
        self._cache: TTLCache[K, V] = TTLCache(maxsize=maxsize, ttl=ttl)
        self._lock = RLock()

    def get(self, key: K) -> Optional[V]:
        with self._lock:
            return self._cache.get(key)

    def set(self, key: K, value: V) -> None:
        with self._lock:
            self._cache[key] = value

    def clear(self) -> None:
        with self._lock:
            self._cache.clear()
