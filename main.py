"""Application entry point for AI IT Troubleshooting Assistant."""

from __future__ import annotations

import logging
import sys
from pathlib import Path

# Ensure project root is in sys.path
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QMessageBox

from config.settings import WINDOW_TITLE, get_resource_path, settings
from database.db_manager import DBManager
from ui.main_window import MainWindow

# Configure clean logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("AI_IT_Assistant")


def load_stylesheet(app: QApplication) -> None:
    """Load and apply QSS stylesheet from ui/styles.qss."""
    qss_path = get_resource_path("ui/styles.qss")
    if qss_path.exists():
        try:
            with open(qss_path, "r", encoding="utf-8") as f:
                app.setStyleSheet(f.read())
            logger.info("Loaded stylesheet from %s", qss_path)
        except Exception as e:
            logger.warning("Failed to load stylesheet: %s", e)
    else:
        logger.warning("Stylesheet not found at %s", qss_path)


def handle_uncaught_exception(exc_type, exc_value, exc_traceback) -> None:
    """Global exception hook to prevent silent crashes and log critical failures."""
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    logger.critical("Uncaught application exception", exc_info=(exc_type, exc_value, exc_traceback))

    # Show a friendly dialog if GUI is running
    app = QApplication.instance()
    if app:
        QMessageBox.critical(
            None,
            "Application Error",
            f"An unexpected internal error occurred:\n{exc_type.__name__}: {exc_value}\n\n"
            "Please check the log output or restart the application.",
        )


def main() -> int:
    """Main application lifecycle entry point."""
    sys.excepthook = handle_uncaught_exception

    # High DPI scaling attributes (default in Qt 6)
    app = QApplication(sys.argv)
    app.setApplicationName("AI IT Troubleshooting Assistant")
    app.setOrganizationName("AI_IT_Assistant")

    # Load custom QSS
    load_stylesheet(app)

    # Initialize Database
    try:
        db = DBManager(settings.db_path)
    except Exception as e:
        logger.exception("Failed to initialize database")
        QMessageBox.critical(
            None,
            "Database Initialization Error",
            f"Failed to access database at '{settings.db_path}':\n{e}",
        )
        return 1

    # Show Main Window
    window = MainWindow(db)
    window.show()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
