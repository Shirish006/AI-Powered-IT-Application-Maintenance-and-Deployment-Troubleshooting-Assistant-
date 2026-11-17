"""Tests for ErrorClassifier: category and severity normalization and heuristics."""

import pytest

from services.error_classifier import CANONICAL_CATEGORIES, CANONICAL_SEVERITIES, ErrorClassifier


def test_category_normalization_exact():
    """Verify all 10 canonical categories pass exact normalization."""
    for cat in CANONICAL_CATEGORIES:
        norm, was_norm = ErrorClassifier.normalize_category(cat)
        assert norm == cat
        assert was_norm is False


def test_category_normalization_case_and_synonyms():
    """Verify case insensitivity and common synonym mappings."""
    # Case insensitivity
    assert ErrorClassifier.normalize_category("syntax error")[0] == "Syntax Error"
    assert ErrorClassifier.normalize_category("RUNTIME ERROR")[0] == "Runtime Error"

    # Synonyms
    assert ErrorClassifier.normalize_category("missing dependency")[0] == "Dependency Error"
    assert ErrorClassifier.normalize_category("compilation error")[0] == "Build Error"
    assert ErrorClassifier.normalize_category("sql error")[0] == "Database Error"
    assert ErrorClassifier.normalize_category("connection refused")[0] == "Network Error"
    assert ErrorClassifier.normalize_category("access denied")[0] == "Permission Error"


def test_severity_normalization():
    """Verify canonical severity mapping and synonyms."""
    for sev in CANONICAL_SEVERITIES:
        assert ErrorClassifier.normalize_severity(sev) == sev

    assert ErrorClassifier.normalize_severity("fatal") == "Critical"
    assert ErrorClassifier.normalize_severity("severe") == "High"
    assert ErrorClassifier.normalize_severity("minor") == "Low"
    assert ErrorClassifier.normalize_severity("moderate") == "Medium"
    assert ErrorClassifier.normalize_severity(None, {"environment": "Production"}) == "High"


def test_problem_type_normalization():
    """Verify problem type normalization to Maintenance or Deployment."""
    assert ErrorClassifier.normalize_problem_type("Maintenance") == "Maintenance"
    assert ErrorClassifier.normalize_problem_type("Deployment") == "Deployment"
    assert ErrorClassifier.normalize_problem_type("docker container") == "Deployment"
    assert ErrorClassifier.normalize_problem_type("code bug") == "Maintenance"


def test_fallback_classification_heuristics():
    """Verify context-aware fallback classification when AI category is missing."""
    # Syntax error fallback
    res = ErrorClassifier.fallback_classify({
        "error_log": "SyntaxError: unexpected EOF while parsing",
        "signals": {"exceptions": ["SyntaxError: unexpected EOF"]},
    })
    assert res == "Syntax Error"

    # Dependency error fallback
    res_dep = ErrorClassifier.fallback_classify({
        "error_log": "ModuleNotFoundError: No module named 'flask'",
        "signals": {"exceptions": ["ModuleNotFoundError: No module named 'flask'"]},
    })
    assert res_dep == "Dependency Error"

    # Database error fallback
    res_db = ErrorClassifier.fallback_classify({
        "error_log": "sqlite3.OperationalError: no such table: users",
        "signals": {"exceptions": []},
    })
    assert res_db == "Database Error"

    # Docker deployment fallback
    res_deploy = ErrorClassifier.fallback_classify({
        "problem_type": "Deployment",
        "environment": "Docker",
        "error_log": "Container failed to start on port 8080",
        "signals": {},
    })
    assert res_deploy in ("Deployment Error", "Configuration Error")
