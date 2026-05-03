# salesforce_server/app/sobjects/download_master.py

from __future__ import annotations
from pathlib import Path

from salesforce_server.app.sobjects.base import SObject
from salesforce_server.app.app import config, resolve_path


class DownloadMaster(SObject):
    """
    Salesforce Mock の DownloadMaster__c SObject。
    JSON ファイルとして保存される。
    """
    OBJECTS_DIR = resolve_path(config["salesforce"]["objects_root"]) / "DownloadMaster__c"
