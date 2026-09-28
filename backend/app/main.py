from contextlib import asynccontextmanager
import uuid
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from app.config import settings
from app.storage.service import storage
from app.auth.service import bootstrap_admin
from app.api import public,admin,health
from app.logging.events import request_id
from app.storage.redis_store import StorageUnavailable


@asynccontextmanager
async def lifespan(app):
    storage.initialize()
    if storage.kind == 'json': bootstrap_admin()
    yield


app=FastAPI(title='priceactioner',version=settings.analysis_engine_version,lifespan=lifespan,
            docs_url='/api/docs' if settings.app_env=='development' else None,redoc_url=None)


@app.exception_handler(StorageUnavailable)
async def storage_unavailable(request, exc):
    return JSONResponse({'detail': str(exc)}, status_code=503)


@app.middleware('http')
async def request_context(request: Request,call_next):
    identifier=str(uuid.uuid4()); token=request_id.set(identifier)
    try:
        if request.method in ('POST','PUT','PATCH','DELETE'):
            origin=request.headers.get('origin')
            if origin and origin!=settings.public_origin:
                return JSONResponse({'detail':'Origin not allowed'},status_code=403)
            if request.headers.get('sec-fetch-site')=='cross-site':
                return JSONResponse({'detail':'Cross-site request rejected'},status_code=403)
            if 'application/json' not in request.headers.get('content-type',''):
                return JSONResponse({'detail':'JSON content type required'},status_code=415)
        response=await call_next(request)
        response.headers['X-Request-ID']=identifier
        response.headers['X-Content-Type-Options']='nosniff'
        response.headers['Cache-Control']='no-store'
        return response
    finally: request_id.reset(token)


app.include_router(public.router)
app.include_router(admin.router)
app.include_router(health.router)
