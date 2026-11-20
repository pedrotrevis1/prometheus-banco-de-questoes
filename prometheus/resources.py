import sys
from pathlib import Path

OFFICIAL_ICON = "prometheus-icon-apple-iOS-Default-1024@1x.png"

def asset_path(name):
    root = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent.parent))
    return root / "prometheus" / "assets" / name


def application_icon_path():
    """Return the official application icon in source and frozen builds."""
    root = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent.parent))
    return root / "icon" / "prometheus-icon-apple Exports" / OFFICIAL_ICON
