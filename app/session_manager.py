import json, secrets
from cryptography.fernet import Fernet
from redis.asyncio import Redis
from .config import settings
redis=Redis.from_url(settings.redis_url,decode_responses=True)

def _cipher():
    if not settings.fernet_key: raise RuntimeError("FERNET_KEY is not configured; refusing to persist broker secrets")
    return Fernet(settings.fernet_key.encode())
async def save_session(user_id:str,provider:str,credentials:dict,ttl=43200):
    encrypted=_cipher().encrypt(json.dumps(credentials).encode()).decode()
    ttl=max(1,min(int(ttl),43200))
    await redis.set(f"broker:session:{user_id}:{provider}",encrypted,ex=ttl)
async def get_session(user_id,provider):
    val=await redis.get(f"broker:session:{user_id}:{provider}")
    if not val: return None
    return json.loads(_cipher().decrypt(val.encode()))
async def create_oauth_state(provider,ttl=600):
    token=secrets.token_urlsafe(32)
    await redis.set(f"oauth:state:{token}",provider,ex=ttl)
    return token
async def consume_oauth_state(token,provider):
    key=f"oauth:state:{token}"
    saved=await redis.get(key)
    if saved!=provider: return False
    await redis.delete(key)
    return True
