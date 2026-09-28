from app.config import settings
from .documents import JsonStore
from .redis_store import RedisStore

# Redis is shared across Vercel instances; local JSON needs no external service.
storage = (RedisStore(settings.upstash_redis_rest_url, settings.upstash_redis_rest_token)
           if settings.storage_backend == 'redis' else JsonStore(settings.local_data_dir))
