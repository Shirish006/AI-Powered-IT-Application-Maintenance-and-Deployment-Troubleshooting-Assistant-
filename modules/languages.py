"""Extensible programming language profiles and troubleshooting guidance."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class LanguageProfile:
    """Represents a language's structural error patterns, dependency managers, and troubleshooting guidance."""

    name: str
    display_name: str
    file_extensions: List[str]
    common_exceptions: List[str]
    dependency_files: List[str]
    common_frameworks: List[str]
    build_and_run_tools: List[str]
    troubleshooting_guidance: List[str]
    extra_metadata: Dict[str, str] = field(default_factory=dict)


# Built-in Profiles
PYTHON_PROFILE = LanguageProfile(
    name="Python",
    display_name="Python",
    file_extensions=[".py", ".pyw", ".ipynb"],
    common_exceptions=[
        "SyntaxError",
        "IndentationError",
        "NameError",
        "TypeError",
        "ValueError",
        "ImportError",
        "ModuleNotFoundError",
        "AttributeError",
        "KeyError",
        "IndexError",
        "FileNotFoundError",
        "PermissionError",
        "RecursionError",
        "ZeroDivisionError",
    ],
    dependency_files=["requirements.txt", "Pipfile", "pyproject.toml", "setup.py", "environment.yml"],
    common_frameworks=["Flask", "Django", "FastAPI", "Tornado", "Pyramid", "Celery", "SQLAlchemy", "PySide6"],
    build_and_run_tools=["python", "pip", "pipenv", "poetry", "uv", "conda", "venv"],
    troubleshooting_guidance=[
        "Verify virtual environment activation (which python / where python).",
        "Check dependencies in requirements.txt or pyproject.toml and reinstall via 'pip install -r requirements.txt'.",
        "Examine Python version compatibility (e.g., Python 3.10+ syntax or removed modules).",
        "Check PYTHONPATH environment variable and current working directory for local module resolution.",
        "Inspect circular imports if ImportError or AttributeError occurs on module attributes.",
    ],
)

JAVA_PROFILE = LanguageProfile(
    name="Java",
    display_name="Java",
    file_extensions=[".java", ".class", ".jar"],
    common_exceptions=[
        "NullPointerException",
        "ClassNotFoundException",
        "NoClassDefFoundError",
        "NoSuchMethodError",
        "ArrayIndexOutOfBoundsException",
        "ClassCastException",
        "IllegalArgumentException",
        "IllegalStateException",
        "OutOfMemoryError",
        "StackOverflowError",
        "SQLException",
        "IOException",
    ],
    dependency_files=["pom.xml", "build.gradle", "build.gradle.kts", "settings.gradle"],
    common_frameworks=["Spring Boot", "Spring MVC", "Jakarta EE", "Quarkus", "Micronaut", "Hibernate", "JUnit"],
    build_and_run_tools=["javac", "java", "mvn", "gradle", "./mvnw", "./gradlew"],
    troubleshooting_guidance=[
        "Verify JAVA_HOME and target JDK/JRE bytecode compatibility (e.g., compiled with Java 21, running on Java 17).",
        "Check Maven/Gradle dependency coordinates and execute 'mvn clean compile' or 'gradle build --refresh-dependencies'.",
        "Investigate classpath/module-path configuration for missing JARs causing ClassNotFoundException.",
        "Inspect JVM memory flags (-Xmx, -Xms) if OutOfMemoryError is observed.",
        "Check Spring application.properties / application.yml for missing datasource or profile definitions.",
    ],
)

JAVASCRIPT_PROFILE = LanguageProfile(
    name="JavaScript",
    display_name="JavaScript",
    file_extensions=[".js", ".mjs", ".cjs", ".ts", ".jsx", ".tsx"],
    common_exceptions=[
        "SyntaxError",
        "TypeError",
        "ReferenceError",
        "RangeError",
        "URIError",
        "UnhandledPromiseRejection",
        "ERR_MODULE_NOT_FOUND",
        "MODULE_NOT_FOUND",
        "ECONNREFUSED",
        "EADDRINUSE",
    ],
    dependency_files=["package.json", "package-lock.json", "yarn.lock", "pnpm-lock.yaml"],
    common_frameworks=["Node.js", "Express", "React", "Next.js", "Vue", "Angular", "NestJS", "Fastify"],
    build_and_run_tools=["node", "npm", "yarn", "pnpm", "bun", "webpack", "vite", "esbuild", "tsc"],
    troubleshooting_guidance=[
        "Verify Node.js version compatibility with engines in package.json (nvm use).",
        "Run 'npm install' or clean cache and reinstall ('rm -rf node_modules package-lock.json && npm install').",
        "Check for CommonJS vs ES Module discrepancies ('type': 'module' vs require/import).",
        "Verify port availability if EADDRINUSE is thrown (check netstat/lsof).",
        "Check .env configuration and process.env variable injection for runtime configs.",
    ],
)

# Registry for profiles
_PROFILE_REGISTRY: Dict[str, LanguageProfile] = {
    "python": PYTHON_PROFILE,
    "java": JAVA_PROFILE,
    "javascript": JAVASCRIPT_PROFILE,
}


def register_language_profile(profile: LanguageProfile) -> None:
    """Register a new language profile (e.g., C, C++, Go, Rust) dynamically."""
    _PROFILE_REGISTRY[profile.name.lower()] = profile


def get_language_profile(name: str) -> LanguageProfile:
    """Retrieve profile by language name; returns Python profile as fallback."""
    key = (name or "").strip().lower()
    return _PROFILE_REGISTRY.get(key, PYTHON_PROFILE)


def list_supported_languages() -> List[str]:
    """Return ordered list of supported language display names."""
    return [p.display_name for p in _PROFILE_REGISTRY.values()]
