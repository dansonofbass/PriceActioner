from app.config import settings
from .documents import JsonStore, MongoStore

# One warm-process client/pool; MongoDB keeps shared durable state across Vercel instances.
storage = (MongoStore(settings.mongodb_uri, settings.mongodb_database)
           if settings.storage_backend == 'mongodb' else JsonStore(settings.local_data_dir))
