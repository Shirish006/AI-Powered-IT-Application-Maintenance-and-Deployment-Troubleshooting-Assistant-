"""Tests for C / C++ Language Support and JSON Export/Import."""

import json
import tempfile
from pathlib import Path

import pytest

from database.db_manager import DBManager
from modules.languages import get_language_profile, list_supported_languages
from services.ai_service import DemoProvider
from services.log_processor import LogProcessor


def test_cpp_language_profiles():
    """Verify C and C++ profiles are registered and accessible."""
    supported = list_supported_languages()
    assert "C" in supported
    assert "C++" in supported

    c_prof = get_language_profile("C")
    assert c_prof.display_name == "C"
    assert ".c" in c_prof.file_extensions
    assert any("valgrind" in t for t in c_prof.build_and_run_tools)

    cpp_prof = get_language_profile("C++")
    assert cpp_prof.display_name == "C++"
    assert ".cpp" in cpp_prof.file_extensions
    assert any("CMakeLists.txt" in f for f in cpp_prof.dependency_files)


def test_cpp_signal_extraction_segfault():
    """Verify Segmentation fault / SIGSEGV signal extraction in C++."""
    log = """
    Starting processing worker thread...
    Process terminated with signal SIGSEGV, Segmentation fault (core dumped).
    Backtrace:
    #0  0x00007f9c in UserService::processUser(User* user) at /src/user.cpp:42
    """
    signals = LogProcessor.extract_signals(log)
    assert "C++" in signals["language_hints"]
    assert any("SIGSEGV" in e for e in signals["exceptions"])


def test_cpp_signal_extraction_cmake():
    """Verify CMake error extraction."""
    log = """
    CMake Error at CMakeLists.txt:18 (add_executable):
      Cannot find source file:
        src/network.cpp
    """
    signals = LogProcessor.extract_signals(log)
    assert "C++" in signals["language_hints"]
    assert any("CMake Error" in e for e in signals["exceptions"])


def test_cpp_demo_provider_segfault():
    """Verify DemoProvider accurately diagnoses a C++ Segmentation fault."""
    provider = DemoProvider()
    payload = {
        "language": "C++",
        "problem_type": "Maintenance",
        "environment": "Development",
        "framework": "Qt",
        "error_log": "Segmentation fault (core dumped) in /app/main.cpp:30",
    }
    result = provider.analyze(payload)
    assert result["error_category"] == "Runtime Error"
    assert result["severity"] == "Critical"
    assert "SIGSEGV" in result["error_summary"]
    assert any("AddressSanitizer" in st for st in result["troubleshooting_steps"])


def test_session_json_export_and_import():
    """Verify exporting a session as JSON and importing it back into SQLite."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    db = DBManager(db_path)
    try:
        session_id = db.insert_session({
            "programming_language": "C++",
            "problem_type": "Deployment",
            "environment": "Docker",
            "application_framework": "CMake",
            "original_error_log": "CMake Error at CMakeLists.txt",
            "error_category": "Build Error",
            "severity": "High",
            "error_summary": "Missing source file in CMake target",
            "error_explanation": "CMake could not find the specified source file.",
            "confirmed_facts": ["CMake Error reported"],
            "possible_causes": ["File renamed or moved"],
            "troubleshooting_steps": ["Verify file path in CMakeLists.txt"],
            "suggested_solution": "Update CMakeLists.txt",
            "verification_steps": ["Run cmake -B build"],
            "resolution_status": "Unresolved",
            "is_demo": 1,
        })

        # Export to JSON
        json_str = db.export_session_json(session_id)
        assert "Missing source file" in json_str

        # Import as new session
        new_id = db.import_session_json(json_str)
        assert new_id > 0
        assert new_id != session_id

        imported = db.get_session(new_id)
        assert imported["programming_language"] == "C++"
        assert imported["error_summary"] == "Missing source file in CMake target"
    finally:
        Path(db_path).unlink(missing_ok=True)
