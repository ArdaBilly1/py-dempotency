from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from .exceptions import MissingIdempotencyKey
from .storage import MemoryStorage
from .models import CachedResponse

IDEMPOTENCY_HEADER = "Idempotency-Key"

class IdempotencyMiddleware(BaseHTTPMiddleware):
        def __init__(self, app, storage = None):
            super().__init__(app)
            self.storage = storage or MemoryStorage()

        async def dispatch(self, request, call_next):
            key = request.headers.get(IDEMPOTENCY_HEADER)

            if not key:
                raise MissingIdempotencyKey("Missing Idempotency-Key header")
            
            # 1. Check cached response
            cached = await self.storage.get(key)
            if cached:
                 return JSONResponse(
                      content=cached.body,
                      status_code=cached.status_code,
                      headers=cached.headers
                 )
            
            # 2. Execute original request
            response = await call_next(request)

            # 3. Save Response
            body = b"".join([section async for section in response.body_iterator])
            response.body_iterator = iter([body]) #reassign body

            cached_resp = CachedResponse(
                 status_code=response.status_code,
                 headers=dict(response.headers),
                 body=body.decode()
            )

            await self.storage.set(key, cached_resp)

            return response