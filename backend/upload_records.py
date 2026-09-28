"""Explicit opt-in: copy local history/log documents to the user's configured Redis.

Does not copy admin credentials, sessions, visitors or daily quotas.
Existing remote IDs are never overwritten. No upload occurs without --confirm.
"""
import argparse
import json
from pathlib import Path
from app.config import settings
from app.storage.redis_store import RedisStore


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--confirm',action='store_true',help='Actually upload local history/logs to configured Redis')
    args=parser.parse_args()
    root=Path(settings.local_data_dir)
    files={name:list((root/name).glob('*.json')) for name in ('analyses','logs')}
    print('Local documents:',{name:len(paths) for name,paths in files.items()})
    if not args.confirm:
        print('Preview only. Set your private UPSTASH_REDIS_REST_URL / UPSTASH_REDIS_REST_TOKEN in .env, then rerun with --confirm to upload.')
        return
    if not settings.upstash_redis_rest_url or not settings.upstash_redis_rest_token:
        raise SystemExit('UPSTASH_REDIS_REST_URL / UPSTASH_REDIS_REST_TOKEN is missing. No upload performed.')
    target=RedisStore(settings.upstash_redis_rest_url,settings.upstash_redis_rest_token)
    target.initialize()
    for name,paths in files.items():
        inserted=0
        documents=sorted((json.loads(path.read_text(encoding='utf-8')) for path in paths),key=lambda doc:doc.get('timestamp',''))
        for doc in documents:
            inserted+=target.insert_once(name,doc['_id'],doc)
        print(f'{name}: inserted {inserted}; existing IDs preserved')


if __name__=='__main__':main()
