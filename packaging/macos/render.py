"""Render DMG presentation assets and a mockup, without building an app/image."""
import argparse
import os
from pathlib import Path
import runpy

LAYOUT = runpy.run_path(str(Path(__file__).with_name("layout.py")))
_application = None


def gui_application():
    global _application
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtGui import QGuiApplication
    _application = QGuiApplication.instance() or QGuiApplication([])
    return _application


def background_image(scale=1):
    gui_application()
    from PySide6.QtCore import QRectF
    from PySide6.QtGui import QImage, QPainter
    from PySide6.QtSvg import QSvgRenderer

    width, height = LAYOUT["WINDOW_SIZE"]
    renderer = QSvgRenderer(str(Path(__file__).with_name("background.svg")))
    if not renderer.isValid():
        raise ValueError("Não foi possível carregar o fundo da imagem de disco.")
    image = QImage(width * scale, height * scale, QImage.Format_ARGB32)
    image.fill(0)
    painter = QPainter(image)
    renderer.render(painter, QRectF(0, 0, image.width(), image.height()))
    painter.end()
    return image


def save_png(image, path):
    if not image.save(str(path), "PNG"):
        raise OSError(f"Não foi possível salvar a imagem: {path}")


def render_backgrounds(directory):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    for scale, name in [(1, "background.png"), (2, "background@2x.png")]:
        save_png(background_image(scale), directory / name)
    return directory / "background.png"


def render_preview(output, app_icon=None):
    """Approximate Finder chrome; native Finder still requires acceptance."""
    gui_application()
    from PySide6.QtCore import QRectF, Qt
    from PySide6.QtGui import QColor, QFont, QIcon, QImage, QPainter

    width, height = LAYOUT["WINDOW_SIZE"]
    title_height = 44
    image = QImage(width * 2, (height + title_height) * 2, QImage.Format_ARGB32)
    image.fill(QColor("#f1f1f3"))
    painter = QPainter(image)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.scale(2, 2)
    painter.drawImage(QRectF(0, title_height, width, height), background_image(2))
    painter.setPen(QColor("#dedee2"))
    painter.drawLine(0, title_height - 1, width, title_height - 1)
    painter.setPen(Qt.NoPen)
    for x, color in [(22, "#ff5f57"), (42, "#febc2e"), (62, "#28c840")]:
        painter.setBrush(QColor(color))
        painter.drawEllipse(QRectF(x - 6, 16, 12, 12))
    font = QFont(".AppleSystemUIFont")
    font.setPixelSize(13)
    font.setWeight(QFont.DemiBold)
    painter.setFont(font)
    painter.setPen(QColor("#444448"))
    painter.drawText(QRectF(100, 0, width - 200, title_height), Qt.AlignCenter, "Prometheus")

    system_icon = Path("/System/Library/CoreServices/CoreTypes.bundle/Contents/Resources/ApplicationsFolderIcon.icns")
    icons = [(LAYOUT["BUNDLE_NAME"], app_icon or LAYOUT["APP_ICON"], "Prometheus"),
             ("Aplicativos", system_icon, "Aplicativos")]
    size = LAYOUT["ICON_SIZE"]
    font.setWeight(QFont.Normal)
    painter.setFont(font)
    for name, path, label in icons:
        x, y = LAYOUT["ICON_LOCATIONS"][name]
        pixmap = QIcon(str(path)).pixmap(size * 2, size * 2)
        if pixmap.isNull():
            painter.end()
            raise ValueError(f"Não foi possível carregar o ícone da prévia: {path}")
        painter.drawPixmap(QRectF(x - size / 2, title_height + y - size / 2, size, size), pixmap, QRectF(pixmap.rect()))
        painter.setPen(QColor("#262629"))
        painter.drawText(QRectF(x - 90, title_height + y + size / 2 + 8, 180, 25), Qt.AlignCenter, label)
    painter.end()
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    save_png(image, output)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Gera somente a prévia visual; não compila o app nem cria um DMG.")
    parser.add_argument("--preview", type=Path, required=True, help="Arquivo PNG da prévia.")
    parser.add_argument("--app-icon", type=Path, help="Ícone alternativo somente para a prévia.")
    arguments = parser.parse_args()
    render_preview(arguments.preview, arguments.app_icon)
    print(f"Prévia salva em {arguments.preview}")
