from contextvars import ContextVar
from datetime import datetime, timezone
import logging
import uuid
from app.storage.service import storage

request_id=ContextVar('request_id',default=None)
analysis_id=ContextVar('analysis_id',default=None)


def event(name: str, component: str, level='INFO', duration_ms=None, **metadata):
    storage.put('logs',str(uuid.uuid4()),dict(timestamp=datetime.now(timezone.utc).isoformat(),level=level,component=component,event=name,
                analysis_id=analysis_id.get(),request_id=request_id.get(),duration_ms=duration_ms,
                message=name.replace('_',' '),details=metadata))
    logging.getLogger('priceactioner').log(getattr(logging,level), '%s request=%s analysis=%s',name,request_id.get(),analysis_id.get())
