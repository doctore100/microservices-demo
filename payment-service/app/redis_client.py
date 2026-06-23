"""
Redis client singleton for the payment service.

This module initializes and exposes a single Redis client instance
configured via environment variables. All data access in the payment
service uses this shared client.

:ivar redis_client: The global Redis client instance connected to Redis Cloud.
"""

import redis.asyncio as redis

from app.config.settings import Settings

settings = Settings()

redis_client = redis.Redis(
    host=settings.REDIS_HOST.get_secret_value(),
    password=settings.REDIS_PASSWORD.get_secret_value(),
    port=settings.REDIS_PORT,
    decode_responses=True,
)
