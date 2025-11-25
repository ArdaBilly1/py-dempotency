# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Project Overview

This is a Python library implementing idempotency middleware for FastAPI/Starlette applications. The middleware intercepts HTTP requests with `Idempotency-Key` headers and caches responses to ensure the same request returns the same response, preventing duplicate operations (e.g., duplicate payments, double submissions).

## Architecture

### Core Components

**middleware.py** - `IdempotencyMiddleware` (Starlette middleware)
- Main entry point: intercepts all requests
- Flow: check cache → execute request if not cached → store response → return
- Uses `Idempotency-Key` header to identify duplicate requests
- Streams response body into memory to cache it

**storage.py** - `MemoryStorage` (async storage backend)
- In-memory dict with asyncio lock for thread safety
- Interface: `get(key)` and `set(key, response)`
- Designed to be swappable (can implement Redis, DB backends)

**models.py** - `CachedResponse` (Pydantic model)
- Stores: status_code, headers, body
- Used to serialize/deserialize cached responses

**exceptions.py** - `MissingIdempotencyKey`
- Raised when required `Idempotency-Key` header is missing

### Key Design Patterns

1. **Storage abstraction**: Middleware accepts any storage backend that implements `get/set` interface
2. **Async-first**: All storage operations are async to support high-concurrency scenarios
3. **Body streaming handling**: Response bodies are streamed iterators; middleware consumes and reassigns them

## Development Commands

### Running the code
This is a library, not a standalone application. To test:
```python
# In a FastAPI app:
from fastapi import FastAPI
from idempotency.middleware import IdempotencyMiddleware

app = FastAPI()
app.add_middleware(IdempotencyMiddleware)
```

### Testing
No test framework is currently configured. To add tests, use pytest:
```bash
pip install pytest pytest-asyncio httpx
pytest tests/
```

### Linting/Formatting
No linting tools configured yet. To add:
```bash
pip install ruff
ruff check .
ruff format .
```

## Known Issues

1. **storage.py:7** - Syntax error: `self.store= Dict(str, CachedResponse) = {}` should be `self.store: Dict[str, CachedResponse] = {}`
2. **storage.py:11** - `await self.store.get(key)` is incorrect; should be `self.store.get(key)` (dict is not awaitable)
3. **Empty files**: `pyproject.toml`, `README.md`, and `__init__.py` are empty and need content
4. No package dependencies defined (needs `pydantic`, `starlette` at minimum)

## Extending the Project

### Adding a new storage backend
1. Create a new class in `storage.py` or separate file
2. Implement async methods: `get(key: str) -> Optional[CachedResponse]` and `set(key: str, response: CachedResponse) -> None`
3. Pass instance to `IdempotencyMiddleware(app, storage=YourStorage())`

### Configuration options to consider
- TTL/expiration for cached responses
- Selective route protection (not all endpoints need idempotency)
- Custom header name instead of `Idempotency-Key`
- Response size limits (don't cache large responses)
