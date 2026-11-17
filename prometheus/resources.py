import sys
from pathlib import Path


def asset_path(name):
    root = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent.parent))
    return root / "prometheus" / "assets" / name
