"""Application entry point for AI IT Troubleshooting Assistant.

Supports both the primary native PySide6 desktop GUI application and a headless
CLI diagnostic mode for fast command-line workflows inside Antigravity IDE.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

# Ensure project root is in sys.path
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from config.settings import WINDOW_TITLE, get_resource_path, settings
from database.db_manager import DBManager
from services.cli_runner import build_cli_parser, run_cli

# Configure clean logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("AI_IT_Assistant")


def load_stylesheet(app) -> None:
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
    try:
        from PySide6.QtWidgets import QApplication, QMessageBox
        app = QApplication.instance()
        if app:
            QMessageBox.critical(
                None,
                "Application Error",
                f"An unexpected internal error occurred:\n{exc_type.__name__}: {exc_value}\n\n"
                "Please check the log output or restart the application.",
            )
    except ImportError:
        pass


def run_gui() -> int:
    """Initialize and run the native PySide6 desktop GUI application."""
    from PySide6.QtWidgets import QApplication, QMessageBox
    from ui.main_window import MainWindow

    sys.excepthook = handle_uncaught_exception

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


def main() -> int:
    """Main application lifecycle entry point supporting GUI and CLI modes."""
    # Check if CLI mode was explicitly requested
    if any(arg in sys.argv for arg in ("--cli", "-f", "--file", "-l", "--log")):
        parser = build_cli_parser()
        args = parser.parse_args()
        return run_cli(args)

    # Default: launch native PySide6 desktop GUI
    return run_gui()


if __name__ == "__main__":
    sys.exit(main())
