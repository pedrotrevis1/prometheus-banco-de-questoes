"""Check runtime assets against the packaging commands without building."""
from pathlib import Path
import re
import shutil
import sys

import pytest
from PySide6.QtGui import QImage

from prometheus.resources import application_icon_path, asset_path


ROOT = Path(__file__).resolve().parents[1]


def assert_runtime_images_load():
    assert not QImage(str(application_icon_path())).isNull()
    assert not QImage(str(asset_path("pix_qr.jpg"))).isNull()


def test_source_assets_load_from_an_unrelated_working_directory(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert_runtime_images_load()


@pytest.mark.parametrize("platform", ["macos", "windows"])
def test_frozen_assets_load_from_build_configuration(tmp_path, monkeypatch, platform, macos_spec_calls):
    extraction = tmp_path / "_MEI simulated extraction"
    if platform == "macos":
        bundled_assets = macos_spec_calls["Analysis"][1]["datas"]
    else:
        command = (ROOT / "build_windows.ps1").read_text()
        bundled_assets = [entry.split(";", 1) for entry in re.findall(r'--add-data "([^"]+)"', command)]
    assert bundled_assets, f"No bundled assets declared for {platform}"
    for source, destination in bundled_assets:
        target = extraction / destination / Path(source).name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / source, target)

    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "_MEIPASS", str(extraction), raising=False)
    monkeypatch.chdir(tmp_path)
    assert_runtime_images_load()
