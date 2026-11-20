"""Package an existing, verified-identity app; never compile the application."""
import argparse
import os
from pathlib import Path
import platform
import plistlib
import runpy
import subprocess
import tempfile

LAYOUT = runpy.run_path(str(Path(__file__).with_name("layout.py")))
render_backgrounds = runpy.run_path(str(Path(__file__).with_name("render.py")))["render_backgrounds"]


def validate_bundle(application):
    application = Path(application).resolve()
    if application.name != LAYOUT["BUNDLE_NAME"] or not application.is_dir():
        raise ValueError("Selecione um bundle Prometheus.app já compilado.")
    with (application / "Contents" / "Info.plist").open("rb") as stream:
        metadata = plistlib.load(stream)
    expected = {
        "CFBundleName": LAYOUT["APP_NAME"],
        "CFBundleDisplayName": LAYOUT["APP_NAME"],
        "CFBundleExecutable": LAYOUT["APP_NAME"],
        "CFBundleIdentifier": LAYOUT["BUNDLE_ID"],
        "CFBundleShortVersionString": LAYOUT["VERSION"],
        "CFBundleVersion": LAYOUT["VERSION"],
        "LSMinimumSystemVersion": LAYOUT["MINIMUM_MACOS"],
    }
    for key, value in expected.items():
        if metadata.get(key) != value:
            raise ValueError(f"Metadados incompatíveis: {key} deve ser {value!r}.")
    executable = application / "Contents" / "MacOS" / metadata["CFBundleExecutable"]
    if not executable.is_file() or not os.access(executable, os.X_OK):
        raise ValueError("O executável do Prometheus está ausente ou sem permissão de execução.")
    icon = metadata.get("CFBundleIconFile", "")
    if not isinstance(icon, str) or not icon or Path(icon).name != icon:
        raise ValueError("O ícone do bundle não está configurado corretamente.")
    if not Path(icon).suffix:
        icon += ".icns"
    if not (application / "Contents" / "Resources" / icon).is_file():
        raise ValueError("O ícone do bundle não foi encontrado.")
    return application, executable


def executable_architecture(executable):
    result = subprocess.run(["/usr/bin/lipo", "-archs", str(executable)],
                            check=True, capture_output=True, text=True)
    architectures = frozenset(result.stdout.split())
    names = {frozenset({"arm64"}): "arm64", frozenset({"x86_64"}): "x86_64",
             frozenset({"arm64", "x86_64"}): "universal2"}
    if architectures not in names:
        raise ValueError(f"Arquitetura não reconhecida no executável: {result.stdout.strip()}")
    return names[architectures]


def create_dmg(application, output=None):
    if platform.system() != "Darwin":
        raise ValueError("A imagem de disco para macOS deve ser criada em um Mac.")
    application, executable = validate_bundle(application)
    architecture = executable_architecture(executable)
    default_name = f"Prometheus-{LAYOUT['VERSION']}-mac-{architecture}.dmg"
    output = Path(output or LAYOUT["ROOT"] / "dist" / default_name).absolute()
    if output.suffix.lower() != ".dmg":
        raise ValueError("O arquivo de saída deve ter a extensão .dmg.")
    if output.resolve().is_relative_to(application):
        raise ValueError("Salve a imagem de disco fora do bundle do aplicativo.")
    if output.exists() or output.is_symlink():
        raise FileExistsError(f"O arquivo já existe e não será substituído: {output}")
    try:
        from dmgbuild import build_dmg
    except ImportError as error:
        raise RuntimeError("Instale requirements-dev.txt no ambiente de build para criar o DMG.") from error

    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="prometheus-dmg-", dir=output.parent) as temporary:
        background = render_backgrounds(Path(temporary) / "presentation")
        staged = Path(temporary) / output.name
        settings = LAYOUT["dmg_settings"](application, background)
        try:
            build_dmg(str(staged), LAYOUT["APP_NAME"], settings=settings)
        except Exception as error:
            raise RuntimeError(f"Não foi possível criar a imagem de disco: {error}") from error
        # Same filesystem: publish atomically without replacing an existing file.
        os.link(staged, output)
    return output


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Cria o DMG a partir de um Prometheus.app existente; não compila o app.")
    parser.add_argument("--app", type=Path, default=LAYOUT["ROOT"] / "dist" / LAYOUT["BUNDLE_NAME"],
                        help="Bundle Prometheus.app já compilado.")
    parser.add_argument("--output", type=Path, help="Destino .dmg; um arquivo existente não será substituído.")
    arguments = parser.parse_args()
    try:
        artifact = create_dmg(arguments.app, arguments.output)
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
        parser.exit(1, f"Erro: {error}\n")
    print(f"Imagem de disco criada em {artifact}")
