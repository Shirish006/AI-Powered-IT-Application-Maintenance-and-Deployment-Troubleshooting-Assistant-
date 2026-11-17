"""Integration and end-to-end workflow tests for AI troubleshooting analysis."""

import tempfile
from pathlib import Path

import pytest
from PySide6.QtCore import QCoreApplication

from config.settings import AppConfig
from database.db_manager import DBManager
from services.ai_service import AIService
from services.log_processor import LogProcessor
from services.workers import AnalysisWorker


@pytest.fixture
def workflow_env():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    db = DBManager(db_path)
    cfg = AppConfig(
        ai_provider="demo",
        demo_mode_forced=True,
        db_path=Path(db_path),
    )
    yield db, cfg

    try:
        Path(db_path).unlink(missing_ok=True)
    except Exception:
        pass


def test_docker_flask_end_to_end_analysis(workflow_env):
    """Test the complete Docker ModuleNotFoundError flask benchmark workflow."""
    db, cfg = workflow_env

    # 1. Input error text with dummy credentials to test simultaneous redaction
    raw_error = """
    docker-compose up
    Starting app_web_1 ... done
    Attaching to app_web_1
    web_1  | Traceback (most recent call last):
    web_1  |   File "/app/server.py", line 3, in <module>
    web_1  |     import flask
    web_1  | ModuleNotFoundError: No module named 'flask'
    web_1  | Database config: postgresql://admin:secret_pass_999@db:5432/appdb
    web_1  | API Token: sk-abc1234567890abcdefghijklmnopqrstuv
    """

    # 2. Process log
    processed = LogProcessor.process(raw_error)
    assert "secret_pass_999" not in processed.redaction_result.cleaned_text
    assert "sk-" not in processed.redaction_result.cleaned_text
    assert processed.redaction_result.redaction_count >= 2

    # 3. Analyze problem using AI service
    payload = {
        "language": "Python",
        "problem_type": "Deployment",
        "environment": "Docker",
        "framework": "Flask",
        "error_log": processed.redaction_result.cleaned_text,
        "signals": processed.signals,
    }

    result = AIService.execute_analysis(payload, cfg)

    # 4. Verify all 10 required structured sections exist
    assert result["error_summary"] != ""
    assert result["error_category"] == "Dependency Error"
    assert result["severity"] in ("Low", "Medium", "High", "Critical")
    assert result["detected_problem_type"] == "Deployment"
    assert len(result["explanation"]) > 20
    assert len(result["confirmed_facts"]) >= 1
    assert len(result["possible_causes"]) >= 1
    assert len(result["troubleshooting_steps"]) >= 3
    assert result["suggested_solution"] != ""
    assert len(result["verification_steps"]) >= 1

    # 5. Persist to SQLite with initial status Unresolved
    session_data = {
        "programming_language": "Python",
        "problem_type": "Deployment",
        "environment": "Docker",
        "application_framework": "Flask",
        "original_error_log": processed.redaction_result.cleaned_text,
        "error_category": result["error_category"],
        "severity": result["severity"],
        "error_summary": result["error_summary"],
        "error_explanation": result["explanation"],
        "confirmed_facts": result["confirmed_facts"],
        "possible_causes": result["possible_causes"],
        "troubleshooting_steps": result["troubleshooting_steps"],
        "suggested_solution": result["suggested_solution"],
        "verification_steps": result["verification_steps"],
        "resolution_status": "Unresolved",
        "is_demo": 1 if result["is_demo"] else 0,
        "ai_provider": result["ai_provider"],
        "ai_model": result["ai_model"],
        "detected_problem_type": result["detected_problem_type"],
    }
    session_id = db.insert_session(session_data)
    assert session_id > 0

    # 6. Verify retrieved from DB
    saved = db.get_session(session_id)
    assert saved["resolution_status"] == "Unresolved"
    assert saved["is_demo"] == 1
    assert "flask" in saved["error_summary"].lower()

    # 7. Update status to Solved
    assert db.update_status(session_id, "Solved") is True
    assert db.get_session(session_id)["resolution_status"] == "Solved"


def test_maintenance_login_workflow(workflow_env):
    """Test the Application Maintenance login error workflow."""
    db, cfg = workflow_env

    raw_error = """
    [2026-11-17 10:14:02,115] ERROR in app: Exception on /api/login [POST]
    Traceback (most recent call last):
      File "/app/auth.py", line 54, in login
        if not verify_password(password, user.password_hash):
    AttributeError: 'NoneType' object has no attribute 'password_hash'
    """

    processed = LogProcessor.process(raw_error)
    payload = {
        "language": "Python",
        "problem_type": "Maintenance",
        "environment": "Development",
        "framework": "Flask",
        "error_log": processed.redaction_result.cleaned_text,
        "signals": processed.signals,
    }

    result = AIService.execute_analysis(payload, cfg)
    assert result["error_category"] in ("Runtime Error", "Logical Error")
    assert result["detected_problem_type"] == "Maintenance"
    assert len(result["troubleshooting_steps"]) >= 2

    # Save and verify
    session_id = db.insert_session({
        "programming_language": "Python",
        "problem_type": "Maintenance",
        "environment": "Development",
        "application_framework": "Flask",
        "original_error_log": processed.redaction_result.cleaned_text,
        "error_category": result["error_category"],
        "severity": result["severity"],
        "error_summary": result["error_summary"],
        "error_explanation": result["explanation"],
        "confirmed_facts": result["confirmed_facts"],
        "possible_causes": result["possible_causes"],
        "troubleshooting_steps": result["troubleshooting_steps"],
        "suggested_solution": result["suggested_solution"],
        "verification_steps": result["verification_steps"],
        "resolution_status": "In Progress",
        "is_demo": 1,
    })

    saved = db.get_session(session_id)
    assert saved["resolution_status"] == "In Progress"
