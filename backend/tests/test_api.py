import pytest
import json
from fastapi.testclient import TestClient
from app.main import app
from app.providers.binance import provider
from app.auth.service import hash_password,verify
from app.auth import service as auth_service
from app.config import settings


@pytest.fixture
def client(document_store):
    with TestClient(app) as client: yield client


def authenticate(client):
    return client.post('/api/admin/login',json={'username':'test-admin','password':'test-only-password-123'})


def test_auth_cookie_logout_and_protected_endpoints(client):
    assert client.get('/api/admin/history').status_code==401
    response=authenticate(client)
    assert response.status_code==200
    cookie=response.headers['set-cookie']
    assert 'HttpOnly' in cookie and 'SameSite=strict' in cookie
    assert client.get('/api/admin/me').status_code==200
    assert auth_service.storage.get('admins','test-admin')['password_hash']!='test-only-password-123'
    assert client.post('/api/admin/logout',json={}).status_code==200
    assert client.get('/api/admin/me').status_code==401


def test_password_hash():
    hashed=hash_password('abc123')
    assert verify('abc123',hashed)
    assert not verify('wrong',hashed)
    assert hash_password('abc123')!=hashed


def test_csrf_and_throttling(client):
    assert client.post('/api/admin/login',json={},headers={'origin':'https://other.example'}).status_code==403
    for _ in range(5):
        assert client.post('/api/admin/login',json={'username':'unknown','password':'bad'}).status_code==401
    assert client.post('/api/admin/login',json={'username':'unknown','password':'bad'}).status_code==429


def test_production_cookie_secure(client,monkeypatch):
    monkeypatch.setattr(settings,'app_env','production')
    assert 'Secure' in authenticate(client).headers['set-cookie']


def test_complete_submission_history_logs_and_preview(client,monkeypatch,bars,intent):
    async def fetch(tf,refresh=False):
        return {'timeframe':tf,'candles':[c.model_dump() for c in bars],'raw':[], 'fetched_at':bars[-1].close_timestamp,'status':'LIVE'}
    monkeypatch.setattr(provider,'fetch',fetch)
    response=client.post('/api/analyze',json=intent.model_dump())
    assert response.status_code==200,response.text
    result=response.json()
    assert result['jev_mode']=='disabled' and 'jev_preview' not in result
    assert 'X-Request-ID' in response.headers
    authenticate(client)
    history=client.get('/api/admin/history').json()
    assert history[0]['analysis_id']==result['analysis_id']
    saved=client.get('/api/admin/analysis/'+result['analysis_id']).json()
    assert saved['config_snapshot'] and saved['frames']['4h']['indicators']['rsi14']>0
    assert saved['jev_preview']['status']=='JEV REQUEST NOT SENT'
    assert result['request_preview']['serialized_request']==saved['jev_preview']['serialized_request']
    assert json.loads(result['request_preview']['serialized_request'])['state']==result['context']
    assert len(result['request_preview']['payload']['questions'])==6
    assert 'test-only-secret' not in json.dumps(result['request_preview'])
    assert result['usage']['remaining']==2
    logs=client.get('/api/admin/logs',params={'analysis_id':result['analysis_id']}).json()
    names={l['event'] for l in logs}
    assert {'analysis_completed','decision_context_completed','jev_request_built','pivot_detection_completed'}<=names
    assert all(l['request_id']==response.headers['X-Request-ID'] for l in logs)
    assert 'jev_request_started' not in names


def test_primary_outage_and_partial_timeframe(client,monkeypatch,bars,intent):
    async def fetch(tf,refresh=False):
        if tf=='4h': raise ValueError('unavailable')
        return {'candles':[c.model_dump() for c in bars]}
    monkeypatch.setattr(provider,'fetch',fetch)
    assert client.post('/api/analyze',json=intent.model_dump()).status_code==503
    async def partial(tf,refresh=False):
        if tf=='1d': raise ValueError('unavailable')
        return {'candles':[c.model_dump() for c in bars]}
    monkeypatch.setattr(provider,'fetch',partial)
    r=client.post('/api/analyze',json=intent.model_dump())
    assert r.status_code==200,r.text
    assert r.json()['status']=='PARTIAL DATA'
    assert r.json()['missing_timeframes']==['1d']


def test_health_has_no_secrets(client,monkeypatch):
    monkeypatch.setattr(settings,'upstash_redis_rest_token','private-password')
    response=client.get('/api/health')
    assert response.status_code==200
    assert response.json()['jev_mode']=='disabled'
    assert 'test-only' not in response.text
    assert 'private-password' not in response.text
    assert response.json()['storage'] in ('json','redis')


def test_invalid_intent(client,intent):
    data=intent.model_dump();data['holding_period_days']=99
    assert client.post('/api/analyze',json=data).status_code==422
