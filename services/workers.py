"""Background worker threads for non-blocking AI analysis and log processing."""

from __future__ import annotations

import logging
from typing import Any, Dict

from PySide6.QtCore import QThread, Signal

from config.settings import AppConfig, settings
from services.ai_service import (
    AIService,
    AuthenticationError,
    MalformedResponseError,
    MissingAPIKeyError,
    NetworkTimeoutError,
    RateLimitError,
)
from services.log_processor import LogProcessor, ProcessedLog

logger = logging.getLogger(__name__)


class AnalysisWorker(QThread):
    """QThread background worker executing log sanitization and AI analysis."""

    started_signal = Signal()
    progress_signal = Signal(str)  # Status message
    finished_signal = Signal(dict, object)  # Result dict, ProcessedLog object
    error_signal = Signal(str)  # Friendly error message

    def __init__(
        self,
        language: str,
        problem_type: str,
        environment: str,
        framework: str,
        raw_error_log: str,
        cfg: AppConfig | None = None,
        parent: Any = None,
    ) -> None:
        super().__init__(parent)
        self.language = language
        self.problem_type = problem_type
        self.environment = environment
        self.framework = framework
        self.raw_error_log = raw_error_log
        self.cfg = cfg or settings
        self._is_cancelled = False

    def cancel(self) -> None:
        """Flag the worker to cancel processing."""
        self._is_cancelled = True

    def run(self) -> None:
        """Worker thread entry point."""
        self.started_signal.emit()

        try:
            if self._is_cancelled:
                return

            # Step 1: Pre-process, normalize, redact secrets, truncate
            self.progress_signal.emit("Analyzing log content & redacting sensitive secrets...")
            processed_log: ProcessedLog = LogProcessor.process(
                self.raw_error_log,
                max_chars=self.cfg.max_log_chars_for_ai,
            )

            if self._is_cancelled:
                return

            # Step 2: Prepare payload for AI analysis
            effective_provider = self.cfg.get_effective_provider()
            provider_label = "Demo Engine" if effective_provider == "demo" else effective_provider.title()
            self.progress_signal.emit(f"Connecting to {provider_label} AI service for analysis...")

            payload = {
                "language": self.language,
                "problem_type": self.problem_type,
                "environment": self.environment,
                "framework": self.framework,
                "error_log": processed_log.redaction_result.cleaned_text,
                "signals": processed_log.signals,
            }

            # Step 3: Execute AI analysis
            result = AIService.execute_analysis(payload, self.cfg)

            if self._is_cancelled:
                return

            self.progress_signal.emit("Finalizing structured recommendations...")
            self.finished_signal.emit(result, processed_log)

        except MissingAPIKeyError as e:
            provider = self.cfg.ai_provider.upper()
            msg = (
                f"No API key configured for {provider}.\n\n"
                f"How to fix:\n"
                f"1. Open the 'API Settings' button on the left sidebar and enter your key, or\n"
                f"2. Add {provider}_API_KEY=your_key in a .env file, or\n"
                f"3. Switch Provider to 'Demo Mode' in Settings to test without an API key."
            )
            self.error_signal.emit(msg)

        except AuthenticationError as e:
            self.error_signal.emit(
                f"API Authentication Failed: Your API key was rejected by the provider.\n\n"
                f"Please verify your API key in Settings or .env file.\n\nDetails: {e}"
            )

        except RateLimitError as e:
            self.error_signal.emit(
                f"Rate Limit Exceeded: The AI provider quota or rate limit has been reached.\n\n"
                f"Please wait a few moments and try again, or switch to Demo Mode in Settings.\n\nDetails: {e}"
            )

        except NetworkTimeoutError as e:
            self.error_signal.emit(
                f"Network Timeout: The request took longer than {self.cfg.ai_timeout_seconds} seconds to respond.\n\n"
                f"Check your internet connection or verify provider availability.\n\nDetails: {e}"
            )

        except MalformedResponseError as e:
            self.error_signal.emit(
                f"Malformed Response: The AI provider returned an unexpected structure.\n\n"
                f"You can click 'Analyze Problem' to retry. Details: {e}"
            )

        except Exception as e:
            logger.exception("Unexpected error in AnalysisWorker")
            self.error_signal.emit(
                f"An unexpected error occurred during analysis: {type(e).__name__}: {str(e)}\n\n"
                f"Your input is preserved. You can check settings or retry."
            )
