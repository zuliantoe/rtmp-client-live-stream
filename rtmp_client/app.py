import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

from rtmp_client.ui.main_window import MainWindow


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("RTMP Client")
    app.setOrganizationName("RTMP Client")
    app.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    app.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
