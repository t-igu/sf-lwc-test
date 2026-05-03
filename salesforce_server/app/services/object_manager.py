# salesforce_server/app/services/object_manager.py

from __future__ import annotations
import json
from pathlib import Path

from salesforce_server.app.app import config, resolve_path


# ------------------------------------------------------------
# SObject ディレクトリのルート
# ------------------------------------------------------------
OBJECTS_ROOT = resolve_path(config["salesforce"]["objects_root"])
# 例: "objects" → /path/to/salesforce_server/objects


def _object_dir(sobject_name: str) -> Path:
    """
    SObject 名からディレクトリパスを返す。
    例: DownloadMaster__c → objects/DownloadMaster__c
    """
    return OBJECTS_ROOT / sobject_name


# ------------------------------------------------------------
# 基本 CRUD 操作
# ------------------------------------------------------------
def load_object(sobject_name: str, record_id: str) -> dict | None:
    file_path = _object_dir(sobject_name) / f"{record_id}.json"
    if not file_path.exists():
        return None
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_object(sobject_name: str, record_id: str, data: dict):
    dir_path = _object_dir(sobject_name)
    dir_path.mkdir(parents=True, exist_ok=True)

    file_path = dir_path / f"{record_id}.json"
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def update_object(sobject_name: str, record_id: str, updates: dict) -> dict | None:
    record = load_object(sobject_name, record_id)
    if record is None:
        return None

    for k, v in updates.items():
        record[k] = v

    save_object(sobject_name, record_id, record)
    return record


def list_objects(sobject_name: str) -> list[dict]:
    dir_path = _object_dir(sobject_name)
    if not dir_path.exists():
        return []

    results = []
    for file in dir_path.glob("*.json"):
        with open(file, "r", encoding="utf-8") as f:
            results.append(json.load(f))
    return results
