# salesforce_server/app/api/apex_router.py

from __future__ import annotations
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
import httpx
import json
from pathlib import Path

from salesforce_server.app.app import config, resolve_path
from salesforce_server.app.sobjects.download_master import DownloadMaster


router = APIRouter(prefix="/apex")

STORAGE_BASE_URL = config["storage"]["base_url"]


# ---------------------------------------------------------
# スキーマ配信
# ---------------------------------------------------------
@router.get("/schema")
async def get_schema():
    schema_path = resolve_path("schema/schema.json")
    with open(schema_path, "r", encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------
# DownloadMaster__c 一覧取得（LWC 用）
# ---------------------------------------------------------
@router.get("/api/download-masters")
async def list_download_master():
    return DownloadMaster.list()


# ---------------------------------------------------------
# Download Request
# ---------------------------------------------------------
@router.post("/download-request")
async def download_request(data: dict):

    file_ids = data.get("file_ids")
    if not file_ids or not isinstance(file_ids, list):
        raise HTTPException(status_code=400, detail="file_ids is required")

    # ------------------------------------------------------------
    # request_id を生成（Storage の分散トレース用）
    # ------------------------------------------------------------
    import uuid
    request_id = str(uuid.uuid4())

    # Storage に送る DownloadMaster__c list
    storage_request_list = []

    for fid in file_ids:
        dm = DownloadMaster.find(fid)

        if dm is None:
            print(f"[WARN] DownloadMaster not found: {fid}")
            continue

        # Status を Pending に更新
        updated = DownloadMaster.update(
            fid,
            {
                "Status__c": "Pending",
                "LastError__c": None,
            },
        )

        if not updated:
            print(f"[ERROR] Failed to update DownloadMaster: {fid}")
            continue

        # Storage 用の DownloadMaster__c (snake_case)
# {
#   "id": "DM-001",
#   "filename": "report_2024.pdf",
#   "filename_disp": "2024年レポート.pdf",
#   "encrypted_filepath": "enc:/files/report_2024.pdf",
#   "extension": "pdf",
#   "status": "Error",
#   "Status__c": "Pending",
#   "LastError__c": null,
#   "ContentDocumentId__c": "069184c46dc123e"
# }        
        storage_request_list.append(
            {
                "id": updated["id"],
                "filename": updated["filename"],
                "filename_disp": updated.get("filename_disp"),
                "encrypted_filepath": updated["encrypted_filepath"],
                "extension": updated["extension"],
                "status": updated.get("status", "Pending"),
            }
        )

    # Storage に送る JSON は {"request": [...]}
    payload = {"request": storage_request_list}

    # ------------------------------------------------------------
    # Storage に送信（X-Request-Id を付与）
    # ------------------------------------------------------------
    async with httpx.AsyncClient() as client:
        await client.post(
            f"{STORAGE_BASE_URL}/download-request",
            json=payload,
            headers={"X-Request-Id": request_id},
        )

    # LWC が必要なのは DownloadMaster の id
    return JSONResponse(content=storage_request_list)
