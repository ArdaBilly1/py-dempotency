import asyncio
import redis.asyncio as redis
import json
from typing import Dict
from .models import CachedResponse

class MemoryStorage:
    def __init__(self):
        self.store: Dict[str, CachedResponse] = {}
        self.lock = asyncio.Lock()
        
    async def get(self, key: str):
        async with self.lock:
            return self.store.get(key)
    
    async def set(self, key:str, response: CachedResponse):
        async with self.lock:
            self.store[key] = response

class RedisStorage:
    def __init__(self, url:str, prefix="idem:"):
        self.redis = redis.from_url(url, decode_responses=True)
        self.prefix = prefix

    def _key(self, key: str):
        return f"{self.prefix}{key}"
    
    async def get(self, key:str):
        raw = await self.redis.get(self._key(key))
        if not raw:
            return None
        
        data = json.loads(raw)
        return CachedResponse(
            status_code=data["status_code"],
            headers=data["headers"],
            body=data["body"]
        )
    
    async def set(self, key:str, response: CachedResponse):
        payload = json.dumps({
            "status_code":response.status_code,
            "headers":response.headers,
            "body":response.body
        })

        await self.redis.set(self._key(key), payload, ex=60*5)

