"""Automated GUI component tests using PySide6 offscreen mode."""

import os
import sys
import tempfile
from pathlib import Path

# Configure Qt offscreen platform before creating QApplication
os.environ["QT_QPA_PLATFORM"] = "offscreen"

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from database.db_manager import DBManager
from ui.main_window import MainWindow


@pytest.fixture(scope="session")
def qapp():
    """Ensure a single persistent QApplication instance exists."""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    return app


@pytest.fixture
def test_window(qapp):
    """Instantiate a test MainWindow with an isolated temporary database."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    db = DBManager(db_path)
    window = MainWindow(db)
    yield window

    window.close()
    try:
        Path(db_path).unlink(missing_ok=True)
    except Exception:
        pass


def test_main_window_structure(test_window):
    """Verify window title, minimum dimensions, and screen instances."""
    assert "AI IT Troubleshooting Assistant" in test_window.windowTitle()
    assert test_window.minimumWidth() >= 1100
    assert test_window.minimumHeight() >= 700
    assert test_window.stacked_widget.count() == 4


def test_navigation_between_screens(test_window):
    """Verify navigation switches the stacked widget index."""
    # Screen 0 (Dashboard)
    test_window.switch_screen(0)
    assert test_window.stacked_widget.currentIndex() == 0

    # Screen 1 (New Troubleshooting)
    test_window.switch_screen(1)
    assert test_window.stacked_widget.currentIndex() == 1

    # Screen 3 (History)
    test_window.switch_screen(3)
    assert test_window.stacked_widget.currentIndex() == 3


def test_dashboard_preselection_signals(test_window):
    """Verify dashboard action signals properly preselect Problem Type in Screen 2."""
    # Preselect Maintenance
    test_window.screen_dashboard.navigate_to_new_issue.emit("Maintenance")
    assert test_window.stacked_widget.currentIndex() == 1
    assert test_window.screen_new_troubleshooting.combo_problem_type.currentText() == "Maintenance"

    # Preselect Deployment
    test_window.screen_dashboard.navigate_to_new_issue.emit("Deployment")
    assert test_window.stacked_widget.currentIndex() == 1
    assert test_window.screen_new_troubleshooting.combo_problem_type.currentText() == "Deployment"


def test_analysis_screen_session_loading(test_window):
    """Verify that an analyzed session loads correctly across all cards in Screen 3."""
    session_id = test_window.db.insert_session({
        "programming_language": "Python",
        "problem_type": "Deployment",
        "environment": "Docker",
        "application_framework": "Flask",
        "original_error_log": "ModuleNotFoundError: No module named 'flask'",
        "error_category": "Dependency Error",
        "severity": "High",
        "error_summary": "Missing Flask package in Docker container",
        "error_explanation": "Flask is required by app.py but missing.",
        "confirmed_facts": ["Docker environment", "No module named 'flask'"],
        "possible_causes": ["Missing in requirements.txt"],
        "troubleshooting_steps": ["Check requirements.txt", "Rebuild Docker image"],
        "suggested_solution": "pip install flask",
        "verification_steps": ["Run container"],
        "resolution_status": "Unresolved",
        "is_demo": 1,
    })

    test_window.screen_analysis.load_session(session_id)
    assert test_window.screen_analysis.badge_lang.text().strip() == "Python"
    assert "Dependency Error" in test_window.screen_analysis.badge_category.text()
    assert not test_window.screen_analysis.demo_banner.isHidden()
    assert "Missing Flask" in test_window.screen_analysis.summary_label.text()
