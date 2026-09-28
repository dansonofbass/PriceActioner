import time
from fastapi import Request, HTTPException
from app.storage.service import storage
from .service import token_hash


def require_admin(request: Request):
    token=request.cookies.get('priceactioner_session')
    session=storage.get('sessions',token_hash(token)) if token else None
    if not session or session['expires_at']<=time.time(): raise HTTPException(401,'Admin login required')
    return session['username']
