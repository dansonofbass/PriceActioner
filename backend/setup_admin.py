"""Interactive local bootstrap. Stores only a salted password hash, never a password."""
import getpass
import secrets
from pathlib import Path


def main():
    path=Path('.env')
    content=path.read_text(encoding='utf-8') if path.exists() else Path('.env.example').read_text(encoding='utf-8')
    username=input('Admin username [admin]: ').strip() or 'admin'
    password=getpass.getpass('New admin password (12+ characters): ')
    if len(password)<12: raise SystemExit('Password must have at least 12 characters.')
    if password!=getpass.getpass('Confirm password: '): raise SystemExit('Passwords do not match.')
    values={}
    for line in content.splitlines():
        if '=' in line and not line.startswith('#'):
            key,value=line.split('=',1); values[key]=value
    values['ADMIN_USERNAME']=username
    values['ADMIN_PASSWORD']=''  # bootstrap hash is written directly to document storage
    values['ADMIN_SECRET_KEY']=values.get('ADMIN_SECRET_KEY') or secrets.token_urlsafe(48)
    values['JEV_MODE']='disabled'
    path.write_text('\n'.join(f'{key}={value}' for key,value in values.items())+'\n',encoding='utf-8')
    from app.storage.service import storage
    from app.auth.service import hash_password
    storage.initialize()
    storage.put('admins',username,{'username':username,'password_hash':hash_password(password)})
    storage.delete_where('sessions',{'username':username})
    print('Admin ready. Password stored as a salted scrypt hash. Restart the backend to load .env.')


if __name__=='__main__': main()
