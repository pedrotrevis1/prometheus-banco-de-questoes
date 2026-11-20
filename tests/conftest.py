"""Capture macOS build configuration without importing or running PyInstaller."""
from pathlib import Path
import runpy
from types import SimpleNamespace

import pytest


@pytest.fixture
def macos_spec_calls():
    calls = {}

    def capture(name):
        def target(*args, **kwargs):
            calls[name] = (args, kwargs)
            return SimpleNamespace(pure=[], scripts=args[0] if name == "Analysis" else [],
                                   binaries=kwargs.get("binaries", []), datas=kwargs.get("datas", []))
        return target

    directory = Path(__file__).resolve().parents[1] / "packaging" / "macos"
    runpy.run_path(str(directory / "Prometheus.spec"), init_globals={
        "SPECPATH": str(directory),
        **{name: capture(name) for name in ("Analysis", "PYZ", "EXE", "BUNDLE")},
    })
    return calls
