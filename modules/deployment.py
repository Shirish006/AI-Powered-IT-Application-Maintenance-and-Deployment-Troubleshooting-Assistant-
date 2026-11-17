"""Application Deployment module.

Focuses on issues arising while preparing, packaging, containerizing, moving,
or hosting an application across environments (Testing, Staging, Production, Cloud, Docker).
"""

from __future__ import annotations

from typing import Any, List

DEPLOYMENT_ISSUE_TYPES = [
    "Missing Environment Dependencies (packages not installed in container/host, missing runtime libraries)",
    "Build & Packaging Failures (Docker build errors, PyInstaller missing imports, Maven/Gradle build exit codes)",
    "Environment Variables & Secrets Misconfiguration (missing DB URL, incorrect host/port, unexpanded variables)",
    "Port & Networking Conflicts (EADDRINUSE, port already bound, firewall blocking incoming/outgoing traffic)",
    "Server & Daemon Startup Failures (Gunicorn/Uvicorn exit, systemd service crashes, Nginx proxy errors)",
    "Infrastructure / DB Connectivity (host unreachable, SSL handshake failure, DNS resolution failure in container)",
    "Permission & User Boundary Errors (container root vs non-root, file permission denied in /var/log or /tmp)",
    "Containerization & Orchestration Quirks (Docker entrypoint syntax, multi-stage build artifacts missing, healthcheck failure)",
]


def get_deployment_prompt_enrichment() -> str:
    """Provide domain guidance for deployment and environment troubleshooting."""
    types_list = "\n".join(f"- {t}" for t in DEPLOYMENT_ISSUE_TYPES)
    return (
        "PROBLEM DOMAIN: APPLICATION DEPLOYMENT & ENVIRONMENT SETUP\n"
        "This issue relates to building, provisioning, containerizing, configuring, or running the application "
        "in its target execution environment (e.g. Docker, Cloud, VM, Production Server).\n\n"
        "Key aspects to investigate:\n"
        f"{types_list}\n\n"
        "Investigation Strategy:\n"
        "1. Examine whether the failure is an environment difference (e.g., works locally but fails in Docker/server).\n"
        "2. Check dependency installation manifests (requirements.txt, package.json, pom.xml) and build steps.\n"
        "3. Review environment variables, port bindings, volume mounts, and network connectivity.\n"
        "4. Provide exact shell commands to inspect container/server state, logs, and configuration files.\n"
        "5. Never suggest destructive production actions without an explicit backup warning."
    )


def validate_deployment_response(data: dict[str, Any]) -> tuple[bool, str]:
    """Validate that the AI response structure matches Deployment expectations."""
    if not isinstance(data, dict):
        return False, "Response is not a dictionary."
    explanation = data.get("explanation", "")
    if len(explanation.strip()) < 10:
        return False, "Explanation is too brief for an application deployment issue."
    return True, "Valid deployment response."
