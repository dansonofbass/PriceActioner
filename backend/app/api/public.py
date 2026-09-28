import asyncio
import time
import uuid
from datetime import datetime,timezone
from fastapi import APIRouter, HTTPException, Request, Response
from starlette.concurrency import run_in_threadpool
from app.config import INTERVAL_MS
from app.providers.binance import provider
from app.schemas.candle import Candle
from app.schemas.intent import UserIntent
from app.analysis.horizon import plan_for
from app.decision.context import analyze
from app.logging.events import event, analysis_id
from app.storage.service import storage
from app.storage.redis_store import StorageUnavailable
from app.api.usage import visitor, status, reserve, refund

router=APIRouter(prefix='/api')
analysis_slots=asyncio.Semaphore(2)


@router.get('/usage')
def usage(request: Request,response: Response):
    return status(visitor(request,response))


@router.get('/market')
async def market(timeframe: str='4h'):
    if timeframe not in INTERVAL_MS: raise HTTPException(422,'Unsupported timeframe')
    try:
        snapshot=await provider.fetch(timeframe)
        return {k:v for k,v in snapshot.items() if k!='raw'}
    except ValueError: raise HTTPException(503,'MARKET DATA UNAVAILABLE')


@router.post('/analyze')
async def submit(intent: UserIntent,request: Request,response: Response):
    digest=visitor(request,response)
    day=reserve(digest)
    completed=False
    identifier=str(uuid.uuid4()); token=analysis_id.set(identifier); started=time.perf_counter()
    try:
        async with analysis_slots:
            snapshots=await asyncio.gather(*(provider.fetch(tf) for tf in INTERVAL_MS),return_exceptions=True)
            data={tf:[Candle(**c) for c in snapshot['candles']] for tf,snapshot in zip(INTERVAL_MS,snapshots) if not isinstance(snapshot,Exception)}
            if plan_for(intent).primary_timeframe not in data: raise HTTPException(503,'MARKET DATA UNAVAILABLE: primary timeframe missing')
            result=await run_in_threadpool(analyze,data,intent,int(time.time()*1000),event)
            result['analysis_id']=identifier
            result['timestamp']=datetime.now(timezone.utc).isoformat()
            storage.put('analyses',identifier,{'analysis_id':identifier,'timestamp':result['timestamp'],'result':result})
            completed=True
            event('analysis_completed','analysis',duration_ms=(time.perf_counter()-started)*1000)
            public={k:result[k] for k in ['analysis_id','timestamp','context','alignment','status','missing_timeframes','engine_version','jev_mode','price_basis']}
            # Only the caller's own submitted context and static questions are exposed.
            public['request_preview']={k:result['jev_preview'][k] for k in ['payload','serialized_request','character_count','approximate_token_count','schema_status']}
            public['human_preview']=result['human_preview']
            public['usage']=status(digest)
            return public
    except StorageUnavailable:
        raise
    except HTTPException:
        event('analysis_failed','analysis',level='ERROR',reason='Market data unavailable'); raise
    except Exception as exc:
        event('analysis_failed','analysis',level='ERROR',error=type(exc).__name__)
        raise HTTPException(500,'ANALYSIS ENGINE ERROR') from exc
    finally:
        analysis_id.reset(token)
        if not completed: refund(digest,day)
