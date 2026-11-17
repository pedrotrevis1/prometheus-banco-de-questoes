import sys

from PySide6.QtWidgets import QApplication

from prometheus import __version__
from prometheus.app import APP_NAME, ExamGeneratorApp
from prometheus.storage.log import initialize_logging


def main():
    initialize_logging()
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationDisplayName(APP_NAME)
    app.setApplicationVersion(__version__)
    window = ExamGeneratorApp()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
