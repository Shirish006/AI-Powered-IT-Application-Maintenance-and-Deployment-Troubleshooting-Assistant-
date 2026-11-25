"""Unit and workflow tests for the CLI runner module."""

from __future__ import annotations

import argparse
from pathlib import Path

import pytest

from config.settings import settings
from database.db_manager import DBManager
from services.cli_runner import build_cli_parser, format_cli_output, run_cli


def test_build_cli_parser():
    parser = build_cli_parser()
    args = parser.parse_args(["--cli", "-f", "sample.log", "--language", "Python"])
    assert args.cli is True
    assert args.file == "sample.log"
    assert args.language == "Python"
    assert args.problem_type == "Automatic Detection"


def test_format_cli_output():
    result = {
        "programming_language": "Python",
        "detected_problem_type": "Maintenance",
        "error_category": "Runtime Error",
        "severity": "High",
        "ai_provider": "demo",
        "ai_model": "offline-demo-engine",
        "error_summary": "Test Summary",
        "explanation": "Test Explanation",
        "confirmed_facts": ["Fact 1", "Fact 2"],
        "possible_causes": ["Cause A"],
        "troubleshooting_steps": ["Step 1", "Step 2"],
        "suggested_solution": "Fix it",
        "verification_steps": ["Verify 1"],
    }
    output = format_cli_output(session_id=42, result=result, redactions_count=3)
    assert "Session ID       : #42" in output
    assert "Language         : Python" in output
    assert "Runtime Error" in output
    assert "HIGH" in output
    assert "3 sensitive pattern(s) removed" in output
    assert "[+] Fact 1" in output
    assert "[?] Cause A" in output
    assert "1. Step 1" in output


def test_run_cli_with_text(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(settings, "demo_mode_forced", True)
    db_file = tmp_path / "test_cli.db"
    db = DBManager(db_file)

    args = argparse.Namespace(
        cli=True,
        file=None,
        log="docker run web-api failed with No module named 'flask'",
        language="Python",
        problem_type="Automatic Detection",
        environment="Docker",
        framework="Flask",
        export=str(tmp_path / "report.md"),
    )

    exit_code = run_cli(args, db=db)
    assert exit_code == 0

    # Verify session was persisted in SQLite
    sessions = db.recent_sessions(limit=5)
    assert len(sessions) == 1
    assert sessions[0]["programming_language"] == "Python"
    assert sessions[0]["detected_problem_type"] == "Deployment"
    assert (tmp_path / "report.md").exists()


def test_run_cli_missing_input():
    args = argparse.Namespace(
        cli=True,
        file=None,
        log=None,
        language="Python",
        problem_type="Maintenance",
        environment="Development",
        framework="",
        export=None,
    )
    exit_code = run_cli(args)
    assert exit_code == 1
