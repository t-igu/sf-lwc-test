# salesforce_server/app/sobjects/content_version.py

from __future__ import annotations
from pathlib import Path

from salesforce_server.app.sobjects.base import SObject
from salesforce_server.app.app import config, resolve_path


class ContentDocumentLink(SObject):
    """
    Salesforce Mock の ContentVersion SObject。
    JSON ファイルとして保存される。
    """
    OBJECTS_DIR = resolve_path(config["salesforce"]["objects_root"]) / "ContentDocumentLink"
