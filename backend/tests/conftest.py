import math
import os
import tempfile
import pytest

TEST_DIRECTORY=tempfile.TemporaryDirectory(prefix='priceactioner-test-')
os.environ['STORAGE_BACKEND']='json'
os.environ['LOCAL_DATA_DIR']=TEST_DIRECTORY.name+'/data'
os.environ['APP_ENV']='development'
os.environ['VERCEL']=''
os.environ['ADMIN_USERNAME']='test-admin'
os.environ['ADMIN_PASSWORD']='test-only-password-123'
os.environ['ADMIN_SECRET_KEY']='test-only-secret-key-with-at-least-32-characters'
os.environ['JEV_MODE']='disabled'
from app.schemas.candle import Candle
from app.schemas.intent import UserIntent


def candle(i,price,volume=100,high=None,low=None):
    return Candle(timestamp=i*60000,close_timestamp=(i+1)*60000-1,open=price,close=price,
                  high=high if high is not None else price+2,low=low if low is not None else price-2,
                  volume=volume,quote_volume=volume*price,trades=10,taker_buy_base_volume=volume*.6,
                  taker_buy_quote_volume=volume*price*.6,closed=True)


@pytest.fixture
def bars():
    # Fixed synthetic market, independent of clocks and network.
    return [candle(i,1000+i*.8+35*math.sin(i/9)) for i in range(360)]


@pytest.fixture
def intent():
    return UserIntent(action='buy',action_timing_days=0,holding_period_days=7,risk_profile='balanced',priority='avoid_bad_entry')


def pytest_sessionfinish(session,exitstatus):
    TEST_DIRECTORY.cleanup()


@pytest.fixture(params=['json','mongodb'])
def document_store(request,tmp_path,monkeypatch):
    import importlib
    import mongomock
    from app.storage.documents import JsonStore,MongoStore
    target=(JsonStore(tmp_path/'records') if request.param=='json' else
            MongoStore('mongodb://unused','test',client=mongomock.MongoClient()))
    target.initialize()
    for name in ['app.main','app.storage.service','app.auth.service','app.auth.dependencies',
                 'app.api.admin','app.api.public','app.api.usage','app.api.health','app.logging.events']:
        monkeypatch.setattr(importlib.import_module(name),'storage',target)
    return target
