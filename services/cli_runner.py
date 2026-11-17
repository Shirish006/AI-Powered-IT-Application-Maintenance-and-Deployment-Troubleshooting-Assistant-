"""Command-line interface (CLI) runner for headless troubleshooting in Antigravity IDE."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List, Optional

from config.settings import settings
from database.db_manager import DBManager
from modules.languages import get_language_profile, list_supported_languages
from services.ai_service import AIService
from services.log_processor import LogProcessor


def build_cli_parser() -> argparse.ArgumentParser:
    """Construct command-line argument parser."""
    parser = argparse.ArgumentParser(
        prog="ai-troubleshoot",
        description="AI-Powered IT Application Maintenance & Deployment Troubleshooting Assistant (CLI Mode)",
    )
    parser.add_argument("--cli", action="store_true", help="Run in CLI headless mode without launching PySide6 GUI")
    parser.add_argument("-f", "--file", type=str, help="Path to error log or output file to diagnose")
    parser.add_argument("-l", "--log", type=str, help="Raw error log or traceback string")
    parser.add_argument(
        "--language",
        type=str,
        default="",
        help="Target language (Python, Java, JavaScript, C, C++). If omitted, auto-detected from log signals.",
    )
    parser.add_argument(
        "--problem-type",
        type=str,
        default="Automatic Detection",
        choices=["Automatic Detection", "Maintenance", "Deployment"],
        help="Problem type category",
    )
    parser.add_argument(
        "--environment",
        type=str,
        default="Development",
        help="Target environment (Development, Testing, Production, Deployment Server, Cloud, Docker)",
    )
    parser.add_argument("--framework", type=str, default="", help="Application or framework name (e.g. Flask, Spring)")
    parser.add_argument("--export", type=str, help="Export diagnosis to specified file path (.md, .html, or .json)")
    return parser


def format_cli_output(session_id: int, result: dict, redactions_count: int) -> str:
    """Format structured diagnosis into clean terminal-friendly text."""
    sep = "=" * 70
    subsep = "-" * 70

    lines = [
        "",
        sep,
        "   AI IT TROUBLESHOOTING ASSISTANT - DIAGNOSIS REPORT",
        sep,
        f"Session ID       : #{session_id} (Saved to SQLite database)",
        f"Language         : {result.get('programming_language', 'Unknown')}",
        f"Problem Type     : {result.get('detected_problem_type', result.get('problem_type', 'Maintenance'))}",
        f"Error Category   : {result.get('error_category', 'General Error')}",
        f"Severity Level   : {result.get('severity', 'Medium').upper()}",
        f"Engine / Model   : {result.get('ai_provider', 'Demo')} ({result.get('ai_model', 'Built-in Heuristic')})",
        f"Secrets Redacted : {redactions_count} sensitive pattern(s) removed",
        subsep,
        "1. ERROR SUMMARY",
        f"   {result.get('error_summary', 'No summary available.')}",
        "",
        "2. EXPLANATION (Beginner-Friendly)",
        f"   {result.get('explanation', 'No explanation provided.')}",
        "",
        "3. CONFIRMED FACTS (Verified from Provided Log)",
    ]

    for fact in result.get("confirmed_facts", []):
        lines.append(f"   [+] {fact}")

    lines.extend(["", "4. POSSIBLE CAUSES (Hypotheses)"])
    for cause in result.get("possible_causes", []):
        lines.append(f"   [?] {cause}")

    lines.extend(["", "5. ORDERED TROUBLESHOOTING STEPS"])
    for i, step in enumerate(result.get("troubleshooting_steps", []), 1):
        lines.append(f"   {i}. {step}")

    lines.extend([
        "",
        "6. SUGGESTED SOLUTION",
        f"   {result.get('suggested_solution', 'No solution suggested.')}",
        "",
        "7. VERIFICATION STEPS",
    ])
    for i, vstep in enumerate(result.get("verification_steps", []), 1):
        lines.append(f"   {i}. {vstep}")

    lines.extend([
        sep,
        "Notice: Guidance is intended for developer review. The assistant never",
        "modifies or executes commands on your external systems.",
        sep,
        "",
    ])

    return "\n".join(lines)


def run_cli(args: argparse.Namespace, db: Optional[DBManager] = None) -> int:
    """Execute analysis via command-line interface."""
    raw_content = ""

    if args.file:
        file_path = Path(args.file)
        if not file_path.exists():
            print(f"[ERROR] Specified file does not exist: {file_path}", file=sys.stderr)
            return 1
        is_valid, err_msg = LogProcessor.validate_file(file_path)
        if not is_valid:
            print(f"[ERROR] File validation failed: {err_msg}", file=sys.stderr)
            return 1
        raw_content = LogProcessor.read_file_safely(file_path)
    elif args.log:
        raw_content = args.log
    else:
        print("[ERROR] Please provide an error log using --file <path> or --log <text>.", file=sys.stderr)
        return 1

    # Redact secrets and extract signals
    redaction = LogProcessor.redact_secrets(raw_content)
    processed_log, was_truncated, trunc_chars = LogProcessor.truncate_intelligently(redaction.cleaned_text)
    trunc_note = f"Truncated {trunc_chars} chars" if was_truncated else ""
    signals = LogProcessor.extract_signals(processed_log)

    # Validate or auto-detect language
    target_lang = args.language.strip()
    if not target_lang:
        if signals.get("language_hints"):
            target_lang = signals["language_hints"][0]
        else:
            target_lang = "Python"

    lang_profile = get_language_profile(target_lang)
    normalized_lang = lang_profile.name if lang_profile else "Python"

    payload = {
        "programming_language": normalized_lang,
        "problem_type": args.problem_type,
        "environment": args.environment,
        "application_framework": args.framework or "Not specified",
        "error_log": processed_log,
        "extracted_signals": signals,
        "was_truncated": was_truncated,
        "truncation_note": trunc_note,
        "redactions_applied": redaction.redaction_count,
    }

    print("[*] Analyzing error with AI Troubleshooting Engine...")
    try:
        result = AIService.execute_analysis(payload, settings)
    except Exception as e:
        print(f"[ERROR] Analysis failed: {e}", file=sys.stderr)
        return 1

    # Store in database
    if db is None:
        db = DBManager(settings.db_path)

    session_data = {
        "programming_language": normalized_lang,
        "problem_type": args.problem_type,
        "environment": args.environment,
        "application_framework": args.framework or "Not specified",
        "original_error_log": processed_log,
        "error_category": result.get("error_category", "General Error"),
        "severity": result.get("severity", "Medium"),
        "error_summary": result.get("error_summary", ""),
        "error_explanation": result.get("explanation", ""),
        "confirmed_facts": result.get("confirmed_facts", []),
        "possible_causes": result.get("possible_causes", []),
        "troubleshooting_steps": result.get("troubleshooting_steps", []),
        "suggested_solution": result.get("suggested_solution", ""),
        "verification_steps": result.get("verification_steps", []),
        "resolution_status": "Unresolved",
        "is_demo": 1 if result.get("is_demo") else 0,
        "ai_provider": result.get("ai_provider", settings.ai_provider),
        "ai_model": result.get("ai_model", ""),
        "detected_problem_type": result.get("detected_problem_type", ""),
    }

    session_id = db.insert_session(session_data)

    result["programming_language"] = normalized_lang
    formatted_report = format_cli_output(session_id, result, redaction.redaction_count)
    print(formatted_report)

    # Optional export
    if args.export:
        export_path = Path(args.export)
        export_ext = export_path.suffix.lower()
        if export_ext == ".json":
            json_data = db.export_session_json(session_id)
            export_path.write_text(json_data, encoding="utf-8")
            print(f"[+] Exported JSON session backup to {export_path}")
        else:
            export_path.write_text(formatted_report, encoding="utf-8")
            print(f"[+] Exported diagnosis report to {export_path}")

    return 0
