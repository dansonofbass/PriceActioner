import json
import re
from concurrent.futures import ThreadPoolExecutor
import pytest
from pydantic import ValidationError
from app.config import Settings
from app.storage.documents import JsonStore


def test_insert_update_delete_and_no_overwrite(document_store):
    store=document_store
    assert store.insert_once('admins','name',{'username':'name','password_hash':'original'})
    assert not store.insert_once('admins','name',{'password_hash':'replaced'})
    assert store.get('admins','name')['password_hash']=='original'
    store.put('sessions','token',{'username':'name','expires_at':100})
    store.put('sessions','other',{'username':'different','expires_at':200})
    store.delete_where('sessions',{'expires_at':{'$lt':150}})
    assert store.get('sessions','token') is None
    assert store.get('sessions','other') is not None
    store.delete('sessions','other')
    assert store.get('sessions','other') is None


def test_history_pagination_log_filters_literal_search(document_store):
    store=document_store
    for i in range(4):
        store.put('logs',str(i),{'timestamp':f'2026-01-0{i+1}', 'level':'INFO' if i%2 else 'ERROR',
                                'event':'literal [tag]' if i==1 else 'untagged','message':'saved'})
    assert [r['_id'] for r in store.find('logs',limit=2,offset=1)]==['2','1']
    assert len(store.find('logs',{'level':'ERROR'}))==2
    assert len(store.find('logs',{'$or':[{'event':{'$regex':re.escape('[tag]')}},{'message':{'$regex':re.escape('[tag]')}}]}))==1


def test_atomic_quota_across_independent_store_clients(document_store):
    store=document_store
    from app.storage.documents import MongoStore
    other=JsonStore(store.root) if store.kind=='json' else MongoStore('mongodb://unused','test',client=store.client)
    def attempt(i):return (store if i%2 else other).reserve('daily_usage','same-day',3)
    with ThreadPoolExecutor(max_workers=8) as executor:
        assert sum(executor.map(attempt,range(12)))==3
    assert store.get('daily_usage','same-day')['used']==3
    for _ in range(5):other.refund('daily_usage','same-day')
    assert store.get('daily_usage','same-day')['used']==0


def test_json_survives_new_instance_and_contains_json_only(tmp_path):
    store=JsonStore(tmp_path/'records')
    store.put('analyses','../../unsafe',{'timestamp':'now','result':{'x':1}})
    restored=JsonStore(tmp_path/'records')
    assert restored.get('analyses','../../unsafe')['result']=={'x':1}
    files=list(tmp_path.rglob('*.json'))
    assert len(files)==1
    assert json.loads(files[0].read_text())['_id']=='../../unsafe'
    assert not list(tmp_path.rglob('*.db'))


def test_cloud_rejects_local_storage_and_missing_connection():
    with pytest.raises(ValidationError):Settings(vercel='1',storage_backend='json')
    with pytest.raises(ValidationError):Settings(storage_backend='mongodb',mongodb_uri='')
    valid=Settings(app_env='production',storage_backend='mongodb',mongodb_uri='mongodb+srv://user:pass@example.invalid/',
                   admin_secret_key='x'*48,public_origin='https://example.com',admin_password='')
    assert valid.storage_backend=='mongodb'
