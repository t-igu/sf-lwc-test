# salesforce_server/app/api/cdc_router.py

from __future__ import annotations
import json
import asyncio
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import StreamingResponse

router = APIRouter(prefix="/cdc")


# ------------------------------------------------------------
# SSE 接続管理
# id → List[asyncio.Queue]
# ------------------------------------------------------------
cdc_connections: dict[str, list[asyncio.Queue]] = {}


# ------------------------------------------------------------
# CDC Relay（Storage → Salesforce Mock → LWC）
# ------------------------------------------------------------
@router.post("/relay")
async def cdc_relay(request: Request):
    """
    Storage Worker が呼び出す。
    LWC にリアルタイム通知するための CDC Relay。
    """
    payload = await request.json()

    if not payload:
        raise HTTPException(status_code=400, detail="no payload")

    # Storage 側は "id" を送る
    record_id = payload.get("id")
    if not record_id:
        raise HTTPException(status_code=400, detail="no id")

    # SSE push
    queues = cdc_connections.setdefault(record_id, [])
    data = json.dumps(payload, ensure_ascii=False)

    for q in queues:
        await q.put(data)

    return {"status": "received"}


# ------------------------------------------------------------
# SSE Stream（LWC EventSource が接続する）
# ------------------------------------------------------------
@router.get("/stream/{id}")
async def cdc_stream(id: str):
    """
    LWC が EventSource で接続する SSE ストリーム。
    id ごとに独立したストリームを持つ。
    """
    queue = asyncio.Queue()
    cdc_connections.setdefault(id, []).append(queue)

    async def event_generator():
        try:
            while True:
                try:
                    # イベント待ち（25秒 heartbeat）
                    data = await asyncio.wait_for(queue.get(), timeout=25)
                    yield f"data: {data}\n\n"
                except asyncio.TimeoutError:
                    # heartbeat
                    yield ": heartbeat\n\n"
        finally:
            # 切断時クリーンアップ
            cdc_connections[id].remove(queue)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
    )
