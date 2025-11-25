from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request
from .exceptions import MissingIdempotencyKey
from .storage import MemoryStorage
from .models import CachedResponse

IDEMPOTENCY_HEADER = "Idempotency-Key"


class IdempotencyMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, storage=None):
        super().__init__(app)
        self.app = app
        self.storage = storage or MemoryStorage()

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)

        request = Request(scope, receive)

        key = request.headers.get(IDEMPOTENCY_HEADER)
        if not key:
            raise MissingIdempotencyKey("Missing Idempotency-Key header")

        # 1. Check cache
        cached = await self.storage.get(key)
        if cached:
            await send({
                "type": "http.response.start",
                "status": cached.status_code,
                "headers": [
                    (k.encode(), v.encode()) for k, v in cached.headers.items()
                ],
            })
            await send({
                "type": "http.response.body",
                "body": cached.body.encode(),
            })
            return

        # Capture request body so downstream handlers can read it
        raw_body = await request.body()

        async def receive_with_body():
            return {"type": "http.request", "body": raw_body, "more_body": False}

        # Prepare response capture variables
        response_body = b""
        status_code = 200
        headers = {}

        async def send_wrapper(message):
            nonlocal response_body, status_code, headers

            if message["type"] == "http.response.start":
                status_code = message["status"]
                headers = {
                    k.decode(): v.decode() for (k, v) in message["headers"]
                }

            if message["type"] == "http.response.body":
                response_body += message.get("body", b"")

            await send(message)

        # Run downstream
        await self.app(scope, receive_with_body, send_wrapper)

        # Save cache
        cached_resp = CachedResponse(
            status_code=status_code,
            headers=headers,
            body=response_body.decode()
        )

        await self.storage.set(key, cached_resp)
