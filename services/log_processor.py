"""Log file processing, secret redaction, truncation, and signal extraction."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

ALLOWED_EXTENSIONS = {
    ".log",
    ".txt",
    ".out",
    ".err",
    ".json",
    ".csv",
    ".md",
    ".yaml",
    ".yml",
    ".py",
    ".java",
    ".js",
    ".ts",
    ".sh",
    ".bat",
    ".ps1",
    ".xml",
    ".ini",
    ".conf",
    ".env.example",
}


@dataclass
class RedactionResult:
    """Outcome of secret redaction."""

    cleaned_text: str
    redaction_count: int
    categories_redacted: dict[str, int] = field(default_factory=dict)


@dataclass
class ProcessedLog:
    """Result of normalizing, truncating, and redacting a log or error text."""

    original_length: int
    final_length: int
    was_truncated: bool
    truncated_chars: int
    redaction_result: RedactionResult
    signals: dict[str, Any] = field(default_factory=dict)


class LogProcessor:
    """Handles text validation, normalization, secret redaction, and signal extraction."""

    # Pre-compiled secret patterns
    PATTERNS: list[tuple[str, re.Pattern[str], str]] = [
        # Private key blocks
        (
            "Private Key",
            re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----[\s\S]*?-----END [A-Z ]*PRIVATE KEY-----"),
            "[REDACTED_PRIVATE_KEY]",
        ),
        # AWS Access Key ID
        (
            "AWS Key",
            re.compile(r"\b(AKIA|ABIA|ACCA|ASIA)[0-9A-Z]{16}\b"),
            "[REDACTED_AWS_KEY]",
        ),
        # OpenAI / generic sk- API keys
        (
            "API Key (sk-)",
            re.compile(r"\bsk-[a-zA-Z0-9_\-]{20,}\b"),
            "[REDACTED_API_KEY]",
        ),
        # Google AIza API Key
        (
            "Google API Key",
            re.compile(r"\bAIza[0-9A-Za-z\-_]{35}\b"),
            "[REDACTED_API_KEY]",
        ),
        # GitHub Personal Access Token
        (
            "GitHub Token",
            re.compile(r"\bgh[pousr]_[a-zA-Z0-9]{36,255}\b"),
            "[REDACTED_GITHUB_TOKEN]",
        ),
        # Slack tokens
        (
            "Slack Token",
            re.compile(r"\bxox[baprs]-[0-9a-zA-Z]{10,48}\b"),
            "[REDACTED_SLACK_TOKEN]",
        ),
        # JSON Web Tokens (JWT)
        (
            "JWT Token",
            re.compile(r"\beyJ[a-zA-Z0-9_-]{10,}\.eyJ[a-zA-Z0-9_-]{10,}\.[a-zA-Z0-9_-]{10,}\b"),
            "[REDACTED_JWT_TOKEN]",
        ),
        # Bearer Tokens in headers
        (
            "Bearer Token",
            re.compile(r"(?i)\bBearer\s+[a-zA-Z0-9_\-\.]{20,}\b"),
            "Bearer [REDACTED_BEARER_TOKEN]",
        ),
        # Basic auth headers
        (
            "Basic Auth Header",
            re.compile(r"(?i)\bAuthorization:\s*Basic\s+[a-zA-Z0-9+/=]{10,}\b"),
            "Authorization: Basic [REDACTED_BASIC_AUTH]",
        ),
        # Connection strings with credentials
        (
            "Connection URI Credentials",
            re.compile(r"((?:https?|mongodb|mongodb\+srv|postgres|postgresql|mysql|redis)://)([^:\s@]+):([^@\s]+)@"),
            r"\1[REDACTED_USER]:[REDACTED_PASSWORD]@",
        ),
        # Key-Value assignments (password=..., token: ...)
        (
            "Secret Assignment",
            re.compile(
                r"(?i)\b(password|passwd|pwd|secret|api_key|apikey|client_secret|access_token|auth_token)\s*([:=])\s*([\"']?)([^\s\"';,\n\r]+)(\3)"
            ),
            r"\1\2\3[REDACTED_SECRET]\5",
        ),
    ]

    @classmethod
    def validate_file(cls, file_path: str | Path, max_bytes: int = 1_048_576) -> tuple[bool, str]:
        """Validate an uploaded log file: extension, existence, size, and text/binary check."""
        path = Path(file_path)
        if not path.exists():
            return False, f"File does not exist: {path.name}"

        if not path.is_file():
            return False, f"Target is not a regular file: {path.name}"

        # Allowed extensions
        ext = path.suffix.lower()
        if ext not in ALLOWED_EXTENSIONS:
            allowed_list = ", ".join(sorted(ALLOWED_EXTENSIONS))
            return False, f"Unsupported file type '{ext}'. Allowed extensions: {allowed_list}"

        # File size
        size = path.stat().st_size
        if size == 0:
            return False, "Selected file is empty."
        if size > max_bytes:
            mb = max_bytes / (1024 * 1024)
            return False, f"File size ({size / 1024:.1f} KB) exceeds the {mb:.1f} MB limit."

        # Binary content check: read first 4096 bytes and look for null bytes or control char density
        try:
            with open(path, "rb") as f:
                chunk = f.read(4096)
                if b"\x00" in chunk:
                    return False, "File appears to contain binary content (null bytes found)."
                # Check control character percentage (excluding \t, \n, \r)
                text_chars = bytearray({7, 8, 9, 10, 12, 13, 27} | set(range(0x20, 0x100)) - {0x7F})
                non_text = chunk.translate(None, text_chars)
                if len(non_text) / max(1, len(chunk)) > 0.3:
                    return False, "File appears to be binary or contains excessive control characters."
        except Exception as e:
            return False, f"Unable to read file: {e}"

        return True, "File is valid."

    @classmethod
    def read_file_safely(cls, file_path: str | Path) -> str:
        """Read a text file with multi-encoding fallback (utf-8, utf-8-sig, latin-1, replace)."""
        path = Path(file_path)
        raw_bytes = path.read_bytes()

        for enc in ("utf-8", "utf-8-sig", "latin-1", "cp1252"):
            try:
                return raw_bytes.decode(enc)
            except UnicodeDecodeError:
                continue

        # Ultimate fallback: replace undecodable bytes without crashing
        return raw_bytes.decode("utf-8", errors="replace")

    @classmethod
    def normalize_text(cls, text: str) -> str:
        """Unify line endings to LF, strip control chars, and collapse blank lines."""
        if not text:
            return ""

        # Normalize line endings
        text = text.replace("\r\n", "\n").replace("\r", "\n")

        # Remove control characters except tab and newline
        text = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]", "", text)

        # Collapse 3 or more consecutive newlines into 2
        text = re.sub(r"\n{3,}", "\n\n", text)

        return text.strip()

    @classmethod
    def redact_secrets(cls, text: str) -> RedactionResult:
        """Redact sensitive patterns (tokens, keys, passwords, credentials) from text."""
        cleaned = text
        total_count = 0
        categories: dict[str, int] = {}

        for cat_name, pattern, replacement in cls.PATTERNS:
            matches = list(pattern.finditer(cleaned))
            if matches:
                count = len(matches)
                total_count += count
                categories[cat_name] = categories.get(cat_name, 0) + count
                cleaned = pattern.sub(replacement, cleaned)

        return RedactionResult(
            cleaned_text=cleaned,
            redaction_count=total_count,
            categories_redacted=categories,
        )

    @classmethod
    def truncate_intelligently(
        cls,
        text: str,
        max_chars: int = 16_000,
        head_chars: int = 4_000,
        tail_chars: int = 10_000,
    ) -> tuple[str, bool, int]:
        """Truncate large text intelligently, preserving head (context) and tail (stack trace)."""
        if len(text) <= max_chars:
            return text, False, 0

        # Adjust head and tail to fit max_chars
        if head_chars + tail_chars >= max_chars:
            head_chars = int(max_chars * 0.3)
            tail_chars = int(max_chars * 0.6)

        head = text[:head_chars]
        tail = text[-tail_chars:]
        truncated_count = len(text) - (head_chars + tail_chars)

        marker = f"\n\n[... Truncated {truncated_count:,} characters from middle to fit AI analysis limits ...]\n\n"
        result = head + marker + tail
        return result, True, truncated_count

    @classmethod
    def extract_signals(cls, text: str) -> dict[str, Any]:
        """Extract lightweight hints: exception types, likely language, stack trace lines."""
        signals: dict[str, Any] = {
            "exceptions": [],
            "language_hints": [],
            "has_stack_trace": False,
        }

        # Python exception patterns: Traceback (most recent call last): ... NameError: ...
        if "Traceback (most recent call last):" in text or re.search(r"File \".*\", line \d+", text):
            signals["language_hints"].append("Python")
            signals["has_stack_trace"] = True

        py_exceptions = re.findall(
            r"\b([A-Z][a-zA-Z0-9]*(?:Error|Exception|Warning|Interrupt|Exit)):\s*(.*)",
            text,
        )
        if py_exceptions:
            for exc_type, msg in py_exceptions[-3:]:
                signals["exceptions"].append(f"{exc_type}: {msg.strip()[:80]}")

        # Java exception patterns: Exception in thread ... at com.foo.Bar
        if re.search(r"\bat\s+[a-zA-Z0-9_$.]+\([a-zA-Z0-9_]+\.java:\d+\)", text) or "java.lang." in text:
            signals["language_hints"].append("Java")
            signals["has_stack_trace"] = True

        java_exceptions = re.findall(
            r"\b([a-zA-Z0-9_.]*(?:Exception|Error))(?::\s*([^\n\r]*))?",
            text,
        )
        if java_exceptions:
            for exc_type, msg in java_exceptions[-5:]:
                short_exc = exc_type.split(".")[-1]
                if short_exc not in ("Exception", "Error"):
                    signals["exceptions"].append(f"{short_exc}: {msg.strip()[:80]}" if msg else short_exc)

        # JavaScript/Node exception patterns: at /app/node_modules/... or ReferenceError:
        if re.search(r"\bat\s+(?:async\s+)?(?:[a-zA-Z0-9_$.<>]+\s+)?\([^)]+:\d+:\d+\)", text) or "node_modules" in text:
            signals["language_hints"].append("JavaScript")
            signals["has_stack_trace"] = True

        js_exceptions = re.findall(
            r"\b(TypeError|ReferenceError|SyntaxError|RangeError|URIError|EvalError|AssertionError):\s*(.*)",
            text,
        )
        if js_exceptions:
            for exc_type, msg in js_exceptions[-3:]:
                signals["exceptions"].append(f"{exc_type}: {msg.strip()[:80]}")

        # C / C++ exception & compiler patterns: Segmentation fault, undefined reference, fatal error, CMake Error
        if (
            re.search(r"\b(Segmentation fault|SIGSEGV|SIGABRT|double free)\b", text, re.IGNORECASE)
            or re.search(r"\b(undefined reference to|fatal error: .* No such file|CMake Error)\b", text)
            or re.search(r"\.(?:c|cpp|cc|cxx|hpp|h):\d+:\d+:\s*(?:error|fatal error)", text)
        ):
            if ".cpp" in text or ".hpp" in text or "g++" in text or "clang++" in text or "std::" in text:
                signals["language_hints"].append("C++")
            else:
                signals["language_hints"].append("C")

            if "Segmentation fault" in text or "SIGSEGV" in text:
                signals["exceptions"].append("SIGSEGV: Segmentation fault (core dumped)")
            elif "undefined reference" in text:
                signals["exceptions"].append("Linker Error: Undefined reference to symbol")
            elif "CMake Error" in text:
                signals["exceptions"].append("CMake Error: Configuration / build generation failure")

        # Deduplicate signals
        signals["language_hints"] = list(dict.fromkeys(signals["language_hints"]))
        signals["exceptions"] = list(dict.fromkeys(signals["exceptions"]))

        return signals

    @classmethod
    def process(cls, raw_text: str, max_chars: int = 16_000) -> ProcessedLog:
        """Execute full normalization, secret redaction, intelligent truncation, and signal extraction."""
        original_length = len(raw_text)
        normalized = cls.normalize_text(raw_text)
        redaction_res = cls.redact_secrets(normalized)
        truncated_text, was_truncated, truncated_chars = cls.truncate_intelligently(
            redaction_res.cleaned_text,
            max_chars=max_chars,
        )
        redaction_res.cleaned_text = truncated_text
        signals = cls.extract_signals(truncated_text)

        return ProcessedLog(
            original_length=original_length,
            final_length=len(truncated_text),
            was_truncated=was_truncated,
            truncated_chars=truncated_chars,
            redaction_result=redaction_res,
            signals=signals,
        )
