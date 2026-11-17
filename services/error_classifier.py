"""Error classification and category/severity normalization."""

from __future__ import annotations

import re
from typing import Any, Tuple

CANONICAL_CATEGORIES = [
    "Syntax Error",
    "Runtime Error",
    "Logical Error",
    "Dependency Error",
    "Configuration Error",
    "Database Error",
    "Network Error",
    "Permission Error",
    "Build Error",
    "Deployment Error",
]

CANONICAL_SEVERITIES = ["Low", "Medium", "High", "Critical"]
CANONICAL_PROBLEM_TYPES = ["Maintenance", "Deployment"]

# Mapping of common aliases and synonyms to canonical categories
CATEGORY_SYNONYMS: dict[str, str] = {
    "syntax": "Syntax Error",
    "syntaxerror": "Syntax Error",
    "parsing error": "Syntax Error",
    "parse error": "Syntax Error",
    "indentation error": "Syntax Error",
    "compilation error": "Build Error",
    "compile error": "Build Error",
    "build failure": "Build Error",
    "build error": "Build Error",
    "linker error": "Build Error",
    "runtime": "Runtime Error",
    "runtime error": "Runtime Error",
    "runtime exception": "Runtime Error",
    "exception": "Runtime Error",
    "nullpointer": "Runtime Error",
    "logic": "Logical Error",
    "logical": "Logical Error",
    "logical error": "Logical Error",
    "assertion error": "Logical Error",
    "dependency": "Dependency Error",
    "dependency error": "Dependency Error",
    "dependencies": "Dependency Error",
    "missing package": "Dependency Error",
    "missing module": "Dependency Error",
    "package error": "Dependency Error",
    "import error": "Dependency Error",
    "configuration": "Configuration Error",
    "configuration error": "Configuration Error",
    "config error": "Configuration Error",
    "misconfiguration": "Configuration Error",
    "env var": "Configuration Error",
    "environment variable": "Configuration Error",
    "database": "Database Error",
    "database error": "Database Error",
    "sql error": "Database Error",
    "db error": "Database Error",
    "query error": "Database Error",
    "network": "Network Error",
    "network error": "Network Error",
    "connection error": "Network Error",
    "connection refused": "Network Error",
    "timeout": "Network Error",
    "dns error": "Network Error",
    "socket error": "Network Error",
    "permission": "Permission Error",
    "permission error": "Permission Error",
    "permissions": "Permission Error",
    "access denied": "Permission Error",
    "authorization error": "Permission Error",
    "deployment": "Deployment Error",
    "deployment error": "Deployment Error",
    "container error": "Deployment Error",
    "docker error": "Deployment Error",
    "startup failure": "Deployment Error",
}


class ErrorClassifier:
    """Validates, normalizes, and provides context-aware heuristic classification."""

    @classmethod
    def normalize_category(
        cls,
        raw_category: str | None,
        context: dict[str, Any] | None = None,
    ) -> Tuple[str, bool]:
        """Normalize raw category to canonical name. Returns (canonical_name, was_normalized)."""
        if not raw_category:
            return cls.fallback_classify(context or {}), True

        cleaned = raw_category.strip().lower()

        # Check exact canonical names case-insensitively
        for canonical in CANONICAL_CATEGORIES:
            if cleaned == canonical.lower():
                return canonical, (raw_category.strip() != canonical)

        # Check synonym map
        if cleaned in CATEGORY_SYNONYMS:
            return CATEGORY_SYNONYMS[cleaned], True

        # Check partial substring match
        for key, canonical in CATEGORY_SYNONYMS.items():
            if key in cleaned:
                return canonical, True

        # Fallback context heuristic
        return cls.fallback_classify(context or {}), True

    @classmethod
    def normalize_severity(cls, raw_severity: str | None, context: dict[str, Any] | None = None) -> str:
        """Normalize severity to Low, Medium, High, or Critical."""
        if not raw_severity:
            # Infer from environment if available
            env = (context or {}).get("environment", "").lower()
            if "production" in env:
                return "High"
            return "Medium"

        cleaned = raw_severity.strip().lower()
        if "crit" in cleaned or "fatal" in cleaned or "emergency" in cleaned:
            return "Critical"
        if "high" in cleaned or "severe" in cleaned or "major" in cleaned:
            return "High"
        if "med" in cleaned or "moderate" in cleaned or "normal" in cleaned:
            return "Medium"
        if "low" in cleaned or "minor" in cleaned or "info" in cleaned or "warn" in cleaned:
            return "Low"

        return "Medium"

    @classmethod
    def normalize_problem_type(cls, raw_type: str | None, default: str = "Maintenance") -> str:
        """Normalize problem type to Maintenance or Deployment."""
        if not raw_type:
            return default
        cleaned = raw_type.strip().lower()
        if "deploy" in cleaned or "release" in cleaned or "infra" in cleaned or "docker" in cleaned or "cloud" in cleaned:
            return "Deployment"
        if "maint" in cleaned or "code" in cleaned or "bug" in cleaned or "feature" in cleaned or "app" in cleaned:
            return "Maintenance"
        return default

    @classmethod
    def fallback_classify(cls, context: dict[str, Any]) -> str:
        """Context-aware multi-signal heuristic fallback if AI classification is missing/ambiguous.

        Combines problem type, environment, extracted signals, and error content.
        """
        problem_type = context.get("problem_type", "")
        environment = (context.get("environment") or "").lower()
        log_text = (context.get("error_log") or "").lower()
        signals = context.get("signals") or {}
        exceptions = [e.lower() for e in signals.get("exceptions", [])]

        # 1. Syntax Errors
        if any("syntaxerror" in e or "indentationerror" in e for e in exceptions) or "syntaxerror" in log_text:
            return "Syntax Error"

        # 2. Dependency Errors
        if (
            any("modulenotfounderror" in e or "importerror" in e or "classnotfoundexception" in e for e in exceptions)
            or "no module named" in log_text
            or "cannot find module" in log_text
            or "package not found" in log_text
            or "pip install" in log_text
        ):
            return "Dependency Error"

        # 3. Database Errors
        if (
            any("sql" in e or "database" in e or "integrityerror" in e for e in exceptions)
            or "database connection" in log_text
            or "relation does not exist" in log_text
            or "psycopg" in log_text
            or "sqlalchemy" in log_text
            or "sqlite3.operationalerror" in log_text
        ):
            return "Database Error"

        # 4. Network Errors
        if (
            any("connectionerror" in e or "socket" in e or "econnrefused" in e for e in exceptions)
            or "econnrefused" in log_text
            or "connection refused" in log_text
            or "failed to resolve" in log_text
            or "timed out" in log_text
        ):
            return "Network Error"

        # 5. Permission Errors
        if (
            any("permissionerror" in e or "accessdenied" in e for e in exceptions)
            or "permission denied" in log_text
            or "eperm" in log_text
            or "403 forbidden" in log_text
        ):
            return "Permission Error"

        # 6. Build Errors
        if (
            "compilation failed" in log_text
            or "build failed" in log_text
            or "javac" in log_text
            or "mvn compile" in log_text
            or "docker build" in log_text
        ):
            return "Build Error"

        # 7. Deployment / Configuration Errors
        if (
            "docker" in environment
            or "cloud" in environment
            or "deployment" in environment
            or "eaddrinuse" in log_text
            or "port already in use" in log_text
        ):
            if "port" in log_text or "bind" in log_text or "docker" in log_text:
                return "Deployment Error"
            return "Configuration Error"

        # 8. Ambiguous fallback based on Problem Type
        if problem_type == "Deployment":
            return "Deployment Error"
        return "Runtime Error"
