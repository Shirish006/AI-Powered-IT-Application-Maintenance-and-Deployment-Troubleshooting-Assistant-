"""Screen 2 - New Troubleshooting (Input & Analysis Submission)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from config.settings import AppConfig, settings
from database.db_manager import DBManager
from modules.languages import list_supported_languages
from services.log_processor import LogProcessor, ProcessedLog
from services.workers import AnalysisWorker
from ui.widgets import CardWidget, LoadingOverlay, get_app_icon


class PrivacyWarningDialog(QDialog):
    """Explicit privacy warning confirmation prior to sending logs to an external AI provider."""

    def __init__(self, provider_name: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("AI Privacy & Log Transmission Notice")
        self.setMinimumWidth(460)
        self.setModal(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        title = QLabel("Sensitive Data & External AI Notice")
        title.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        layout.addWidget(title)

        body = QLabel(
            f"You are about to transmit your error log to the configured external AI service ({provider_name.upper()}).\n\n"
            "• Best-effort automated redaction will replace common API keys, tokens, passwords, and authorization headers.\n"
            "• Please ensure you have reviewed your logs to confirm no internal proprietary data or credentials remain.\n"
            "• The AI service will generate diagnostic recommendations only. No code or commands will be executed automatically."
        )
        body.setWordWrap(True)
        body.setStyleSheet("color: #475569; font-size: 12px; line-height: 1.4;")
        layout.addWidget(body)

        self.dont_show_checkbox = QCheckBox("Don't show this confirmation again on this computer")
        self.dont_show_checkbox.setStyleSheet("color: #334155; font-size: 12px; margin-top: 6px;")
        layout.addWidget(self.dont_show_checkbox)

        btn_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btn_box.button(QDialogButtonBox.StandardButton.Ok).setText("Proceed to Analyze")
        btn_box.button(QDialogButtonBox.StandardButton.Ok).setProperty("class", "primaryBtn")
        btn_box.button(QDialogButtonBox.StandardButton.Cancel).setProperty("class", "secondaryBtn")
        btn_box.accepted.connect(self.accept)
        btn_box.rejected.connect(self.reject)
        layout.addWidget(btn_box)


class NewTroubleshootingScreen(QWidget):
    """Input screen for configuring and submitting new error logs for AI analysis."""

    analysis_completed = Signal(int)  # Emits newly created session ID
    navigate_to_settings = Signal()

    def __init__(self, db_manager: DBManager, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.db = db_manager
        self.current_worker: AnalysisWorker | None = None

        # Root scroll area
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        self.container = QWidget()
        self.main_layout = QVBoxLayout(self.container)
        self.main_layout.setContentsMargins(28, 28, 28, 28)
        self.main_layout.setSpacing(18)

        # 1. Header
        header_layout = QVBoxLayout()
        header_layout.setSpacing(4)
        title = QLabel("New Troubleshooting Session")
        title.setProperty("class", "screenTitle")
        subtitle = QLabel("Provide error details, stack traces, or log files for automated AI diagnosis")
        subtitle.setProperty("class", "screenSubtitle")
        header_layout.addWidget(title)
        header_layout.addWidget(subtitle)
        self.main_layout.addLayout(header_layout)

        # 2. Main Input Card
        form_card = CardWidget()
        form_card_layout = form_card.layout_box

        # Grid for Configuration dropdowns
        grid = QGridLayout()
        grid.setSpacing(12)

        # Programming Language
        lbl_lang = QLabel("Programming Language *")
        lbl_lang.setStyleSheet("font-weight: 600; color: #334155;")
        self.combo_language = QComboBox()
        self.combo_language.addItems(list_supported_languages())
        grid.addWidget(lbl_lang, 0, 0)
        grid.addWidget(self.combo_language, 1, 0)

        # Problem Type
        lbl_type = QLabel("Problem Type *")
        lbl_type.setStyleSheet("font-weight: 600; color: #334155;")
        self.combo_problem_type = QComboBox()
        self.combo_problem_type.addItems(["Automatic Detection", "Maintenance", "Deployment"])
        grid.addWidget(lbl_type, 0, 1)
        grid.addWidget(self.combo_problem_type, 1, 1)

        # Environment
        lbl_env = QLabel("Target Environment *")
        lbl_env.setStyleSheet("font-weight: 600; color: #334155;")
        self.combo_environment = QComboBox()
        self.combo_environment.addItems([
            "Development",
            "Testing",
            "Production",
            "Deployment Server",
            "Cloud",
            "Docker",
        ])
        grid.addWidget(lbl_env, 0, 2)
        grid.addWidget(self.combo_environment, 1, 2)

        # Application / Framework (Optional)
        lbl_framework = QLabel("Application / Framework (Optional)")
        lbl_framework.setStyleSheet("font-weight: 600; color: #334155;")
        self.input_framework = QLineEdit()
        self.input_framework.setPlaceholderText("e.g. Flask, Django, Spring Boot, React, Node.js, FastAPI")
        grid.addWidget(lbl_framework, 2, 0, 1, 3)
        grid.addWidget(self.input_framework, 3, 0, 1, 3)

        form_card_layout.addLayout(grid)

        # 3. Log / Error Text Input Area
        log_header = QHBoxLayout()
        lbl_log = QLabel("Error Message / Stack Trace / Log File *")
        lbl_log.setStyleSheet("font-weight: 600; color: #334155;")
        log_header.addWidget(lbl_log)
        log_header.addStretch()

        self.upload_btn = QPushButton("📁 Upload Log File...")
        self.upload_btn.setProperty("class", "secondaryBtn")
        self.upload_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.upload_btn.clicked.connect(self._on_upload_file_clicked)
        log_header.addWidget(self.upload_btn)
        form_card_layout.addLayout(log_header)

        self.text_error_log = QPlainTextEdit()
        self.text_error_log.setPlaceholderText(
            "Paste the complete error message, stack trace, container log, or build output here...\n\n"
            "Example:\n"
            "Traceback (most recent call last):\n"
            "  File \"/app/main.py\", line 4, in <module>\n"
            "    import flask\n"
            "ModuleNotFoundError: No module named 'flask'"
        )
        self.text_error_log.setMinimumHeight(240)
        self.text_error_log.textChanged.connect(self._on_text_changed)
        form_card_layout.addWidget(self.text_error_log)

        # Redaction & Truncation status label
        self.status_note_label = QLabel("")
        self.status_note_label.setStyleSheet("color: #64748b; font-size: 11px;")
        form_card_layout.addWidget(self.status_note_label)

        # 4. Action Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)

        self.clear_btn = QPushButton("Clear Form")
        self.clear_btn.setProperty("class", "secondaryBtn")
        self.clear_btn.clicked.connect(self.clear_form)
        btn_layout.addWidget(self.clear_btn)

        btn_layout.addStretch()

        self.analyze_btn = QPushButton("⚡ Analyze Problem")
        self.analyze_btn.setProperty("class", "primaryBtn")
        self.analyze_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.analyze_btn.setMinimumHeight(40)
        self.analyze_btn.setMinimumWidth(180)
        self.analyze_btn.clicked.connect(self.start_analysis)
        btn_layout.addWidget(self.analyze_btn)

        form_card_layout.addLayout(btn_layout)
        self.main_layout.addWidget(form_card)
        self.main_layout.addStretch()

        # Root layout with loading overlay
        scroll.setWidget(self.container)
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.addWidget(scroll)

        # Loading overlay
        self.loading_overlay = LoadingOverlay(self)
        self.loading_overlay.cancelled.connect(self._on_analysis_cancelled)

    def resizeEvent(self, event: Any) -> None:
        """Keep loading overlay sized to full widget area."""
        super().resizeEvent(event)
        self.loading_overlay.resize(self.size())

    def preselect_problem_type(self, problem_type: str) -> None:
        """Preselect the problem type dropdown when navigating from dashboard."""
        idx = self.combo_problem_type.findText(problem_type)
        if idx >= 0:
            self.combo_problem_type.setCurrentIndex(idx)

    def set_inputs(self, language: str, problem_type: str, environment: str, framework: str, error_log: str) -> None:
        """Populate form inputs (used by 'Try Again' button from analysis screen)."""
        idx_lang = self.combo_language.findText(language)
        if idx_lang >= 0:
            self.combo_language.setCurrentIndex(idx_lang)

        idx_type = self.combo_problem_type.findText(problem_type)
        if idx_type >= 0:
            self.combo_problem_type.setCurrentIndex(idx_type)

        idx_env = self.combo_environment.findText(environment)
        if idx_env >= 0:
            self.combo_environment.setCurrentIndex(idx_env)

        self.input_framework.setText(framework)
        self.text_error_log.setPlainText(error_log)

    def clear_form(self) -> None:
        """Reset the form to default blank state."""
        self.combo_language.setCurrentIndex(0)
        self.combo_problem_type.setCurrentIndex(0)
        self.combo_environment.setCurrentIndex(0)
        self.input_framework.clear()
        self.text_error_log.clear()
        self.status_note_label.setText("")

    def _on_text_changed(self) -> None:
        """Update live char count indicator."""
        length = len(self.text_error_log.toPlainText())
        if length > 0:
            self.status_note_label.setText(f"Character count: {length:,} characters (will be sanitized prior to AI submission)")
        else:
            self.status_note_label.setText("")

    def _on_upload_file_clicked(self) -> None:
        """Open file dialog, validate, and load log text safely."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Log or Error File",
            "",
            "Supported Log & Code Files (*.log *.txt *.out *.err *.json *.csv *.md *.yaml *.yml *.py *.java *.js *.ts *.xml *.ini *.conf);;All Files (*.*)",
        )
        if not file_path:
            return

        is_valid, message = LogProcessor.validate_file(file_path, max_bytes=settings.max_log_size_bytes)
        if not is_valid:
            QMessageBox.warning(self, "Invalid File", message)
            return

        try:
            content = LogProcessor.read_file_safely(file_path)
            self.text_error_log.setPlainText(content)

            # Auto-detect language hint if possible
            signals = LogProcessor.extract_signals(content)
            hints = signals.get("language_hints", [])
            if hints:
                suggested_lang = hints[0]
                idx = self.combo_language.findText(suggested_lang)
                if idx >= 0:
                    self.combo_language.setCurrentIndex(idx)

            QMessageBox.information(
                self,
                "File Loaded",
                f"Successfully loaded '{Path(file_path).name}' ({len(content):,} characters).\n"
                "Review the content and click 'Analyze Problem' when ready.",
            )
        except Exception as e:
            QMessageBox.critical(self, "File Read Error", f"Unable to read file: {e}")

    def start_analysis(self) -> None:
        """Validate input, show privacy warning if needed, and run background worker."""
        raw_text = self.text_error_log.toPlainText().strip()
        if not raw_text:
            QMessageBox.warning(self, "Missing Error Log", "Please paste an error message, stack trace, or upload a log file.")
            self.text_error_log.setFocus()
            return

        if len(raw_text) < 5:
            QMessageBox.warning(self, "Input Too Short", "The provided error text is too short to perform meaningful diagnosis.")
            return

        effective_provider = settings.get_effective_provider()

        # Check API key if not in demo mode
        if effective_provider != "demo" and not settings.has_valid_api_key():
            reply = QMessageBox.question(
                self,
                "API Key Not Configured",
                f"No API key is configured for {settings.ai_provider.upper()}.\n\n"
                "Would you like to switch to DEMO MODE to test the application offline?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply == QMessageBox.StandardButton.Yes:
                settings.demo_mode_forced = True
                settings.save_preferences()
                effective_provider = "demo"
            else:
                self.navigate_to_settings.emit()
                return

        # Privacy confirmation for external providers
        if effective_provider != "demo" and not settings.suppress_privacy_warning:
            dlg = PrivacyWarningDialog(settings.ai_provider, self)
            if dlg.exec() != QDialog.DialogCode.Accepted:
                return
            if dlg.dont_show_checkbox.isChecked():
                settings.suppress_privacy_warning = True
                settings.save_preferences()

        # Disable UI and show loading
        self.analyze_btn.setEnabled(False)
        self.upload_btn.setEnabled(False)
        self.clear_btn.setEnabled(False)
        self.loading_overlay.set_message("Preparing analysis...")
        self.loading_overlay.show()

        # Spawn background worker
        self.current_worker = AnalysisWorker(
            language=self.combo_language.currentText(),
            problem_type=self.combo_problem_type.currentText(),
            environment=self.combo_environment.currentText(),
            framework=self.input_framework.text().strip(),
            raw_error_log=raw_text,
            cfg=settings,
            parent=self,
        )
        self.current_worker.progress_signal.connect(self.loading_overlay.set_message)
        self.current_worker.finished_signal.connect(self._on_analysis_success)
        self.current_worker.error_signal.connect(self._on_analysis_error)
        self.current_worker.start()

    def _on_analysis_cancelled(self) -> None:
        """Handle user clicking Cancel on the loading overlay."""
        if self.current_worker and self.current_worker.isRunning():
            self.current_worker.cancel()
            self.current_worker.terminate()
            self.current_worker.wait(1000)

        self._reset_ui_state()
        QMessageBox.information(self, "Cancelled", "Analysis request was cancelled.")

    def _on_analysis_success(self, result: dict[str, Any], processed_log: ProcessedLog) -> None:
        """Handle worker success: persist automatically to SQLite and navigate to Screen 3."""
        self._reset_ui_state()

        # Save session automatically to SQLite with status 'Unresolved'
        session_data = {
            "programming_language": self.combo_language.currentText(),
            "problem_type": self.combo_problem_type.currentText(),
            "environment": self.combo_environment.currentText(),
            "application_framework": self.input_framework.text().strip(),
            "original_error_log": processed_log.redaction_result.cleaned_text,
            "error_category": result.get("error_category", "Runtime Error"),
            "severity": result.get("severity", "Medium"),
            "error_summary": result.get("error_summary", "Unspecified Error"),
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

        try:
            session_id = self.db.insert_session(session_data)
            self.analysis_completed.emit(session_id)
        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"Analysis completed but could not be saved to history: {e}")

    def _on_analysis_error(self, error_message: str) -> None:
        """Handle worker failure: show error dialog, keep user input intact."""
        self._reset_ui_state()
        QMessageBox.warning(self, "Troubleshooting Analysis Error", error_message)

    def _reset_ui_state(self) -> None:
        """Hide loading overlay and re-enable buttons."""
        self.loading_overlay.hide()
        self.analyze_btn.setEnabled(True)
        self.upload_btn.setEnabled(True)
        self.clear_btn.setEnabled(True)
        self.current_worker = None
