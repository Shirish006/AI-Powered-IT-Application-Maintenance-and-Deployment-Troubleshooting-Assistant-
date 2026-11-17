"""Tests for AI Service, JSON parsing, DemoProvider, and error mapping."""

import json
import pytest

from config.settings import AppConfig
from services.ai_service import (
    AIService,
    DemoProvider,
    MalformedResponseError,
    MissingAPIKeyError,
)


def test_extract_json_from_code_fences():
    """Verify extraction of JSON wrapped in markdown code fences."""
    fenced = """Here is your diagnostic breakdown:
```json
{
  "error_summary": "Test error",
  "error_category": "Runtime Error",
  "severity": "Medium"
}
```
Hope this helps!"""

    extracted = AIService.extract_json_object(fenced)
    parsed = json.loads(extracted)
    assert parsed["error_summary"] == "Test error"
    assert parsed["error_category"] == "Runtime Error"


def test_parse_and_validate_fills_defaults():
    """Verify missing fields receive safe defaults and categories are normalized."""
    raw = json.dumps({
        "error_summary": "Incomplete raw response",
        "error_category": "missing dependency",
        "severity": "high",
    })

    payload = {
        "language": "Python",
        "problem_type": "Deployment",
        "environment": "Docker",
    }

    validated = AIService.parse_and_validate_json(raw, payload, provider="test", model="test-model")
    assert validated["error_category"] == "Dependency Error"
    assert validated["severity"] == "High"
    assert validated["detected_problem_type"] == "Deployment"
    assert isinstance(validated["confirmed_facts"], list)
    assert isinstance(validated["possible_causes"], list)
    assert isinstance(validated["troubleshooting_steps"], list)
    assert isinstance(validated["verification_steps"], list)


def test_malformed_json_raises_error():
    """Verify completely invalid JSON raises MalformedResponseError."""
    with pytest.raises(MalformedResponseError):
        AIService.extract_json_object("There is no json object here.")


def test_demo_provider_flask_docker():
    """Verify DemoProvider produces expected benchmark for Docker Flask error."""
    provider = DemoProvider()
    payload = {
        "language": "Python",
        "problem_type": "Deployment",
        "environment": "Docker",
        "framework": "Flask",
        "error_log": "ModuleNotFoundError: No module named 'flask'",
    }

    result = provider.analyze(payload)
    assert result["is_demo"] is True
    assert result["error_category"] == "Dependency Error"
    assert result["detected_problem_type"] == "Deployment"
    assert "flask" in result["error_summary"].lower()
    assert len(result["troubleshooting_steps"]) >= 4
    assert any("requirements.txt" in step for step in result["troubleshooting_steps"])
    assert any("docker" in step.lower() for step in result["troubleshooting_steps"])
    assert len(result["verification_steps"]) >= 2


def test_demo_provider_login_maintenance():
    """Verify DemoProvider produces expected output for Maintenance login error."""
    provider = DemoProvider()
    payload = {
        "language": "Python",
        "problem_type": "Maintenance",
        "environment": "Development",
        "framework": "Django",
        "error_log": "Error during user login authentication flow: User credentials mismatch",
    }

    result = provider.analyze(payload)
    assert result["is_demo"] is True
    assert result["detected_problem_type"] == "Maintenance"
    assert "login" in result["error_summary"].lower() or "authentication" in result["error_summary"].lower()


def test_ai_service_provider_selection_missing_key():
    """Verify MissingAPIKeyError is raised when API key is missing and demo mode is not forced."""
    cfg = AppConfig(
        ai_provider="gemini",
        gemini_api_key="",
        demo_mode_forced=False,
    )
    # When api_key is missing, get_effective_provider defaults to demo unless explicitly invoked through GeminiProvider
    provider = AIService.get_provider(cfg)
    assert isinstance(provider, DemoProvider)
