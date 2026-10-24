import json
import logging

import redis

from ai_email_ops.app.config import settings

logger = logging.getLogger("uvicorn.error")

# Short timeouts: if Redis is slow or down, give up quickly instead of freezing requests
redis_client = redis.Redis.from_url(
    settings.redis_url,
    decode_responses=True,
    socket_connect_timeout=1,
    socket_timeout=1,
)

# Change this number whenever the prompt or schema changes, so old cached drafts are ignored
PROMPT_VERSION = "v1"
TICKET_DRAFT_TTL_SECONDS = 3600  # 1 hour


def ticket_draft_key(email_id: int) -> str:
    return f"ticket_draft:{PROMPT_VERSION}:{email_id}"


def cache_get(key: str):
    """Return the cached value, or None if missing. Never raises."""
    try:
        value = redis_client.get(key)
    except redis.RedisError:
        logger.warning("Redis unavailable: skipping cache read")
        return None
    return json.loads(value) if value else None


def cache_set(key: str, value, ttl_seconds: int) -> None:
    try:
        redis_client.set(key, json.dumps(value), ex=ttl_seconds)
    except redis.RedisError:
        logger.warning("Redis unavailable: skipping cache write")


def cache_delete(key: str) -> None:
    try:
        redis_client.delete(key)
    except redis.RedisError:
        logger.warning("Redis unavailable: skipping cache delete")