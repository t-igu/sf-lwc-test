# storage_server/app/api/download_router.py
from fastapi import APIRouter, BackgroundTasks, Request, Header, Body
import msgspec

from storage_server.app.models import QueueModel, DownloadMaster__c
from storage_server.app.queue_manager import create_queue_file
from storage_server.app.worker.notify import notify_error
from storage_server.app.models import DownloadMaster__c
from storage_server.app.logging_decorator import trace_action
from pydantic import BaseModel
from storage_server.app.security.crypto import decrypt_path, validate_path

from pathlib import Path

class DownloadMasterModel(BaseModel):
    id: str
    filename: str
    filename_disp: str | None = None
    encrypted_filepath: str
    extension: str
    status: str

class DownloadRequestModel(BaseModel):
    request: list[DownloadMasterModel]

class DownloadRequest(msgspec.Struct):
    request: list[DownloadMaster__c]

decoder = msgspec.json.Decoder(type=DownloadRequest)

router = APIRouter(prefix="")


@trace_action
async def output_queue(request_id: str, masters: list[DownloadMaster__c]):
    """
    Apex Mock → Storage に送られた DownloadMaster__c の list を処理し、
    QueueModel に変換して queue/accepted に保存する。
    Worker は queue/accepted を監視して処理する。
    """

    # 2. 各 DownloadMaster__c を QueueModel に変換して queue に保存
    for dm in masters:
        try:
            # decrypt / validate / file existence check は後で実装
            decrypted = decrypt_path(dm.encrypted_filepath)
            safe_path = validate_path(Path(decrypted))
        except Exception as e:
            # Salesforce Mock にエラー通知（3回リトライ）
            await notify_error(dm.id, str(e))
            # continue

        # QueueModel に変換
        queue_item = QueueModel(
            request_id=request_id,
            id=dm.id,
            filename=dm.filename,
            encrypted_filepath=dm.encrypted_filepath,
            extension=dm.extension,
            status="Pending",
            retry_count=0,
            last_error=None,
        )

        # queue/accepted に JSON を保存（atomic write）
        create_queue_file(queue_item)

    print(f"[output_queue] Completed processing request_id={request_id}")


@trace_action
async def handle_download_request(fastapi_req, background_tasks, request_id):
    raw = await fastapi_req.body()
    data = decoder.decode(raw)
    downloads = data.request

    background_tasks.add_task(output_queue, request_id, downloads)

    return {
        "status": "accepted",
        "request_id": request_id,
        "status_code": 202,
    }


@router.post("/download-request", status_code=202)
async def create_download_request(
    fastapi_req: Request,
    background_tasks: BackgroundTasks,
    request_id: str = Header(None, alias="X-Request-Id"),
    _: DownloadRequestModel = Body(...),
):
    return await handle_download_request(fastapi_req, background_tasks, request_id)

