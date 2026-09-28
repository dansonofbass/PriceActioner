import base64
import hashlib
import hmac
import secrets
import time
from app.config import settings
from app.storage.service import storage


def hash_password(password: str, salt: bytes | None=None) -> str:
    salt=salt or secrets.token_bytes(16)
    digest=hashlib.scrypt(password.encode(),salt=salt,n=16384,r=8,p=1)
    return base64.b64encode(salt).decode()+':'+base64.b64encode(digest).decode()


def verify(password: str, encoded: str) -> bool:
    salt=base64.b64decode(encoded.split(':')[0])
    return hmac.compare_digest(hash_password(password,salt),encoded)


def token_hash(token: str) -> str:
    return hmac.new(settings.admin_secret_key.encode(),token.encode(),hashlib.sha256).hexdigest()


def bootstrap_admin():
    if not settings.admin_password or not settings.admin_secret_key: return
    storage.insert_once('admins',settings.admin_username,{
        'username':settings.admin_username,'password_hash':hash_password(settings.admin_password)})


def login(username,password):
    admin=storage.get('admins',username)
    dummy='MDEyMzQ1Njc4OWFiY2RlZg==:AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA='
    valid=verify(password,admin['password_hash'] if admin else dummy)
    if not admin or not valid or not settings.admin_secret_key: return None
    token=secrets.token_urlsafe(32)
    storage.delete_where('sessions',{'expires_at':{'$lt':time.time()}})
    storage.put('sessions',token_hash(token),{'username':username,'expires_at':time.time()+28800})
    return token
