import time
import re
from fastapi import APIRouter, Depends, Request, Response, HTTPException, Query
from pydantic import BaseModel, Field
from app.auth.dependencies import require_admin
from app.auth.service import login,token_hash
from app.storage.service import storage
from app.config import settings,ENGINE_CONFIG,INTERVAL_MS
from app.providers.binance import provider
from app.schemas.intent import UserIntent
from app.analysis.horizon import plan_for
from app.decision.context import SOURCE_MAP

router=APIRouter(prefix='/api/admin')


class Credentials(BaseModel):
    username: str=Field(max_length=100)
    password: str=Field(max_length=1024)


@router.post('/login')
def sign_in(credentials: Credentials,request: Request,response: Response):
    # Persistent fixed-window throttling, shared by all serverless instances.
    host=request.client.host if request.client else 'local'
    key=token_hash(f'login:{host}:{credentials.username}:{int(time.time()//300)}')
    if not storage.reserve('login_attempts',key,5):
        raise HTTPException(429,'Too many login attempts. Try again in five minutes.')
    token=login(credentials.username,credentials.password)
    if not token: raise HTTPException(401,'Invalid username or password')
    storage.delete('login_attempts',key)
    response.set_cookie('priceactioner_session',token,httponly=True,secure=settings.app_env=='production',samesite='strict',max_age=28800,path='/')
    return {'status':'authenticated'}


@router.post('/logout',dependencies=[Depends(require_admin)])
def logout(request: Request,response: Response):
    storage.delete('sessions',token_hash(request.cookies['priceactioner_session']))
    response.delete_cookie('priceactioner_session',path='/')
    return {'status':'logged out'}


@router.get('/me')
def me(username=Depends(require_admin)): return {'username':username,'jev_mode':'disabled'}


@router.get('/raw',dependencies=[Depends(require_admin)])
async def raw(timeframe: str='4h',refresh: bool=False):
    if timeframe not in INTERVAL_MS: raise HTTPException(422,'Unsupported timeframe')
    try: return await provider.fetch(timeframe,refresh)
    except ValueError: raise HTTPException(503,'MARKET DATA UNAVAILABLE')


@router.get('/history',dependencies=[Depends(require_admin)])
def history(limit: int=Query(50,ge=1,le=200),offset: int=Query(0,ge=0)):
    rows=storage.find('analyses',limit=limit,offset=offset)
    return [{'analysis_id':r['analysis_id'],'timestamp':r['timestamp'],'intent':r['result']['context']['user_intent'],
             'price':r['result']['context']['current_price'],'engine_version':r['result']['engine_version']} for r in rows]


@router.get('/analysis/{identifier}',dependencies=[Depends(require_admin)])
def saved_analysis(identifier: str):
    rows=storage.find('analyses',limit=1) if identifier=='latest' else []
    row=(rows[0] if rows else None) if identifier=='latest' else storage.get('analyses',identifier)
    if not row: raise HTTPException(404,'No analysis yet. Submit the public form first.')
    return row['result']


@router.get('/horizon',dependencies=[Depends(require_admin)])
def horizon(days: float=Query(7,ge=1,le=30)):
    return plan_for(UserIntent(action='buy',action_timing_days=0,holding_period_days=days,risk_profile='balanced',priority='balanced'))


@router.get('/system',dependencies=[Depends(require_admin)])
def system():
    return {'config':ENGINE_CONFIG,'source_map':SOURCE_MAP,'jev_mode':'disabled','engine_version':settings.analysis_engine_version,
            'admin_configured':bool(settings.admin_secret_key),'data_source':'https://data-api.binance.vision',
            'runtime':f'Python / FastAPI / {storage.kind}','storage':storage.kind,
            'scope':'Public market data only; no execution or account access'}


@router.get('/logs',dependencies=[Depends(require_admin)])
def logs(level: str='',component: str='',analysis_id: str='',search: str='',limit: int=Query(100,ge=1,le=500),offset: int=Query(0,ge=0)):
    filters={}
    if level: filters['level']=level
    if component: filters['component']=component
    if analysis_id: filters['analysis_id']=analysis_id
    if search: filters['$or']=[{'message':{'$regex':re.escape(search)}},{'event':{'$regex':re.escape(search)}}]
    rows=storage.find('logs',filters,limit=limit,offset=offset)
    return [{name:row.get(name) for name in ['timestamp','level','component','event','analysis_id','request_id','duration_ms','message','details']} for row in rows]
