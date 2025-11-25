import asyncio
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