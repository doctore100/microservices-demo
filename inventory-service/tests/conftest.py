from collections import UserDict

import pytest


class FakeRedisJson:
    def __init__(self, store: UserDict):
        self._store = store

    async def set(self, key, path, obj, nx=False):
        if nx and key in self._store:
            return False
        self._store[key] = obj
        return True

    async def get(self, key):
        return self._store.get(key)


class FakeRedis:
    def __init__(self):
        self._store = UserDict()
        self._streams = {}

    def json(self):
        return FakeRedisJson(self._store)

    async def exists(self, key):
        return key in self._store

    async def keys(self, pattern):
        prefix = pattern.replace("*", "")
        return [k for k in self._store if k.startswith(prefix)]

    async def delete(self, key):
        self._store.pop(key, None)

    async def xadd(self, stream, data, maxlen=None):
        if stream not in self._streams:
            self._streams[stream] = []
        msg_id = f"{len(self._streams[stream]) + 1}-0"
        self._streams[stream].append((msg_id, dict(data)))
        return msg_id

    async def xgroup_create(self, stream, groupname, id="$", mkstream=False):
        if stream not in self._streams and mkstream:
            self._streams[stream] = []

    async def xreadgroup(
        self, groupname, consumername, streams, count=None, block=None
    ):
        result = []
        for stream in streams:
            if stream not in self._streams:
                continue
            entries = list(self._streams[stream])
            if count:
                entries = entries[:count]
            if entries:
                result.append((stream, entries))
        return result if result else None

    async def xack(self, stream, groupname, *ids):
        pass

    async def sadd(self, key, member):
        if key not in self._store:
            self._store[key] = set()
        self._store[key].add(member)
        return 1

    async def srem(self, key, member):
        s = self._store.get(key)
        if isinstance(s, set):
            s.discard(member)
        return 1

    async def sismember(self, key, member):
        s = self._store.get(key)
        if isinstance(s, set):
            return 1 if member in s else 0
        return 0


@pytest.fixture
def fake_redis():
    return FakeRedis()


@pytest.fixture(autouse=True)
def mock_redis_client(monkeypatch, fake_redis):
    monkeypatch.setattr("app.schemas.redis_client", fake_redis)
    monkeypatch.setattr("app.main.redis_client", fake_redis)
    monkeypatch.setattr("app.streams.redis_client", fake_redis)
    monkeypatch.setattr("app.consumer.redis_client", fake_redis)
