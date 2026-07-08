import sys

from PySide6.QtWidgets import QApplication

from backend.database.init_database import init_database
from backend.i18n import init_i18n


def main() -> None:
    init_database()

    app = QApplication(sys.argv)
    init_i18n(app)

    from frontend.views.home_view import HomeView

    window = HomeView()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
