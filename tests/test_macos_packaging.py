"""Release configuration checks; these tests never build an app or disk image."""
from pathlib import Path
import plistlib
import runpy
import shutil
import subprocess
import sys
from types import SimpleNamespace

import pytest

from prometheus import __version__


ROOT = Path(__file__).resolve().parents[1]
MACOS = ROOT / "packaging" / "macos"


def test_bundle_identity_and_finder_version_follow_source(macos_spec_calls):
    exe = macos_spec_calls["EXE"][1]
    bundle = macos_spec_calls["BUNDLE"][1]
    assert exe["name"] == "Prometheus"
    assert exe["console"] is False
    assert exe["target_arch"] == "arm64"
    assert "exclude_binaries" not in exe  # One-file executable, without COLLECT.
    assert bundle["name"] == "Prometheus.app"
    assert bundle["bundle_identifier"] == "com.pedrotrevisan.prometheus"
    assert bundle["version"] == __version__
    assert bundle["info_plist"]["CFBundleShortVersionString"] == __version__
    assert bundle["info_plist"]["CFBundleVersion"] == __version__
    assert bundle["info_plist"]["LSMinimumSystemVersion"] == "15.0"
    assert isinstance(__version__, str)
    assert "CFBundleExecutable" not in bundle["info_plist"]  # Let PyInstaller match EXE.
    entrypoints = macos_spec_calls["Analysis"][0][0]
    assert entrypoints == [str(ROOT / "prometheus" / "__main__.py")]


def test_dmg_layout_uses_real_app_and_portuguese_applications_shortcut():
    layout = runpy.run_path(str(MACOS / "layout.py"))
    settings = layout["dmg_settings"](Path("/tmp/Prometheus.app"), Path("/tmp/background.png"))
    assert settings["files"] == [("/tmp/Prometheus.app", "Prometheus.app")]
    assert settings["symlinks"] == {"Aplicativos": "/Applications"}
    assert settings["window_rect"][1] == (640, 420)
    assert settings["default_view"] == "icon-view"
    assert settings["arrange_by"] is None
    assert settings["icon_size"] == 112
    assert settings["icon_locations"] == {"Prometheus.app": (180, 224), "Aplicativos": (460, 224)}
    for key in ("show_toolbar", "show_sidebar", "show_status_bar", "show_pathbar", "show_tab_view"):
        assert settings[key] is False
    assert settings["grid_spacing"] < 100


def test_dmg_does_not_add_finderinfo_to_signed_app():
    layout = runpy.run_path(str(MACOS / "layout.py"))
    settings = layout["dmg_settings"](Path("/tmp/Prometheus.app"), Path("/tmp/background.png"))
    # dmgbuild uses SetFile for this option, invalidating strict signature checks.
    assert settings.get("hide_extensions", []) == []


def test_frozen_docx_paths_create_footer_header_and_save(tmp_path, monkeypatch, macos_spec_calls):
    from docx import Document
    from docx.parts import hdrftr
    from PyInstaller.utils.hooks import collect_data_files
    from zipfile import ZipFile

    # Reproduce explicit spec data plus the standard hook's template data.
    data = macos_spec_calls["Analysis"][1]["datas"] + collect_data_files("docx")
    for source, destination in data:
        target = tmp_path / destination / Path(source).name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
    monkeypatch.setattr(hdrftr, "__file__", str(tmp_path / "docx" / "parts" / "hdrftr.py"))
    document = Document(tmp_path / "docx" / "templates" / "default.docx")
    document.add_paragraph("Verificação do macOS — questões e gabarito")
    document.sections[0].footer.paragraphs[0].text = "Página 1"
    document.sections[0].header.paragraphs[0].text = "Verificação"
    output = tmp_path / "prova.docx"
    document.save(output)
    with ZipFile(output) as archive:
        assert archive.testzip() is None
        assert "Página 1" in archive.read("word/footer1.xml").decode()
        assert "Verificação" in archive.read("word/header1.xml").decode()


@pytest.fixture
def app_bundle(tmp_path):
    contents = tmp_path / "build with spaces" / "Prometheus.app" / "Contents"
    (contents / "MacOS").mkdir(parents=True)
    (contents / "Resources").mkdir()
    (contents / "MacOS" / "Prometheus").write_bytes(b"synthetic executable; lipo is mocked")
    (contents / "MacOS" / "Prometheus").chmod(0o755)
    (contents / "Resources" / "Prometheus.icns").write_bytes(b"synthetic icon")
    metadata = {
        "CFBundleName": "Prometheus",
        "CFBundleDisplayName": "Prometheus",
        "CFBundleExecutable": "Prometheus",
        "CFBundleIdentifier": "com.pedrotrevisan.prometheus",
        "CFBundleShortVersionString": __version__,
        "CFBundleVersion": __version__,
        "LSMinimumSystemVersion": "15.0",
        "CFBundleIconFile": "Prometheus.icns",
    }
    (contents / "Info.plist").write_bytes(plistlib.dumps(metadata))
    return contents.parent


@pytest.fixture
def dmg_tool(tmp_path, monkeypatch):
    tool = runpy.run_path(str(MACOS / "dmg.py"))
    calls = []
    monkeypatch.setattr(tool["platform"], "system", lambda: "Darwin")

    def lipo(command, **kwargs):
        calls.append(("lipo", command))
        assert command[:2] == ["/usr/bin/lipo", "-archs"]
        return SimpleNamespace(stdout="arm64\n")

    def background(directory):
        directory.mkdir()
        path = directory / "background.png"
        path.write_bytes(b"synthetic background")
        return path

    def builder(filename, volume_name, *, settings):
        calls.append(("builder", volume_name, settings))
        Path(filename).write_bytes(b"synthetic DMG; no disk-image tools ran")

    monkeypatch.setattr(subprocess, "run", lipo)
    monkeypatch.setitem(tool["create_dmg"].__globals__, "render_backgrounds", background)
    monkeypatch.setitem(sys.modules, "dmgbuild", SimpleNamespace(build_dmg=builder))
    # Route default output into the test's temporary directory.
    tool["LAYOUT"]["ROOT"] = tmp_path
    return tool, calls


@pytest.mark.parametrize("slices,label", [
    ("arm64", "arm64"), ("x86_64", "x86_64"), ("x86_64 arm64", "universal2"),
])
def test_package_names_actual_executable_architecture_and_preserves_app(app_bundle, dmg_tool, monkeypatch, slices, label):
    tool, calls = dmg_tool
    before = {path.relative_to(app_bundle): path.read_bytes() for path in app_bundle.rglob("*") if path.is_file()}

    def lipo(command, **kwargs):
        assert command == ["/usr/bin/lipo", "-archs", str(app_bundle / "Contents" / "MacOS" / "Prometheus")]
        return SimpleNamespace(stdout=slices)

    monkeypatch.setattr(subprocess, "run", lipo)
    output = tool["create_dmg"](app_bundle)
    assert output.name == f"Prometheus-{__version__}-mac-{label}.dmg"
    assert output.read_bytes() == b"synthetic DMG; no disk-image tools ran"
    _, volume, settings = calls[0]
    assert volume == "Prometheus"
    assert settings["files"] == [(str(app_bundle), "Prometheus.app")]
    assert settings["symlinks"] == {"Aplicativos": "/Applications"}
    assert sorted(output.parent.iterdir()) == [output]  # Temporary files cleaned.
    assert {path.relative_to(app_bundle): path.read_bytes() for path in app_bundle.rglob("*") if path.is_file()} == before


@pytest.mark.parametrize("key,value", [
    ("CFBundleExecutable", "WrongName"),
    ("CFBundleIdentifier", "wrong.identifier"),
    ("CFBundleShortVersionString", "0.0.0"),
    ("CFBundleVersion", 2),
    ("LSMinimumSystemVersion", "11.0"),
])
def test_inconsistent_bundle_is_rejected_before_packaging(app_bundle, dmg_tool, key, value):
    tool, calls = dmg_tool
    plist = app_bundle / "Contents" / "Info.plist"
    metadata = plistlib.loads(plist.read_bytes())
    metadata[key] = value
    plist.write_bytes(plistlib.dumps(metadata))
    with pytest.raises(ValueError, match=key):
        tool["create_dmg"](app_bundle)
    assert calls == []


@pytest.mark.parametrize("missing", ["executable", "icon", "permission"])
def test_missing_bundle_content_is_rejected(app_bundle, dmg_tool, missing):
    tool, calls = dmg_tool
    executable = app_bundle / "Contents" / "MacOS" / "Prometheus"
    if missing == "permission":
        executable.chmod(0o644)
    elif missing == "executable":
        executable.unlink()
    else:
        (app_bundle / "Contents" / "Resources" / "Prometheus.icns").unlink()
    with pytest.raises(ValueError):
        tool["create_dmg"](app_bundle)
    assert calls == []


def test_existing_output_is_not_replaced(app_bundle, dmg_tool, tmp_path):
    tool, calls = dmg_tool
    output = tmp_path / "existing.dmg"
    output.write_bytes(b"preserve existing release")
    with pytest.raises(FileExistsError):
        tool["create_dmg"](app_bundle, output)
    assert output.read_bytes() == b"preserve existing release"
    assert not any(call[0] == "builder" for call in calls)


def test_output_cannot_modify_source_bundle(app_bundle, dmg_tool):
    tool, calls = dmg_tool
    with pytest.raises(ValueError, match="fora do bundle"):
        tool["create_dmg"](app_bundle, app_bundle / "release.dmg")
    assert not (app_bundle / "release.dmg").exists()
    assert not any(call[0] == "builder" for call in calls)


def test_wrong_platform_and_missing_app_do_not_invoke_tools(dmg_tool, tmp_path, monkeypatch):
    tool, calls = dmg_tool
    monkeypatch.setattr(tool["platform"], "system", lambda: "Linux")
    with pytest.raises(ValueError, match="Mac"):
        tool["create_dmg"](tmp_path / "Prometheus.app")
    monkeypatch.setattr(tool["platform"], "system", lambda: "Darwin")
    with pytest.raises(ValueError, match="já compilado"):
        tool["create_dmg"](tmp_path / "Prometheus.app")
    assert calls == []


def test_builder_failure_does_not_publish_partial_artifact(app_bundle, dmg_tool, monkeypatch, tmp_path):
    tool, _ = dmg_tool

    def fail(filename, *args, **kwargs):
        Path(filename).write_bytes(b"incomplete")
        raise RuntimeError("synthetic failure")

    monkeypatch.setitem(sys.modules, "dmgbuild", SimpleNamespace(build_dmg=fail))
    output = tmp_path / "release.dmg"
    with pytest.raises(RuntimeError, match="synthetic failure"):
        tool["create_dmg"](app_bundle, output)
    assert not output.exists()
    assert not list(tmp_path.glob("prometheus-dmg-*"))


def test_retina_backgrounds_match_finder_geometry(tmp_path):
    from PySide6.QtGui import QImage

    renderer = runpy.run_path(str(MACOS / "render.py"))
    renderer["render_backgrounds"](tmp_path)
    standard = QImage(str(tmp_path / "background.png"))
    retina = QImage(str(tmp_path / "background@2x.png"))
    assert (standard.width(), standard.height()) == (640, 420)
    assert (retina.width(), retina.height()) == (1280, 840)
