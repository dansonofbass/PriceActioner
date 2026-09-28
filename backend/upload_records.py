"""Explicit opt-in: copy local history/log documents to the user's configured MongoDB.

Does not copy admin credentials, sessions, visitors or daily quotas.
Existing remote IDs are never overwritten. No upload occurs without --confirm.
"""
import argparse
import json
from pathlib import Path
from app.config import settings
from app.storage.documents import MongoStore


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--confirm',action='store_true',help='Actually upload local history/logs to configured MongoDB')
    args=parser.parse_args()
    root=Path(settings.local_data_dir)
    files={name:list((root/name).glob('*.json')) for name in ('analyses','logs')}
    print('Local documents:',{name:len(paths) for name,paths in files.items()})
    if not args.confirm:
        print('Preview only. Set your private MONGODB_URI in .env, then rerun with --confirm to upload.')
        return
    if not settings.mongodb_uri:
        raise SystemExit('MONGODB_URI is missing. No upload performed.')
    target=MongoStore(settings.mongodb_uri,settings.mongodb_database)
    target.initialize()
    for name,paths in files.items():
        inserted=0
        for path in paths:
            doc=json.loads(path.read_text(encoding='utf-8'))
            inserted+=target.insert_once(name,doc['_id'],doc)
        print(f'{name}: inserted {inserted}; existing IDs preserved')


if __name__=='__main__':main()
