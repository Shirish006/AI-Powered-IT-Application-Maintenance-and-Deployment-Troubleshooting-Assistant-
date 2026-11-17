"""Tests for SQLite Database Manager and Schema."""

import sqlite3
import tempfile
from pathlib import Path

import pytest

from database.db_manager import DBManager


@pytest.fixture
def temp_db():
    """Create a temporary isolated SQLite database file."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        temp_path = f.name
    db = DBManager(temp_path)
    yield db
    try:
        Path(temp_path).unlink(missing_ok=True)
    except Exception:
        pass


def test_db_initialization(temp_db):
    """Verify tables and schema version are created on startup."""
    with temp_db.get_connection() as conn:
        cursor = conn.execute("SELECT version FROM schema_version;")
        row = cursor.fetchone()
        assert row is not None
        assert row["version"] == 1


def test_insert_and_get_session(temp_db):
    """Verify session insertion and retrieval with JSON fields."""
    data = {
        "programming_language": "Python",
        "problem_type": "Deployment",
        "environment": "Docker",
        "application_framework": "Flask",
        "original_error_log": "ModuleNotFoundError: No module named 'flask'",
        "error_category": "Dependency Error",
        "severity": "High",
        "error_summary": "Missing flask package in container",
        "error_explanation": "Flask is not installed in the container environment.",
        "confirmed_facts": ["ModuleNotFoundError in app.py", "Docker container env"],
        "possible_causes": ["Missing in requirements.txt", "pip install failed"],
        "troubleshooting_steps": ["Check requirements.txt", "Rebuild Docker image"],
        "suggested_solution": "Add Flask to requirements.txt",
        "verification_steps": ["Run container and curl endpoint"],
        "resolution_status": "Unresolved",
        "is_demo": 0,
    }

    session_id = temp_db.insert_session(data)
    assert session_id > 0

    session = temp_db.get_session(session_id)
    assert session is not None
    assert session["id"] == session_id
    assert session["programming_language"] == "Python"
    assert session["problem_type"] == "Deployment"
    assert session["environment"] == "Docker"
    assert session["resolution_status"] == "Unresolved"
    assert isinstance(session["confirmed_facts"], list)
    assert len(session["confirmed_facts"]) == 2
    assert isinstance(session["troubleshooting_steps"], list)
    assert len(session["troubleshooting_steps"]) == 2


def test_update_status(temp_db):
    """Verify resolution status updates and resolved_at timestamp."""
    data = {
        "programming_language": "Java",
        "problem_type": "Maintenance",
        "environment": "Development",
        "original_error_log": "NullPointerException at com.example.App.main",
        "error_category": "Runtime Error",
        "severity": "Medium",
        "error_summary": "NPE in main method",
        "error_explanation": "Attempted to dereference null pointer.",
        "confirmed_facts": [],
        "possible_causes": [],
        "troubleshooting_steps": [],
        "suggested_solution": "Add null check",
        "verification_steps": [],
        "resolution_status": "Unresolved",
    }
    session_id = temp_db.insert_session(data)

    # Set to In Progress
    assert temp_db.update_status(session_id, "In Progress") is True
    s = temp_db.get_session(session_id)
    assert s["resolution_status"] == "In Progress"
    assert s["resolved_at"] == ""

    # Set to Solved
    assert temp_db.update_status(session_id, "Solved") is True
    s = temp_db.get_session(session_id)
    assert s["resolution_status"] == "Solved"
    assert s["resolved_at"] != ""


def test_search_and_filters(temp_db):
    """Verify parameterized search and combined filtering."""
    temp_db.insert_session({
        "programming_language": "Python",
        "problem_type": "Maintenance",
        "environment": "Development",
        "original_error_log": "SyntaxError: invalid syntax",
        "error_category": "Syntax Error",
        "severity": "Low",
        "error_summary": "Typo in loop header",
        "error_explanation": "Missing colon after for loop statement.",
        "confirmed_facts": [],
        "possible_causes": [],
        "troubleshooting_steps": [],
        "suggested_solution": "Add colon",
        "verification_steps": [],
        "resolution_status": "Solved",
    })

    temp_db.insert_session({
        "programming_language": "JavaScript",
        "problem_type": "Deployment",
        "environment": "Cloud",
        "original_error_log": "Error: Cannot find module 'express'",
        "error_category": "Dependency Error",
        "severity": "High",
        "error_summary": "Missing express module",
        "error_explanation": "Express package not installed.",
        "confirmed_facts": [],
        "possible_causes": [],
        "troubleshooting_steps": [],
        "suggested_solution": "npm install express",
        "verification_steps": [],
        "resolution_status": "Unresolved",
    })

    # Search for "syntax"
    res = temp_db.list_sessions(search="syntax")
    assert len(res) == 1
    assert res[0]["programming_language"] == "Python"

    # Filter by Language
    res_js = temp_db.list_sessions(language="JavaScript")
    assert len(res_js) == 1
    assert res_js[0]["error_category"] == "Dependency Error"

    # Filter by Problem Type
    res_deploy = temp_db.list_sessions(problem_type="Deployment")
    assert len(res_deploy) == 1

    # Filter by Status
    res_solved = temp_db.list_sessions(status="Solved")
    assert len(res_solved) == 1
    assert res_solved[0]["programming_language"] == "Python"


def test_sql_injection_safety(temp_db):
    """Verify parameterized queries withstand SQL injection attempts."""
    malicious_search = "'; DROP TABLE troubleshooting_history;--"
    res = temp_db.list_sessions(search=malicious_search)
    assert len(res) == 0

    # Ensure table was not dropped
    counts = temp_db.counts_by_status()
    assert "total" in counts


def test_delete_session(temp_db):
    """Verify session deletion by ID."""
    session_id = temp_db.insert_session({
        "programming_language": "Python",
        "problem_type": "Maintenance",
        "environment": "Development",
        "original_error_log": "TypeError: unsupported operand",
        "error_category": "Runtime Error",
        "severity": "Medium",
        "error_summary": "Type mismatch",
        "error_explanation": "Added str to int",
        "confirmed_facts": [],
        "possible_causes": [],
        "troubleshooting_steps": [],
        "suggested_solution": "Cast to int",
        "verification_steps": [],
        "resolution_status": "Unresolved",
    })

    assert temp_db.delete_session(session_id) is True
    assert temp_db.get_session(session_id) is None


def test_counts_by_status(temp_db):
    """Verify status counter aggregation."""
    for status in ("Unresolved", "In Progress", "Solved", "Unresolved"):
        temp_db.insert_session({
            "programming_language": "Python",
            "problem_type": "Maintenance",
            "environment": "Development",
            "original_error_log": "err",
            "error_category": "Runtime Error",
            "severity": "Low",
            "error_summary": "test",
            "error_explanation": "test",
            "confirmed_facts": [],
            "possible_causes": [],
            "troubleshooting_steps": [],
            "suggested_solution": "test",
            "verification_steps": [],
            "resolution_status": status,
        })

    counts = temp_db.counts_by_status()
    assert counts["total"] == 4
    assert counts["unresolved"] == 2
    assert counts["in_progress"] == 1
    assert counts["solved"] == 1
