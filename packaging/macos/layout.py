"""Shared macOS release identity and Finder layout; importing builds nothing."""
from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parents[2]
VERSION = runpy.run_path(str(ROOT / "prometheus" / "__init__.py"))["__version__"]
APP_NAME = "Prometheus"
BUNDLE_NAME = f"{APP_NAME}.app"
BUNDLE_ID = "com.pedrotrevisan.prometheus"
MINIMUM_MACOS = "15.0"
APP_ICON = ROOT / "icon" / "prometheus-icon-apple Exports" / "prometheus-icon-apple-iOS-Default-1024@1x.png"
WINDOW_SIZE = (640, 420)
ICON_SIZE = 112
ICON_LOCATIONS = {BUNDLE_NAME: (180, 224), "Aplicativos": (460, 224)}


def dmg_settings(application, background):
    """Return dmgbuild settings with real, draggable Finder items."""
    return {
        "format": "UDZO",
        "filesystem": "HFS+",
        "files": [(str(application), BUNDLE_NAME)],
        "symlinks": {"Aplicativos": "/Applications"},
        "background": str(background),
        "window_rect": ((160, 160), WINDOW_SIZE),
        "default_view": "icon-view",
        "show_toolbar": False,
        "show_sidebar": False,
        "show_status_bar": False,
        "show_pathbar": False,
        "show_tab_view": False,
        "arrange_by": None,
        "grid_spacing": 80,
        "scroll_position": (0, 0),
        "icon_size": ICON_SIZE,
        "text_size": 13,
        "label_pos": "bottom",
        "icon_locations": ICON_LOCATIONS.copy(),
        "include_icon_view_settings": True,
        "include_list_view_settings": False,
    }
