import time
from fastapi import APIRouter
from app.config import settings
from app.storage.service import storage
from app.providers.binance import provider

router=APIRouter(prefix='/api')


@router.get('/health')
def health():
    try:
        storage.ping()
        database='ONLINE'
    except Exception: database='OFFLINE'
    recent=provider.last_fetch and time.time()*1000-provider.last_fetch<60000
    return {'backend':'ONLINE','database':database,'storage':storage.kind,'binance':'OFFLINE' if provider.last_error else 'ONLINE' if recent else 'UNKNOWN',
            'analysis_engine_version':settings.analysis_engine_version,'analysis_engine':'READY','jev_mode':'disabled',
            'jev_configured':bool(settings.jev_api_key),'last_data_fetch':provider.last_fetch,
            'failed_timeframes':list(provider.failures),
            'candle_counts':{tf:len(s['candles']) for tf,s in provider.cache.items()}}
