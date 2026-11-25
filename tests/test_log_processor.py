"""Tests for LogProcessor: validation, normalization, redaction, truncation, and signals."""

import tempfile
from pathlib import Path

import pytest

from services.log_processor import LogProcessor


def test_file_validation_valid():
    """Verify standard supported log file passes validation."""
    with tempfile.NamedTemporaryFile(suffix=".log", mode="w", encoding="utf-8", delete=False) as f:
        f.write("Standard error log content\nTraceback...\n")
        path = f.name

    try:
        is_valid, msg = LogProcessor.validate_file(path)
        assert is_valid is True
    finally:
        Path(path).unlink(missing_ok=True)


def test_file_validation_unsupported_ext():
    """Verify unsupported file extensions are rejected."""
    with tempfile.NamedTemporaryFile(suffix=".exe", mode="wb", delete=False) as f:
        f.write(b"MZ\x90\x00")
        path = f.name

    try:
        is_valid, msg = LogProcessor.validate_file(path)
        assert is_valid is False
        assert "Unsupported file type" in msg
    finally:
        Path(path).unlink(missing_ok=True)


def test_file_validation_binary():
    """Verify files with null bytes are rejected as binary."""
    with tempfile.NamedTemporaryFile(suffix=".txt", mode="wb", delete=False) as f:
        f.write(b"Text header\x00\x00binary data")
        path = f.name

    try:
        is_valid, msg = LogProcessor.validate_file(path)
        assert is_valid is False
        assert "binary content" in msg
    finally:
        Path(path).unlink(missing_ok=True)


def test_file_validation_oversize():
    """Verify oversized files exceed limit."""
    with tempfile.NamedTemporaryFile(suffix=".log", mode="wb", delete=False) as f:
        f.write(b"x" * 2000)
        path = f.name

    try:
        is_valid, msg = LogProcessor.validate_file(path, max_bytes=1000)
        assert is_valid is False
        assert "exceeds" in msg
    finally:
        Path(path).unlink(missing_ok=True)


def test_normalize_text():
    """Verify CRLF conversion, control char removal, and multiple newline collapsing."""
    raw = "Line 1\r\nLine 2\r\n\n\n\n\nLine 3\x01\x02\n"
    normalized = LogProcessor.normalize_text(raw)
    assert "\r" not in normalized
    assert "\x01" not in normalized
    assert "\n\n\n" not in normalized
    assert "Line 1\nLine 2\n\nLine 3" == normalized


def test_secret_redaction_api_keys():
    """Verify API keys from common providers are redacted."""
    text = (
        "API key: sk-abcdefghijklmnopqrstuvwxyz123456\n"
        "Google key: AIzaSyD1234567890abcdefghijklmnopqrstuv\n"
        "GitHub token: ghp_1234567890abcdefghijklmnopqrstuvwxyzAB\n"
        "Slack: xoxb-TESTINGTOKENREDACTION1234567890\n"
    )
    res = LogProcessor.redact_secrets(text)
    assert res.redaction_count >= 4
    assert "sk-" not in res.cleaned_text
    assert "AIza" not in res.cleaned_text
    assert "ghp_" not in res.cleaned_text
    assert "[REDACTED_API_KEY]" in res.cleaned_text
    assert "[REDACTED_GITHUB_TOKEN]" in res.cleaned_text


def test_secret_redaction_passwords_and_connections():
    """Verify passwords in key-value pairs and connection strings are redacted."""
    text = (
        'DB connection: postgresql://admin_user:super_secret_password_123@db.example.com:5432/mydb\n'
        'config: password="my_db_password_xyz"\n'
        'apiKey = "secret_token_val"\n'
    )
    res = LogProcessor.redact_secrets(text)
    assert "super_secret_password_123" not in res.cleaned_text
    assert "my_db_password_xyz" not in res.cleaned_text
    assert "secret_token_val" not in res.cleaned_text
    assert "[REDACTED_PASSWORD]" in res.cleaned_text or "[REDACTED_SECRET]" in res.cleaned_text


def test_secret_redaction_private_keys():
    """Verify PEM private key blocks are fully removed."""
    text = (
        "Logs starting...\n"
        "-----BEGIN RSA PRIVATE KEY-----\n"
        "MIIEowIBAAKCAQEA0Y1234567890abcdefgh\n"
        "-----END RSA PRIVATE KEY-----\n"
        "Logs ending."
    )
    res = LogProcessor.redact_secrets(text)
    assert "MIIEowIBAAKCAQEA0Y1234567890abcdefgh" not in res.cleaned_text
    assert "[REDACTED_PRIVATE_KEY]" in res.cleaned_text


def test_intelligent_truncation():
    """Verify truncation preserves head and tail and inserts clear marker."""
    head_content = "START_OF_LOG_HEADER\n" * 50
    middle_content = "REPETITIVE_DEBUG_NOISE\n" * 500
    tail_content = "\nFATAL_STACK_TRACE_ERROR_AT_END"

    full_text = head_content + middle_content + tail_content
    truncated, was_trunc, count = LogProcessor.truncate_intelligently(
        full_text,
        max_chars=2000,
        head_chars=400,
        tail_chars=800,
    )

    assert was_trunc is True
    assert count > 0
    assert "START_OF_LOG_HEADER" in truncated
    assert "FATAL_STACK_TRACE_ERROR_AT_END" in truncated
    assert "Truncated" in truncated


def test_signal_extraction_python():
    """Verify Python exception extraction and traceback detection."""
    log = """
    Traceback (most recent call last):
      File "/app/main.py", line 12, in <module>
        import flask
    ModuleNotFoundError: No module named 'flask'
    """
    signals = LogProcessor.extract_signals(log)
    assert "Python" in signals["language_hints"]
    assert signals["has_stack_trace"] is True
    assert any("ModuleNotFoundError" in e for e in signals["exceptions"])


def test_signal_extraction_java():
    """Verify Java exception and stack trace detection."""
    log = """
    Exception in thread "main" java.lang.NullPointerException
        at com.example.service.UserService.login(UserService.java:45)
    """
    signals = LogProcessor.extract_signals(log)
    assert "Java" in signals["language_hints"]
    assert signals["has_stack_trace"] is True
    assert any("NullPointerException" in e for e in signals["exceptions"])
