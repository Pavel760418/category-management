from pathlib import Path
import yaml

BASE = Path(__file__).resolve().parents[1] / "config"


def load_yaml(name: str):
    with open(BASE / name, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)
