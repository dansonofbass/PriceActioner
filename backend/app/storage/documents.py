"""JSON document storage: locked files locally, MongoDB for shared cloud persistence."""
import hashlib
import json
import os
import re
import uuid
from pathlib import Path
import portalocker
from pymongo import MongoClient, ReturnDocument, DESCENDING

COLLECTIONS = {'admins', 'sessions', 'analyses', 'logs', 'visitors', 'daily_usage', 'login_attempts'}


def collection_name(value):
    if value not in COLLECTIONS:
        raise ValueError('Unknown collection')
    return value


def matches(document, filters):
    for key, expected in (filters or {}).items():
        if key == '$or':
            if not any(matches(document, condition) for condition in expected):
                return False
            continue
        actual = document.get(key)
        if isinstance(expected, dict):
            for op, value in expected.items():
                if op == '$lt' and (actual is None or actual >= value): return False
                if op == '$gt' and (actual is None or actual <= value): return False
                if op == '$regex' and re.search(value, str(actual or '')) is None: return False
        elif actual != expected:
            return False
    return True


class JsonStore:
    """Atomic replace and an OS file lock prevent partial files/lost counter updates."""
    kind = 'json'

    def __init__(self, root):
        self.root = Path(root).resolve()

    def initialize(self):
        self.root.mkdir(parents=True, exist_ok=True)

    def _lock(self):
        self.initialize()
        return portalocker.Lock(str(self.root / '.store.lock'), timeout=15)

    def _path(self, collection, key):
        name = hashlib.sha256(str(key).encode()).hexdigest() + '.json'
        return self.root / collection_name(collection) / name

    def _get(self, collection, key):
        path = self._path(collection, key)
        return json.loads(path.read_text(encoding='utf-8')) if path.exists() else None

    def _put(self, collection, key, document):
        path = self._path(collection, key)
        path.parent.mkdir(exist_ok=True)
        temporary = path.with_suffix('.' + uuid.uuid4().hex + '.tmp')
        try:
            with temporary.open('w', encoding='utf-8') as handle:
                json.dump({**document, '_id': str(key)}, handle, ensure_ascii=False, allow_nan=False)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, path)
        finally:
            temporary.unlink(missing_ok=True)

    def ping(self):
        with self._lock(): return True

    def get(self, collection, key):
        with self._lock(): return self._get(collection, key)

    def put(self, collection, key, document):
        with self._lock(): self._put(collection, key, document)

    def insert_once(self, collection, key, document):
        with self._lock():
            if self._get(collection, key) is not None: return False
            self._put(collection, key, document)
            return True

    def delete(self, collection, key):
        with self._lock(): self._path(collection, key).unlink(missing_ok=True)

    def _find(self, collection, filters):
        return [row for path in (self.root / collection_name(collection)).glob('*.json')
                if matches(row := json.loads(path.read_text(encoding='utf-8')), filters)]

    def find(self, collection, filters=None, *, sort='timestamp', limit=100, offset=0):
        with self._lock():
            rows = sorted(self._find(collection, filters), key=lambda row: (str(row.get(sort, '')), row['_id']), reverse=True)
            return rows[offset:offset+limit]

    def delete_where(self, collection, filters):
        with self._lock():
            for row in self._find(collection, filters): self._path(collection, row['_id']).unlink(missing_ok=True)

    def reserve(self, collection, key, limit, metadata=None):
        with self._lock():
            row = self._get(collection, key) or {**(metadata or {}), 'used': 0}
            if row['used'] >= limit: return False
            row['used'] += 1
            self._put(collection, key, row)
            return True

    def refund(self, collection, key):
        with self._lock():
            row = self._get(collection, key)
            if row and row['used'] > 0:
                row['used'] -= 1
                self._put(collection, key, row)


class MongoStore:
    kind = 'mongodb'

    def __init__(self, uri, database, client=None):
        self.client = client if client is not None else MongoClient(
            uri, serverSelectionTimeoutMS=5000, connectTimeoutMS=5000,
            socketTimeoutMS=10000, maxPoolSize=5, maxIdleTimeMS=60000,
            appname='priceactioner')
        self.db = self.client[database]

    def initialize(self):
        # _id has a unique index automatically. These cover history and admin log queries.
        self.db.analyses.create_index([('timestamp', DESCENDING)])
        self.db.logs.create_index([('timestamp', DESCENDING)])
        self.db.logs.create_index([('analysis_id', 1), ('timestamp', DESCENDING)])

    def ping(self):
        self.client.admin.command('ping')
        return True

    def _collection(self, name):
        return self.db[collection_name(name)]

    def get(self, collection, key):
        return self._collection(collection).find_one({'_id': str(key)})

    def put(self, collection, key, document):
        self._collection(collection).replace_one({'_id': str(key)}, {**document, '_id': str(key)}, upsert=True)

    def insert_once(self, collection, key, document):
        from pymongo.errors import DuplicateKeyError
        try:
            result = self._collection(collection).update_one(
                {'_id': str(key)}, {'$setOnInsert': {**document, '_id': str(key)}}, upsert=True)
            return result.upserted_id is not None
        except DuplicateKeyError:
            # Another instance won the initial insert; the existing record is authoritative.
            return False

    def delete(self, collection, key):
        self._collection(collection).delete_one({'_id': str(key)})

    def find(self, collection, filters=None, *, sort='timestamp', limit=100, offset=0):
        return list(self._collection(collection).find(filters or {}).sort(
            [(sort, DESCENDING), ('_id', DESCENDING)]).skip(offset).limit(limit))

    def delete_where(self, collection, filters):
        self._collection(collection).delete_many(filters)

    def reserve(self, collection, key, limit, metadata=None):
        self.insert_once(collection, key, {**(metadata or {}), 'used': 0})
        # One document, one conditional atomic update. No read/modify/write race.
        row = self._collection(collection).find_one_and_update(
            {'_id': str(key), 'used': {'$lt': limit}}, {'$inc': {'used': 1}},
            return_document=ReturnDocument.AFTER)
        return row is not None

    def refund(self, collection, key):
        self._collection(collection).update_one({'_id': str(key), 'used': {'$gt': 0}}, {'$inc': {'used': -1}})
