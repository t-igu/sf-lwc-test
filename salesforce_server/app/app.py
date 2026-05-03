# salesforce_server/app/app.py

from __future__ import annotations
from pathlib import Path
import tomllib


# ------------------------------------------------------------
# 1. プロジェクトルート
# ------------------------------------------------------------
ROOT_DIR = Path(__file__).resolve().parents[2]


# ------------------------------------------------------------
# 2. config.toml 読み込み
# ------------------------------------------------------------
def load_config() -> dict:
    config_path = ROOT_DIR / "config" / "config.toml"
    with open(config_path, "rb") as f:
        return tomllib.load(f)


config = load_config()


# ------------------------------------------------------------
# 3. resolve_path（storage と同じ）
# ------------------------------------------------------------
def resolve_path(path: str | Path) -> Path:
    p = Path(path)
    if p.is_absolute():
        return p
    return (ROOT_DIR / p).resolve()


