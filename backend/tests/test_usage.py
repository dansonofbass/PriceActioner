from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
import uuid
import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from app.main import app
from app.api.usage import reserve, status, refund
from app.providers.binance import provider


@pytest.fixture
def client(document_store):
    with TestClient(app) as client: yield client


def test_usage_sets_private_cookie_without_consuming(client):
    first=client.get('/api/usage')
    assert first.status_code==200
    assert first.json()['remaining']==3
    assert first.json()['scope']=='browser'
    assert 'HttpOnly' in first.headers['set-cookie']
    assert 'SameSite=strict' in first.headers['set-cookie']
    token=client.cookies.get('priceactioner_visitor')
    for _ in range(3): assert client.get('/api/usage').json()['remaining']==3
    assert client.cookies.get('priceactioner_visitor')==token


def test_fourth_analysis_blocked_and_preview_does_not_consume(client,monkeypatch,bars,intent):
    count=0
    async def fetch(tf,refresh=False):
        nonlocal count
        count+=1
        return {'candles':[c.model_dump() for c in bars]}
    monkeypatch.setattr(provider,'fetch',fetch)
    client.get('/api/usage')
    for remaining in [2,1,0]:
        response=client.post('/api/analyze',json=intent.model_dump())
        assert response.status_code==200,response.text
        assert response.json()['usage']['remaining']==remaining
    assert client.get('/api/usage').json()['remaining']==0
    response=client.post('/api/analyze',json=intent.model_dump())
    assert response.status_code==429 and 'Daily limit reached' in response.text
    assert count==15


def test_failures_and_invalid_forms_do_not_consume(client,monkeypatch,intent):
    async def unavailable(tf,refresh=False):raise ValueError('unavailable')
    monkeypatch.setattr(provider,'fetch',unavailable)
    client.get('/api/usage')
    for _ in range(4):
        assert client.post('/api/analyze',json=intent.model_dump()).status_code==503
    assert client.get('/api/usage').json()['remaining']==3
    assert client.post('/api/analyze',json={}).status_code==422
    assert client.get('/api/usage').json()['remaining']==3


def test_resets_at_utc_midnight_and_refund_uses_original_day(client,monkeypatch):
    now=datetime(2026,9,28,23,59,tzinfo=timezone.utc)
    monkeypatch.setattr('app.api.usage.utc_now',lambda:now)
    digest=uuid.uuid4().hex
    day=reserve(digest)
    assert status(digest)['remaining']==2
    assert status(digest)['resets_at']=='2026-09-29T00:00:00+00:00'
    now+=timedelta(minutes=2)
    assert status(digest)['remaining']==3
    reserve(digest)
    refund(digest,day)
    assert status(digest)['remaining']==2


def test_concurrent_reservations_cannot_exceed_three(client):
    digest=uuid.uuid4().hex
    def attempt(_):
        try:reserve(digest);return True
        except HTTPException as exc:
            assert exc.status_code==429
            return False
    with ThreadPoolExecutor(max_workers=8) as executor:
        admitted=list(executor.map(attempt,range(8)))
    assert sum(admitted)==3
    assert status(digest)['used']==3


def test_other_browser_has_separate_allowance(client,monkeypatch,bars,intent):
    async def fetch(tf,refresh=False):return {'candles':[c.model_dump() for c in bars]}
    monkeypatch.setattr(provider,'fetch',fetch)
    client.get('/api/usage')
    assert client.post('/api/analyze',json=intent.model_dump()).json()['usage']['remaining']==2
    with TestClient(app) as other:
        assert other.get('/api/usage').json()['remaining']==3
    assert client.get('/api/usage').json()['remaining']==2
