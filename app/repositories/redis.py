from redis import Redis, BlockingConnectionPool


class RedisCache:
    def __init__(
        self,
        host: str,
        port: int,
        username: str | None = None,
        password: str | None = None,
    ):
        # Limit the size of connection pool for a server so multiple instances can share
        # the maximum of 256 connections to redis
        self.pool = BlockingConnectionPool(
            host=host,
            port=port,
            username=username,
            password=password,
            decode_responses=True,
            max_connections=10,
            timeout=0.5,
            socket_connect_timeout=1.0,
            socket_timeout=0.5,
        )
        self.client = Redis(connection_pool=self.pool)

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
