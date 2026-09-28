import json
import httpx
import fakeredis
import pytest
from fastapi.testclient import TestClient
from app.storage.redis_store import RedisStore, RestClient, StorageUnavailable


def test_rest_transport_and_scripts_retention_and_expiry():
    server = fakeredis.FakeRedis(decode_responses=True)
    def handle(request):
        assert request.headers['authorization'] == 'Bearer private-token'
        command = json.loads(request.content)
        result=server.execute_command(*command)
        if command[0]=='PING': result='PONG'
        return httpx.Response(200, json={'result': result})
    client = RestClient('https://example.upstash.io', 'private-token', httpx.Client(transport=httpx.MockTransport(handle)))
    store = RedisStore(client=client)
    store.limits = {'analyses': 2, 'logs': 3}
    assert store.ping()
    for i in range(5):
        store.put('analyses', str(i), {'timestamp':str(i), 'payload':'متن'*3000})
        store.put('logs', str(i), {'timestamp':str(i)})
    assert [r['_id'] for r in store.find('analyses')] == ['4','3']
    assert store.get('analyses','0') is None
    assert store.get('analyses','4')['payload']=='متن'*3000
    assert len(store.find('logs'))==3
    assert 0 < server.ttl(store._key('analyses','4')) <= 604800
    assert store.reserve('daily_usage','v:today',3)
    counter=store._key('daily_usage','v:today')
    server.expire(counter,60)
    assert store.reserve('daily_usage','v:today',3)
    store.refund('daily_usage','v:today')
    assert 0 < server.ttl(counter) <= 60
    server.expire(counter,0)
    assert store.get('daily_usage','v:today') is None
    assert store.reserve('daily_usage','v:tomorrow',3)
    store.put('admins','admin',{'password_hash':'hash'})
    assert server.ttl(store._key('admins','admin'))==-1


@pytest.mark.parametrize('status,body',[(401,{'error':'private upstream token'}),(200,{'error':'private upstream token'}),(500,{'error':'private upstream token'})])
def test_rest_errors_do_not_leak_credentials(status,body):
    http = httpx.Client(transport=httpx.MockTransport(lambda request:httpx.Response(status,json=body)))
    client=RestClient('https://example.upstash.io','secret-token',http)
    with pytest.raises(StorageUnavailable) as error:client.execute_command('PING')
    assert 'secret-token' not in str(error.value) and 'private upstream' not in str(error.value)


def test_missing_redis_does_not_crash_startup(monkeypatch):
    from app.main import app
    from app import main
    from app.api import health,admin
    store=RedisStore()
    for module in (main,health,admin):monkeypatch.setattr(module,'storage',store)
    with TestClient(app) as client:
        response=client.get('/api/health')
        assert response.status_code==200
        assert response.json()['database']=='OFFLINE'
        assert response.json()['storage']=='redis'
        assert 'UPSTASH_REDIS_REST_URL' in response.json()['storage_error']
        response=client.post('/api/admin/login',json={'username':'admin','password':'anything'})
        assert response.status_code==503
        assert 'Redis is not configured' in response.json()['detail']
