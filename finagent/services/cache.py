import json

from finagent.core.config import get_settings


class Cache:
    def __init__(self):
        self.client = None
        try:
            from redis import Redis

            client = Redis.from_url(
                get_settings().redis_url, decode_responses=True, socket_connect_timeout=0.25
            )
            client.ping()
            self.client = client
        except Exception:
            pass

    def get(self, key: str):
        value = self.client.get(key) if self.client else None
        return json.loads(value) if value else None

    def set(self, key: str, value: dict, ttl: int = 900):
        if self.client:
            self.client.setex(key, ttl, json.dumps(value, default=str))
