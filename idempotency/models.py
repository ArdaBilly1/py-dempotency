from pydantic import BaseModel
from typing import Any

class CachedResponse(BaseModel):
    status_code:int
    headers: dict
    body: Any
