from __future__ import annotations
from pathlib import Path
import tomllib

def find_project_root() -> Path:
    return Path(__file__).resolve().parents[2]

PROJECT_ROOT = find_project_root()
CONFIG_PATH = PROJECT_ROOT / "config/config.toml"

with CONFIG_PATH.open("rb") as f:
    config: dict = tomllib.load(f)

ROOT_DIR = Path(config["app"]["root_dir"]).resolve()
    
def resolve_path(relative: str | Path) -> Path:
    return ROOT_DIR / Path(relative)

