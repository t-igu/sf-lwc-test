# storage_server/app/queue_manager.py
from __future__ import annotations

from pathlib import Path
import msgspec
from datetime import datetime, timedelta
from typing import Any

from storage_server.app.config_loader import resolve_path
from storage_server.app.const import QUEUE_DIR

# ------------------------------------------------------------
# queue ディレクトリの初期化
# ------------------------------------------------------------
QUEUE_BASE = resolve_path(QUEUE_DIR)

ACCEPTED = QUEUE_BASE / "accepted"
PROCESSING = QUEUE_BASE / "processing"
COMPLETED = QUEUE_BASE / "completed"
ERROR = QUEUE_BASE / "error"

def _ensure_dirs() -> None:
    for d in (ACCEPTED, PROCESSING, COMPLETED, ERROR):
        d.mkdir(parents=True, exist_ok=True)

_ensure_dirs()

# ------------------------------------------------------------
# atomic write
# ------------------------------------------------------------
def _atomic_write_json(path: Path, data: Any) -> None:
    """
    JSON を一時ファイルに書き出してから rename することで atomic write を保証する。
    """
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_bytes(msgspec.json.encode(data))
    tmp.replace(path)


# ------------------------------------------------------------
# QueueModel → accepted/ に書き込む
# ------------------------------------------------------------
def create_queue_file(item: Any) -> Path:
    """
    Queue エントリを accepted/ に作成する。
    item は msgspec.Struct / dict どちらでも OK。
    """
    queue_file = ACCEPTED / f"{getattr(item, 'id', None)}.json"
    _atomic_write_json(queue_file, item)
    return queue_file


# ------------------------------------------------------------
# 状態遷移（atomic move）
# ------------------------------------------------------------
def move_to_processing(queue_file: Path) -> Path:
    dest = PROCESSING / queue_file.name
    queue_file.replace(dest)
    return dest


def move_to_completed(queue_file: Path, delete: bool = True) -> Path | None:
    dest = COMPLETED / queue_file.name
    queue_file.replace(dest)
    if delete:
        dest.unlink(missing_ok=True)
        return None
    return dest


def move_to_error(queue_file: Path) -> Path:
    dest = ERROR / queue_file.name
    queue_file.replace(dest)
    return dest


# ------------------------------------------------------------
# cleanup
# ------------------------------------------------------------
def delete_old_completed(days: int = 7) -> int:
    threshold = datetime.now() - timedelta(days=days)
    deleted = 0
    for f in COMPLETED.glob("*.json"):
        if datetime.fromtimestamp(f.stat().st_mtime) < threshold:
            f.unlink(missing_ok=True)
            deleted += 1
    return deleted


def delete_old_error(days: int = 30) -> int:
    threshold = datetime.now() - timedelta(days=days)
    deleted = 0
    for f in ERROR.glob("*.json"):
        if datetime.fromtimestamp(f.stat().st_mtime) < threshold:
            f.unlink(missing_ok=True)
            deleted += 1
    return deleted
