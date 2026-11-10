"""Límite de solicitudes por IP, en memoria del proceso."""
from collections import OrderedDict
from threading import Lock
from time import monotonic

from fastapi import HTTPException, Request


class RateLimiter:
    """Límite local por IP (5 solicitudes por minuto si no se indica otro); memoria acotada.

    Para varias instancias debe sustituirse por un contador compartido.
    No confiar en X-Forwarded-For enviado directamente por el visitante.
    """

    def __init__(self, per_minute: int = 5):
        self.per_minute = per_minute
        self.buckets = OrderedDict()
        self.lock = Lock()

    def allow(self, request: Request) -> bool:
        try:
            self.check(request)
        except HTTPException:
            return False
        return True

    def check(self, request: Request):
        key = request.client.host if request.client else "unknown"
        now = monotonic()
        with self.lock:
            while self.buckets:
                first = next(iter(self.buckets))
                if self.buckets[first][0] + 60 > now:
                    break
                self.buckets.popitem(last=False)
            start, count = self.buckets.get(key, (now, 0))
            if count >= self.per_minute:
                raise HTTPException(429, "Demasiadas solicitudes", headers={"Retry-After": "60"})
            if key not in self.buckets and len(self.buckets) >= 10000:
                raise HTTPException(429, "Inténtalo más tarde", headers={"Retry-After": "60"})
            self.buckets[key] = (start, count + 1)
