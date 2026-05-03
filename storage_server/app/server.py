# storage_server/app/server.py

from fastapi import FastAPI, Request
from storage_server.app.api.routers import router as api_router
from storage_server.app.logging_context import bind_request_id, clear_context
from storage_server.app.logging_config import setup_logging
setup_logging()

app = FastAPI()
app.include_router(api_router)

@app.middleware("http")
async def add_request_id(request: Request, call_next):
    req_id = request.headers.get("X-Request-Id")
    bind_request_id(req_id)
    try:
        response = await call_next(request)
        return response
    finally:
        clear_context()

