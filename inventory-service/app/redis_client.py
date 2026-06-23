"""
Redis client singleton for the inventory service.

This module exposes a lazily-initialized Redis client instance.
The underlying connection is created on first method call, so importing
this module does not require environment variables to be present.
"""

from __future__ import annotations

from typing import Any

import redis.asyncio as redis

from app.config.settings import Settings


class _LazyRedis:
    _client: redis.Redis | None = None

    def _ensure(self) -> redis.Redis:
        if self._client is None:
            s = Settings()
            self._client = redis.Redis(
                host=s.REDIS_HOST.get_secret_value(),
                password=s.REDIS_PASSWORD.get_secret_value(),
                port=s.REDIS_PORT,
                decode_responses=True,
            )
        return self._client

    def __getattr__(self, name: str) -> Any:
        return getattr(self._ensure(), name)


redis_client = _LazyRedis()
