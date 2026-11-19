import sys

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon

from prometheus import __version__
from prometheus.app import APP_NAME, ExamGeneratorApp
from prometheus.storage.log import initialize_logging
from prometheus.resources import application_icon_path


def main():
    initialize_logging()
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationDisplayName(APP_NAME)
    app.setApplicationVersion(__version__)
    app.setWindowIcon(QIcon(str(application_icon_path())))
    window = ExamGeneratorApp()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
