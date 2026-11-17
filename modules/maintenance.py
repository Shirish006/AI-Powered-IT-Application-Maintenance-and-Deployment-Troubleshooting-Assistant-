"""Application Maintenance module.

Focuses on issues arising within an existing, developed application code base
during development, refactoring, or regular operation.
"""

from __future__ import annotations

from typing import Any, List

MAINTENANCE_ISSUE_TYPES = [
    "Syntax Errors (code parsing, indentation, invalid tokens)",
    "Runtime Exceptions (NullPointer, TypeError, NameError, unhandled cases)",
    "Logical Bugs (incorrect state transitions, calculation flaws, bad conditional branches)",
    "Application Database Operations (bad SQL syntax, ORM mapping failures, constraint violations)",
    "Application Network / HTTP Client Requests (failed API calls, timeout handling, payload parsing)",
    "Application-level Configuration Errors (missing local config keys, parsing yaml/json)",
    "Local File System / Permissions (file lock, missing directory, read-only paths)",
    "Local Dependency & Packaging Quirks (version mismatch between packages)",
]


def get_maintenance_prompt_enrichment() -> str:
    """Provide domain guidance for application maintenance troubleshooting."""
    types_list = "\n".join(f"- {t}" for t in MAINTENANCE_ISSUE_TYPES)
    return (
        "PROBLEM DOMAIN: APPLICATION MAINTENANCE\n"
        "This issue relates to internal application code logic, runtime execution, data manipulation, "
        "or existing functional behavior.\n\n"
        "Key aspects to investigate:\n"
        f"{types_list}\n\n"
        "Investigation Strategy:\n"
        "1. Identify the exact line of code, stack trace frame, and exception causing the failure.\n"
        "2. Explain the root cause in terms of application code flow and data state.\n"
        "3. Provide non-destructive troubleshooting steps (e.g., logging, unit tests, reproducible test cases).\n"
        "4. Suggest clean code adjustments or configuration fixes with code snippets."
    )


def validate_maintenance_response(data: dict[str, Any]) -> tuple[bool, str]:
    """Validate that the AI response structure matches Maintenance expectations."""
    if not isinstance(data, dict):
        return False, "Response is not a dictionary."
    explanation = data.get("explanation", "")
    if len(explanation.strip()) < 10:
        return False, "Explanation is too brief for an application maintenance issue."
    return True, "Valid maintenance response."
