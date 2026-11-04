"""Slows down password guessing. Too many failed sign-ins for one account, or from one address, block further
attempts for a while. Successful sign-ins don't count, and clear the account's failures.

If Redis is unreachable, sign-in still works (unlimited) rather than locking everyone out.
"""
from redis import Redis, RedisError

from app.config import settings

WINDOW_SECONDS = 15 * 60
MAX_FAILURES_PER_ACCOUNT = 10
# Higher, because many students can share one address (a campus or office network).
MAX_FAILURES_PER_ADDRESS = 50
KEY_PREFIX = "login-failures:"

_redis = Redis.from_url(settings.redis_url, socket_timeout=1, socket_connect_timeout=1)


def _keys(identifier: str, address: str) -> tuple[str, str]:
    return f"{KEY_PREFIX}account:{identifier.lower()}", f"{KEY_PREFIX}address:{address}"


def is_locked(identifier: str, address: str) -> bool:
    try:
        account, by_address = _redis.mget(_keys(identifier, address))
    except RedisError:
        return False
    return int(account or 0) >= MAX_FAILURES_PER_ACCOUNT or int(by_address or 0) >= MAX_FAILURES_PER_ADDRESS


def record_failure(identifier: str, address: str) -> None:
    try:
        with _redis.pipeline() as pipe:
            for key in _keys(identifier, address):
                pipe.incr(key)
                pipe.expire(key, WINDOW_SECONDS, nx=True)  # the window starts at the first failure
            pipe.execute()
    except RedisError:
        pass


def clear_account(identifier: str) -> None:
    try:
        _redis.delete(_keys(identifier, "")[0])
    except RedisError:
        pass


def clear_all() -> None:
    """For tests."""
    keys = list(_redis.scan_iter(f"{KEY_PREFIX}*"))
    if keys:
        _redis.delete(*keys)
