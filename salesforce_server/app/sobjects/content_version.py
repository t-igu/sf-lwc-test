# salesforce_server/app/sobjects/content_version.py

from __future__ import annotations
from pathlib import Path

from salesforce_server.app.sobjects.base import SObject
from salesforce_server.app.app import config, resolve_path


class ContentVersion(SObject):
    """
    Salesforce Mock の ContentVersion SObject。
    JSON ファイルとして保存される。
    """
    OBJECTS_DIR = resolve_path(config["salesforce"]["objects_root"]) / "ContentVersion"
    print(__name__, "ContentVersion OBJECTS_DIR:", OBJECTS_DIR)

    @classmethod
    def find_by_document_id(cls, doc_id: str):
        """
        ContentDocumentId → ContentVersion を検索する
        """
        for rec in cls.list():
            if rec.get("ContentDocumentId") == doc_id:
                return rec
        return None

