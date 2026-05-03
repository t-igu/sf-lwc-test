# salesforce_server/app/api/lwc_router.py

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles

from salesforce_server.app.app import config, resolve_path

import mimetypes
from salesforce_server.app.sobjects.content_version import ContentVersion
from salesforce_server.app.sobjects.content_version_data import ContentVersionData


router = APIRouter()  # LWC はルートにマウントする


# ------------------------------------------------------------
# LWC OSS の静的ファイルディレクトリ
# ------------------------------------------------------------
STATIC_DIR = resolve_path(config["lwc"]["dist_dir"])
OBJECTS_DIR = resolve_path(config["salesforce"]["objects_root"])

if not STATIC_DIR.exists():
    print("\n" + "=" * 60)
    print(f"警告: LWC dist ディレクトリが見つかりません: {STATIC_DIR}")
    print("先に 'cd salesforce_lwc && npm run build' を実行してください。")
    print("=" * 60 + "\n")

if not OBJECTS_DIR.exists():
    print("\n" + "=" * 60)
    print(f"警告: objects_root ディレクトリが見つかりません: {OBJECTS_DIR}")
    print("=" * 60 + "\n")

print(f"[LWC] STATIC_DIR = {STATIC_DIR}")
print(f"[LWC] OBJECTS_DIR = {OBJECTS_DIR}")


@router.get("/sfc/servlet.shepherd/version/download/{doc_id}")
async def mock_download(doc_id: str):
    """
    Salesforce のファイルダウンロード URL を模倣する。
    ContentDocumentId → 最新の ContentVersion → バイナリ返却
    """
    # ContentDocumentId → ContentVersion を検索
    version = ContentVersion.find_by_document_id(doc_id)
    if not version:
        print(f"ファイルが見つかりません: {version}")
        raise HTTPException(status_code=404, detail="ContentVersion not found")

    version_id = version["Id"]

    # ContentVersionData の実体ファイルがあるか？
    if not ContentVersionData.exists(version_id):
        raise HTTPException(status_code=404, detail="VersionData not found")

    # Content-Type 推測
    filename = version.get("Title") or "download.bin"
    mime, _ = mimetypes.guess_type(filename)

    return StreamingResponse(
        ContentVersionData.iter_binary(version_id),
        media_type=mime or "application/octet-stream",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        }
    )

# ------------------------------------------------------------
# LWC OSS の静的ファイル配信
# ------------------------------------------------------------
def mount_static(app):
    """
    app.py から呼ばれる。
    LWC dist を "/" にマウントする。
    """
    app.mount(
        "/",
        StaticFiles(directory=STATIC_DIR, html=True),
        name="lwc",
    )
