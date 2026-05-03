from __future__ import annotations
import base64
import uuid
import asyncio
import httpx
from pathlib import Path
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse

from salesforce_server.app.app import config
from salesforce_server.app.sobjects.download_master import DownloadMaster
from salesforce_server.app.sobjects.content_version import ContentVersion
from salesforce_server.app.sobjects.content_ducument_link import ContentDocumentLink

router = APIRouter(prefix=f"/services/data/{config['salesforce']['api_version']}/sobjects")

CDC_RELAY_URL = f"{config['salesforce']['base_url']}/cdc/relay"


# ------------------------------------------------------------
# CDC Relay → LWC へイベント通知
# ------------------------------------------------------------
def push_cdc_event(id: str, status: str | None, doc_id: str | None):
    payload = {
        "id": id,
        "status": status,
        "content_document_id": doc_id,
        "event_type": "DownloadMaster__c",
    }

    async def send():
        async with httpx.AsyncClient() as client:
            await client.post(CDC_RELAY_URL, json=payload)
        print(f"[CDC] Relay sent: {payload}")

    asyncio.create_task(send())


# ------------------------------------------------------------
# ContentVersion (POST)
# ------------------------------------------------------------
@router.post("/ContentVersion")
async def create_content_version(request: Request):
    """
    VersionData(Base64) を受け取り、実体ファイルとして保存する Salesforce モック。
    FirstPublishLocationId を指定すると ContentDocumentLink を自動生成する。
    """
    data = await request.json()

    version_id = f"068{uuid.uuid4().hex[:12]}"
    document_id = f"069{uuid.uuid4().hex[:12]}"

    # -----------------------------
    # VersionData(Base64) → バイナリ保存
    # -----------------------------
    version_data_b64 = data.get("VersionData")
    if version_data_b64:
        try:
            file_bytes = base64.b64decode(version_data_b64)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid Base64 VersionData")

        # 保存先ディレクトリ
        data_dir = Path("objects/ContentVersionData")
        data_dir.mkdir(parents=True, exist_ok=True)

        # versionId をファイル名として保存
        file_path = data_dir / version_id
        file_path.write_bytes(file_bytes)

    # -----------------------------
    # ContentVersion メタデータ保存
    # -----------------------------
    version_record = {
        "Id": version_id,
        "ContentDocumentId": document_id,
        "Title": data.get("Title"),
        "PathOnClient": data.get("PathOnClient"),
        "VersionData": None,  # 本番と同じく保存しない
        "FirstPublishLocationId": data.get("FirstPublishLocationId"),
    }

    ContentVersion.insert(version_id, version_record)

    # -----------------------------
    # FirstPublishLocationId → DownloadMaster__c に自動リンク
    # -----------------------------
    parent_id = data.get("FirstPublishLocationId")
    if parent_id:
        # DownloadMaster__c に ContentDocumentId を紐付け
        DownloadMaster.update(
            parent_id,
            {"ContentDocumentId__c": document_id},
        )

        # ContentDocumentLink 自動生成
        ContentDocumentLink.insert(
            document_id,
            {
                "ContentDocumentId": document_id,
                "LinkedEntityId": parent_id,
                "ShareType": "V",
            },
        )

    return {"id": version_id, "ContentDocumentId": document_id}


# ------------------------------------------------------------
# DownloadMaster__c PATCH
# ------------------------------------------------------------
@router.patch("/DownloadMaster__c/{id}")
async def update_download_master(id: str, data: dict):

    update_data = {}

    if "Status__c" in data:
        update_data["Status__c"] = data["Status__c"]

    status_map = {
        "Completed": "Completed",
        "完了": "Completed",
        "Error": "Error",
        "失敗": "Error",
    }
    if data.get("Status__c") in status_map:
        update_data["status"] = status_map[data["Status__c"]]

    if "ContentDocumentId__c" in data:
        update_data["ContentDocumentId__c"] = data["ContentDocumentId__c"]

    record = DownloadMaster.update(id, update_data)
    if record is None:
        raise HTTPException(status_code=404, detail="not found")

    push_cdc_event(
        id=id,
        status=record.get("status"),
        doc_id=record.get("ContentDocumentId__c"),
    )

    return JSONResponse({"success": True})
