"""Small retained document store over Upstash HTTPS; no MongoDB/TCP setup."""
import hashlib
import base64
import zlib
import json
import httpx
from .documents import collection_name, matches


class StorageUnavailable(RuntimeError):
    """A safe error: never include credentials or upstream response bodies."""


class RestClient:
    def __init__(self, url, token, client=None):
        self.url = url.rstrip('/')
        self.token = token
        self.client = client or httpx.Client(timeout=10)

    def execute_command(self, *command):
        if not self.url or not self.token:
            raise StorageUnavailable('Redis is not configured. Set UPSTASH_REDIS_REST_URL and UPSTASH_REDIS_REST_TOKEN in the backend environment.')
        try:
            response = self.client.post(self.url, json=list(command), headers={'Authorization': 'Bearer ' + self.token})
            response.raise_for_status()
            data = response.json()
            if 'error' in data or 'result' not in data:
                raise ValueError('Invalid Redis response')
            return data['result']
        except (httpx.HTTPError, ValueError, TypeError):
            # Do not retry writes automatically: a lost response may have committed a quota.
            raise StorageUnavailable('Redis is unavailable. Check the backend REST URL/token and service status.') from None


# Index scores are expiry times; all data keys have native Redis expiry too.
# The script atomically saves, updates the index and bounds retained history.
PUT = """
if ARGV[4] == 'insert' and redis.call('EXISTS', KEYS[1]) == 1 then return 0 end
local clock = redis.call('TIME')
local now = tonumber(clock[1]) + tonumber(clock[2]) / 1000000
local ttl = tonumber(ARGV[2])
if ttl > 0 then redis.call('SET', KEYS[1], ARGV[1], 'EX', ttl)
else redis.call('SET', KEYS[1], ARGV[1]) end
redis.call('ZREMRANGEBYSCORE', KEYS[2], '-inf', now)
redis.call('ZADD', KEYS[2], ttl > 0 and now + ttl or 99999999999, KEYS[1])
if ttl > 0 then redis.call('EXPIRE', KEYS[2], ttl) end
local cap = tonumber(ARGV[3])
local count = redis.call('ZCARD', KEYS[2])
if cap > 0 and count > cap then
  local old = redis.call('ZRANGE', KEYS[2], 0, count - cap - 1)
  for _, key in ipairs(old) do redis.call('DEL', key); redis.call('ZREM', KEYS[2], key) end
end
return 1
"""
RESERVE = """
local raw = redis.call('GET', KEYS[1])
local doc = cjson.decode(raw or ARGV[1])
if doc.used >= tonumber(ARGV[2]) then return 0 end
doc.used = doc.used + 1
if raw then redis.call('SET', KEYS[1], cjson.encode(doc), 'KEEPTTL')
else redis.call('SET', KEYS[1], cjson.encode(doc), 'EX', ARGV[3]) end
return 1
"""
REFUND = """
local raw = redis.call('GET', KEYS[1])
if not raw then return 0 end
local doc = cjson.decode(raw)
if doc.used > 0 then
  doc.used = doc.used - 1
  redis.call('SET', KEYS[1], cjson.encode(doc), 'KEEPTTL')
end
return 1
"""
DELETE = """
redis.call('DEL', KEYS[1])
redis.call('ZREM', KEYS[2], KEYS[1])
return 1
"""


class RedisStore:
    kind = 'redis'
    retention_days = 7
    limits = {'analyses': 100, 'logs': 2000}
    ttls = {'analyses': 604800, 'logs': 604800, 'sessions': 28800,
            'visitors': 31536000, 'daily_usage': 172800, 'login_attempts': 600, 'admins': 0}

    def __init__(self, url='', token='', client=None):
        self.client = client if client is not None else RestClient(url, token)

    def initialize(self):
        # No network dependency during ASGI startup; /health remains reachable on outages.
        pass

    def _key(self, collection, key):
        return '{priceactioner}:' + collection_name(collection) + ':' + hashlib.sha256(str(key).encode()).hexdigest()

    def _index(self, collection):
        return '{priceactioner}:index:' + collection_name(collection)

    def _command(self, *args):
        return self.client.execute_command(*args)

    def ping(self):
        result=self._command('PING')
        if result not in ('PONG', True): raise StorageUnavailable('Redis health check failed.')
        return True

    def get(self, collection, key):
        raw = self._command('GET', self._key(collection, key))
        return self._decode(raw) if raw is not None else None

    @staticmethod
    def _decode(raw):
        if raw.startswith('z:'): raw = zlib.decompress(base64.b64decode(raw[2:])).decode('utf-8')
        return json.loads(raw)

    def _put(self, collection, key, document, mode):
        raw = json.dumps({**document, '_id': str(key)}, ensure_ascii=False, allow_nan=False)
        if len(raw)>4096: raw = 'z:' + base64.b64encode(zlib.compress(raw.encode('utf-8'))).decode('ascii')
        return bool(self._command('EVAL', PUT, 2, self._key(collection, key), self._index(collection),
                                  raw, self.ttls[collection], self.limits.get(collection, 0), mode))

    def put(self, collection, key, document):
        self._put(collection, key, document, 'put')

    def insert_once(self, collection, key, document):
        return self._put(collection, key, document, 'insert')

    def delete(self, collection, key):
        self._command('EVAL', DELETE, 2, self._key(collection, key), self._index(collection))

    def _find(self, collection, filters):
        keys = self._command('ZRANGE', self._index(collection), 0, -1)
        rows = []
        for start in range(0, len(keys), 25):
            for raw in self._command('MGET', *keys[start:start+25]):
                if raw is not None:
                    doc = self._decode(raw)
                    if matches(doc, filters): rows.append(doc)
        return rows

    def find(self, collection, filters=None, *, sort='timestamp', limit=100, offset=0):
        rows = sorted(self._find(collection, filters), key=lambda row: (str(row.get(sort, '')), row['_id']), reverse=True)
        return rows[offset:offset+limit]

    def delete_where(self, collection, filters):
        for row in self._find(collection, filters): self.delete(collection, row['_id'])

    def reserve(self, collection, key, limit, metadata=None):
        raw = json.dumps({**(metadata or {}), '_id': str(key), 'used': 0})
        return bool(self._command('EVAL', RESERVE, 1, self._key(collection, key), raw, limit, self.ttls[collection]))

    def refund(self, collection, key):
        self._command('EVAL', REFUND, 1, self._key(collection, key))
