"""Anonymous per-browser quota. No IP addresses or fingerprints are stored."""
import hashlib
import secrets
import time
from datetime import datetime, timedelta, timezone
from fastapi import Request, Response, HTTPException
from app.config import settings
from app.storage.service import storage

COOKIE='priceactioner_visitor'


def utc_now():
    return datetime.now(timezone.utc)


def visitor(request: Request, response: Response) -> str:
    token=request.cookies.get(COOKIE,'')
    digest=hashlib.sha256(token.encode()).hexdigest()
    if not token or not storage.get('visitors',digest):
        token=secrets.token_urlsafe(32)
        digest=hashlib.sha256(token.encode()).hexdigest()
        storage.put('visitors',digest,{'created_at':time.time()})
        response.set_cookie(COOKIE,token,httponly=True,secure=settings.app_env=='production',
                            samesite='strict',max_age=31536000,path='/')
    return digest


def status(digest: str) -> dict:
    now=utc_now()
    day=now.date().isoformat()
    reset=datetime.combine(now.date()+timedelta(days=1),datetime.min.time(),tzinfo=timezone.utc)
    record=storage.get('daily_usage',f'{digest}:{day}')
    used=record['used'] if record else 0
    return {'limit':settings.daily_analysis_limit,'used':used,
            'remaining':max(0,settings.daily_analysis_limit-used),'resets_at':reset.isoformat(),
            'scope':'browser','timezone':'UTC'}


def reserve(digest: str) -> str:
    """Atomic conditional increment also protects concurrent requests."""
    day=utc_now().date().isoformat()
    if not storage.reserve('daily_usage',f'{digest}:{day}',settings.daily_analysis_limit,{'visitor_hash':digest,'day':day}):
        reset=status(digest)['resets_at']
        raise HTTPException(429,f'Daily limit reached: {settings.daily_analysis_limit} analyses per day. Resets at {reset} (UTC).')
    return day


def refund(digest: str, day: str):
    storage.refund('daily_usage',f'{digest}:{day}')
