import time
from fastapi import APIRouter
from app.config import settings
from app.storage.service import storage
from app.providers.binance import provider

router=APIRouter(prefix='/api')


@router.get('/health')
def health():
    storage_error=None
    try:
        storage.ping()
        database='ONLINE'
    except Exception:
        database='OFFLINE'
        storage_error='Check backend UPSTASH_REDIS_REST_URL / UPSTASH_REDIS_REST_TOKEN and Redis service availability.' if storage.kind=='redis' else 'Local storage unavailable.'
    recent=provider.last_fetch and time.time()*1000-provider.last_fetch<60000
    return {'backend':'ONLINE','database':database,'storage':storage.kind,'storage_error':storage_error,'binance':'OFFLINE' if provider.last_error else 'ONLINE' if recent else 'UNKNOWN',
            'analysis_engine_version':settings.analysis_engine_version,'analysis_engine':'READY','jev_mode':'disabled',
            'jev_configured':bool(settings.jev_api_key),'last_data_fetch':provider.last_fetch,
            'failed_timeframes':list(provider.failures),
            'candle_counts':{tf:len(s['candles']) for tf,s in provider.cache.items()}}
