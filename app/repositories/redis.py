from redis import Redis, BlockingConnectionPool
import time
from threading import Lock
from typing import Optional


class Node:
    def __init__(self, key: str = "", value: str = "", expires_at: float = -1):
        self.key = key
        self.value = value
        self.expires_at = expires_at
        self.prev: Optional[Node] = None
        self.next: Optional[Node] = None


class L1Cache:
    def __init__(self, max_size: int = 100):
        if max_size <= 0:
            raise ValueError("Invalid max_size")

        self._key_to_node: dict[str, Node] = {}

        self._first_node = Node()
        self._last_node = Node()
        self._first_node.next = self._last_node
        self._last_node.prev = self._first_node

        self._lock: Lock = Lock()
        self._max_size = max_size

    def _remove(self, node: Node) -> None:
        if node.prev is None or node.next is None:
            raise RuntimeError("Detached node")

        node.prev.next = node.next
        node.next.prev = node.prev
        node.prev = None
        node.next = None

    def _add_to_head(self, node: Node) -> None:
        node.next = self._first_node.next
        node.prev = self._first_node
        self._first_node.next.prev = node
        self._first_node.next = node

    def get(self, key: str) -> Optional[str]:
        with self._lock:
            node = self._key_to_node.get(key)
            if node is None:
                return None

            if node.expires_at <= time.monotonic():
                # Key is expired and is removed from the cache
                del self._key_to_node[key]
                self._remove(node)
                return None

            # The node becomes most recently used (MRU)
            self._remove(node)
            self._add_to_head(node)
            return node.value

    def set(self, key: str, value: str, ttl: int) -> None:
        if ttl <= 0 or ttl > 60:
            raise ValueError("Invalid ttl, ttl must be positive and less than 1 minute")

        with self._lock:
            existing_node = self._key_to_node.get(key)
            if existing_node is not None:
                self._remove(existing_node)

            new_node = Node(
                key=key,
                value=value,
                expires_at=time.monotonic() + ttl,
            )
            self._key_to_node[key] = new_node
            self._add_to_head(new_node)

            # If the cache exceeds the maximum capacity, remove the least recently used key
            if len(self._key_to_node) > self._max_size:
                lru_node = self._last_node.prev
                if lru_node is not self._first_node:
                    self._key_to_node.pop(lru_node.key, None)
                    self._remove(lru_node)

    def delete(self, key: str) -> None:
        with self._lock:
            if key in self._key_to_node:
                node = self._key_to_node[key]
                del self._key_to_node[key]
                self._remove(node)


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

    def set(self, key: str, value: str, ttl: int) -> None:
        self.client.set(
            key,
            value,
            ex=ttl,
        )

    def delete(self, key: str) -> None:
        self.client.delete(key)
