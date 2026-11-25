"""Application configuration and settings management.

Handles environment variables, default settings, user preferences persistence,
and resource path resolution for development and PyInstaller bundled environments.
"""

from __future__ import annotations

import json
import os
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

try:
    from platformdirs import user_data_dir
except ImportError:
    # Fallback if platformdirs is missing
    def user_data_dir(appname: str, appauthor: str | None = None) -> str:
        return str(Path.home() / f".{appname.lower()}")


APP_NAME = "AI_IT_Troubleshooting_Assistant"
APP_AUTHOR = "AI_IT_Assistant"
WINDOW_TITLE = "AI IT Troubleshooting Assistant"


def get_base_dir() -> Path:
    """Return the base directory of the project, whether running from source or frozen."""
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parent.parent


def get_resource_path(relative_path: str | Path) -> Path:
    """Resolve resource path for both development and PyInstaller packaged executable."""
    base = get_base_dir()
    return base / relative_path


def get_user_data_directory() -> Path:
    """Return the user data directory where SQLite database and user configs persist."""
    data_dir = Path(user_data_dir(APP_NAME, APP_AUTHOR))
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


# Load environment variables: check user data dir first, then project root, then current dir
_user_env = get_user_data_directory() / ".env"
_proj_env = get_base_dir() / ".env"
if _user_env.exists():
    load_dotenv(_user_env)
if _proj_env.exists():
    load_dotenv(_proj_env)
load_dotenv()  # fallback to standard cwd .env


@dataclass
class AppConfig:
    """Global configuration settings for the application."""

    ai_provider: str = "gemini"  # "gemini", "openai", "demo"
    gemini_api_key: str = ""
    openai_api_key: str = ""
    gemini_model: str = "gemini-3.8-flash"
    openai_model: str = "gpt-4o-mini"
    ai_timeout_seconds: int = 60
    max_log_size_bytes: int = 1_048_576  # 1 MB
    max_log_chars_for_ai: int = 16_000
    db_path: Path = field(default_factory=lambda: get_user_data_directory() / "troubleshooting.db")
    suppress_privacy_warning: bool = False
    demo_mode_forced: bool = False

    @classmethod
    def load(cls) -> AppConfig:
        """Load configuration from environment variables and user preferences file."""
        config = cls()

        # 1. Environment variables
        env_provider = os.getenv("AI_PROVIDER", "").strip().lower()
        if env_provider in ("gemini", "openai", "demo"):
            config.ai_provider = env_provider

        config.gemini_api_key = os.getenv("GEMINI_API_KEY", "").strip()
        config.openai_api_key = os.getenv("OPENAI_API_KEY", "").strip()
        config.gemini_model = os.getenv("GEMINI_MODEL", config.gemini_model).strip()
        config.openai_model = os.getenv("OPENAI_MODEL", config.openai_model).strip()

        try:
            config.ai_timeout_seconds = int(os.getenv("AI_TIMEOUT_SECONDS", str(config.ai_timeout_seconds)))
        except ValueError:
            pass

        try:
            config.max_log_size_bytes = int(os.getenv("MAX_LOG_SIZE_BYTES", str(config.max_log_size_bytes)))
        except ValueError:
            pass

        try:
            config.max_log_chars_for_ai = int(os.getenv("MAX_LOG_CHARS_FOR_AI", str(config.max_log_chars_for_ai)))
        except ValueError:
            pass

        db_env = os.getenv("DB_PATH", "").strip()
        if db_env:
            config.db_path = Path(db_env)

        # 2. User preferences JSON file (saved by GUI settings dialog)
        prefs_file = get_user_data_directory() / "preferences.json"
        if prefs_file.exists():
            try:
                with open(prefs_file, "r", encoding="utf-8") as f:
                    prefs: dict[str, Any] = json.load(f)
                    if "ai_provider" in prefs:
                        config.ai_provider = prefs["ai_provider"]
                    if "gemini_api_key" in prefs and not config.gemini_api_key:
                        config.gemini_api_key = prefs["gemini_api_key"]
                    if "openai_api_key" in prefs and not config.openai_api_key:
                        config.openai_api_key = prefs["openai_api_key"]
                    if "gemini_model" in prefs:
                        config.gemini_model = prefs["gemini_model"]
                    if "openai_model" in prefs:
                        config.openai_model = prefs["openai_model"]
                    if "suppress_privacy_warning" in prefs:
                        config.suppress_privacy_warning = bool(prefs["suppress_privacy_warning"])
                    if "demo_mode_forced" in prefs:
                        config.demo_mode_forced = bool(prefs["demo_mode_forced"])
            except Exception:
                pass  # Fall back to env/defaults safely

        return config

    def save_preferences(self) -> None:
        """Save UI-configurable preferences to user preferences JSON file."""
        prefs_file = get_user_data_directory() / "preferences.json"
        data = {
            "ai_provider": self.ai_provider,
            "gemini_api_key": self.gemini_api_key,
            "openai_api_key": self.openai_api_key,
            "gemini_model": self.gemini_model,
            "openai_model": self.openai_model,
            "suppress_privacy_warning": self.suppress_privacy_warning,
            "demo_mode_forced": self.demo_mode_forced,
        }
        try:
            with open(prefs_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception:
            pass

    def get_effective_provider(self) -> str:
        """Return which provider will be used: 'gemini', 'openai', or 'demo'."""
        if self.demo_mode_forced or self.ai_provider == "demo":
            return "demo"
        if self.ai_provider == "gemini":
            return "gemini" if self.gemini_api_key else "demo"
        if self.ai_provider == "openai":
            return "openai" if self.openai_api_key else "demo"
        return "demo"

    def has_valid_api_key(self) -> bool:
        """Check if an API key is available for the active provider."""
        if self.ai_provider == "gemini":
            return bool(self.gemini_api_key)
        if self.ai_provider == "openai":
            return bool(self.openai_api_key)
        return False


# Global singleton settings
settings = AppConfig.load()
