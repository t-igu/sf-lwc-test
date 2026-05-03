# storage_server/app/security/crypto.py

from __future__ import annotations
from pathlib import Path
from cryptography.fernet import Fernet

from storage_server.app.config_loader import config, resolve_path


# ---------------------------------------------------------
# Fernet 初期化（import 時に key を読まない）
# ---------------------------------------------------------
def get_fernet() -> Fernet:
    key = config["security"]["fernet_key"]
    return Fernet(key)


# ---------------------------------------------------------
# 暗号化（Salesforce 側で使用）
# ---------------------------------------------------------
def encrypt_path(path: Path) -> str:
    f = get_fernet()
    return f.encrypt(str(path).encode("utf-8")).decode("utf-8")


# ---------------------------------------------------------
# 復号化（Storage 側で使用）
# ---------------------------------------------------------
def decrypt_path(enc: str) -> str:
    f = get_fernet()
    return f.decrypt(enc.encode("utf-8")).decode("utf-8")


# ---------------------------------------------------------
# Path Traversal 防止
# ---------------------------------------------------------
def validate_path(path: Path) -> Path:
    resolved = path.resolve()
    root_dir = resolve_path("")
    if not str(resolved).startswith(str(root_dir)):
        raise ValueError(f"Path traversal detected: {resolved}")

    if not resolved.exists():
        raise FileNotFoundError(f"File not found: {resolved}")


    return resolved
