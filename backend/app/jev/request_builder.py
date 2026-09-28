import json
import math
from app.config import settings
from .questions import QUESTIONS


def build_request(context: dict) -> dict:
    payload={'model':settings.jev_model or None,'state':context,'questions':QUESTIONS}
    serialized=json.dumps(payload,ensure_ascii=False,separators=(',',':'),allow_nan=False)
    return {'mode':'disabled','status':'JEV REQUEST NOT SENT','model':settings.jev_model or 'not configured',
            'payload':payload,'serialized_request':serialized,'character_count':len(serialized),
            'approximate_token_count':math.ceil(len(serialized)/4),'token_estimation':'characters / 4; not a tokenizer',
            'schema_status':'Local draft for inspection; live provider schema unverified'}
