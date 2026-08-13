from redis import Redis


class RedisCache:
    def __init__(self, host: str, port: int):
        self.client = Redis(
            host=host,
            port=port,
            decode_responses=True,
        )

    def get(self, key: str) -> str | None:
        return self.client.get(key)

    def set(self, key: str, value: str, ttl: int):
        return self.client.set(
            key,
            value,
            ex=ttl,
        )

    def delete(self, key: str) -> bool:
        return bool(self.client.delete(key))
