from __future__ import annotations
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from salesforce_server.app.app import ROOT_DIR as PROJECT_ROOT

# ------------------------------------------------------------
# 1. lifespan
# ------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("[salesforce_server] startup")
    yield
    print("[salesforce_server] shutdown")


# ------------------------------------------------------------
# 2. FastAPI app
# ------------------------------------------------------------
app = FastAPI(
    title="Salesforce Mock Server",
    version="1.0.0",
    lifespan=lifespan,
)


# ------------------------------------------------------------
# 3. Routers（先に登録する）
# ------------------------------------------------------------
from salesforce_server.app.api.apex_router import router as apex_router
from salesforce_server.app.api.cdc_router import router as cdc_router
from salesforce_server.app.api.restapi_router import router as restapi_router
from salesforce_server.app.api.lwc_router import router as lwc_router
from salesforce_server.app.api.auth_router import router as auth_router

app.include_router(auth_router)
app.include_router(lwc_router)
app.include_router(apex_router)
app.include_router(cdc_router)
app.include_router(restapi_router)


# ------------------------------------------------------------
# 4. LWC 静的ファイル（最後に mount）
# ------------------------------------------------------------
LWC_DIR = PROJECT_ROOT / "salesforce_lwc" / "dist"

app.mount("/", StaticFiles(directory=LWC_DIR, html=True), name="lwc")
