"""Main Window container with sidebar navigation, stacked screen management, and API settings."""

from __future__ import annotations

from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QIcon
from PySide6.QtWidgets import (
    QButtonGroup,
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from config.settings import WINDOW_TITLE, settings
from database.db_manager import DBManager
from ui.analysis_screen import AnalysisScreen
from ui.dashboard import DashboardScreen
from ui.history_screen import HistoryScreen
from ui.new_troubleshooting import NewTroubleshootingScreen
from ui.widgets import get_app_icon


class SettingsDialog(QDialog):
    """Configuration dialog for setting AI provider, API keys, and models."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("AI Provider & API Settings")
        self.setMinimumWidth(500)
        self.setModal(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        title = QLabel("AI Configuration")
        title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        layout.addWidget(title)

        desc = QLabel(
            "Configure which AI provider handles error troubleshooting, or enable offline Demo Mode.\n"
            "Keys are stored in your secure local user profile and are never transmitted to third parties."
        )
        desc.setStyleSheet("color: #64748b; font-size: 12px;")
        desc.setWordWrap(True)
        layout.addWidget(desc)

        # Provider Selector
        p_layout = QHBoxLayout()
        p_lbl = QLabel("Active AI Provider:")
        p_lbl.setStyleSheet("font-weight: 600;")
        self.provider_combo = QComboBox()
        self.provider_combo.addItems(["Gemini (Google AI)", "OpenAI (GPT-4o)", "Demo Mode (Offline)"])

        # Set initial combo index
        if settings.demo_mode_forced or settings.ai_provider == "demo":
            self.provider_combo.setCurrentIndex(2)
        elif settings.ai_provider == "openai":
            self.provider_combo.setCurrentIndex(1)
        else:
            self.provider_combo.setCurrentIndex(0)

        self.provider_combo.currentIndexChanged.connect(self._on_provider_changed)
        p_layout.addWidget(p_lbl)
        p_layout.addWidget(self.provider_combo)
        layout.addLayout(p_layout)

        # Gemini Section
        self.gemini_group = QFrame()
        self.gemini_group.setStyleSheet("background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; padding: 12px;")
        g_layout = QVBoxLayout(self.gemini_group)
        g_layout.setSpacing(8)

        g_title = QLabel("Google Gemini Configuration")
        g_title.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        g_layout.addWidget(g_title)

        g_key_lbl = QLabel("Gemini API Key:")
        self.input_gemini_key = QLineEdit(settings.gemini_api_key)
        self.input_gemini_key.setEchoMode(QLineEdit.EchoMode.Password)
        self.input_gemini_key.setPlaceholderText("AIzaSy...")

        g_model_lbl = QLabel("Model Name:")
        self.input_gemini_model = QLineEdit(settings.gemini_model)

        g_layout.addWidget(g_key_lbl)
        g_layout.addWidget(self.input_gemini_key)
        g_layout.addWidget(g_model_lbl)
        g_layout.addWidget(self.input_gemini_model)
        layout.addWidget(self.gemini_group)

        # OpenAI Section
        self.openai_group = QFrame()
        self.openai_group.setStyleSheet("background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; padding: 12px;")
        o_layout = QVBoxLayout(self.openai_group)
        o_layout.setSpacing(8)

        o_title = QLabel("OpenAI Configuration")
        o_title.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        o_layout.addWidget(o_title)

        o_key_lbl = QLabel("OpenAI API Key:")
        self.input_openai_key = QLineEdit(settings.openai_api_key)
        self.input_openai_key.setEchoMode(QLineEdit.EchoMode.Password)
        self.input_openai_key.setPlaceholderText("sk-proj-...")

        o_model_lbl = QLabel("Model Name:")
        self.input_openai_model = QLineEdit(settings.openai_model)

        o_layout.addWidget(o_key_lbl)
        o_layout.addWidget(self.input_openai_key)
        o_layout.addWidget(o_model_lbl)
        o_layout.addWidget(self.input_openai_model)
        layout.addWidget(self.openai_group)

        # Show/Hide passwords toggle
        self.show_keys_cb = QCheckBox("Show API key characters")
        self.show_keys_cb.toggled.connect(self._toggle_password_visibility)
        layout.addWidget(self.show_keys_cb)

        # Reset Privacy Notice Checkbox
        self.reset_privacy_cb = QCheckBox("Reset privacy notice (show confirmation on next external AI request)")
        self.reset_privacy_cb.setChecked(not settings.suppress_privacy_warning)
        layout.addWidget(self.reset_privacy_cb)

        # Dialog Buttons
        btn_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        btn_box.button(QDialogButtonBox.StandardButton.Save).setProperty("class", "primaryBtn")
        btn_box.button(QDialogButtonBox.StandardButton.Cancel).setProperty("class", "secondaryBtn")
        btn_box.accepted.connect(self._save_settings)
        btn_box.rejected.connect(self.reject)
        layout.addWidget(btn_box)

        self._on_provider_changed(self.provider_combo.currentIndex())

    def _toggle_password_visibility(self, checked: bool) -> None:
        mode = QLineEdit.EchoMode.Normal if checked else QLineEdit.EchoMode.Password
        self.input_gemini_key.setEchoMode(mode)
        self.input_openai_key.setEchoMode(mode)

    def _on_provider_changed(self, index: int) -> None:
        """Toggle active provider box."""
        if index == 0:  # Gemini
            self.gemini_group.show()
            self.openai_group.hide()
        elif index == 1:  # OpenAI
            self.gemini_group.hide()
            self.openai_group.show()
        else:  # Demo
            self.gemini_group.hide()
            self.openai_group.hide()

    def _save_settings(self) -> None:
        """Persist settings to memory and file."""
        idx = self.provider_combo.currentIndex()
        if idx == 0:
            settings.ai_provider = "gemini"
            settings.demo_mode_forced = False
        elif idx == 1:
            settings.ai_provider = "openai"
            settings.demo_mode_forced = False
        else:
            settings.ai_provider = "demo"
            settings.demo_mode_forced = True

        settings.gemini_api_key = self.input_gemini_key.text().strip()
        settings.gemini_model = self.input_gemini_model.text().strip() or "gemini-2.5-flash"
        settings.openai_api_key = self.input_openai_key.text().strip()
        settings.openai_model = self.input_openai_model.text().strip() or "gpt-4o-mini"
        settings.suppress_privacy_warning = not self.reset_privacy_cb.isChecked()

        settings.save_preferences()
        self.accept()


class MainWindow(QMainWindow):
    """Root application window with sidebar navigation and stacked screens."""

    def __init__(self, db_manager: DBManager) -> None:
        super().__init__()
        self.db = db_manager
        self.setWindowTitle(WINDOW_TITLE)
        self.setMinimumSize(1100, 720)
        self.resize(1200, 780)

        app_icon = get_app_icon("app_icon.svg")
        if not app_icon.isNull():
            self.setWindowIcon(app_icon)

        # Central layout
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        main_h_layout = QHBoxLayout(central_widget)
        main_h_layout.setContentsMargins(0, 0, 0, 0)
        main_h_layout.setSpacing(0)

        # 1. Left Sidebar
        sidebar = self._create_sidebar()
        main_h_layout.addWidget(sidebar)

        # 2. Main Content Stacked Widget
        self.stacked_widget = QStackedWidget()
        self.stacked_widget.setObjectName("contentArea")

        # Initialize the 4 Screens
        self.screen_dashboard = DashboardScreen(self.db, self)
        self.screen_new_troubleshooting = NewTroubleshootingScreen(self.db, self)
        self.screen_analysis = AnalysisScreen(self.db, self)
        self.screen_history = HistoryScreen(self.db, self)

        self.stacked_widget.addWidget(self.screen_dashboard)  # Index 0
        self.stacked_widget.addWidget(self.screen_new_troubleshooting)  # Index 1
        self.stacked_widget.addWidget(self.screen_analysis)  # Index 2
        self.stacked_widget.addWidget(self.screen_history)  # Index 3

        main_h_layout.addWidget(self.stacked_widget, stretch=1)

        # Wire cross-screen navigation signals
        self._connect_signals()

        # Update initial status in sidebar
        self._update_sidebar_status()

    def _create_sidebar(self) -> QWidget:
        """Construct the left dark-indigo navigation sidebar."""
        sidebar_frame = QWidget()
        sidebar_frame.setObjectName("sidebarWidget")
        sidebar_frame.setFixedWidth(240)

        layout = QVBoxLayout(sidebar_frame)
        layout.setContentsMargins(0, 0, 0, 16)
        layout.setSpacing(6)

        # Header with Logo
        header = QFrame()
        header.setObjectName("sidebarHeader")
        h_layout = QVBoxLayout(header)
        h_layout.setContentsMargins(14, 16, 14, 16)
        h_layout.setSpacing(2)

        app_title = QLabel("AI IT Assistant")
        app_title.setObjectName("appLogoTitle")
        app_sub = QLabel("Troubleshooting System")
        app_sub.setObjectName("appLogoSubtitle")
        h_layout.addWidget(app_title)
        h_layout.addWidget(app_sub)
        layout.addWidget(header)

        layout.addSpacing(10)

        # Navigation Buttons Group
        self.nav_btn_group = QButtonGroup(self)
        self.nav_btn_group.setExclusive(True)

        self.btn_nav_dashboard = QPushButton("  Dashboard")
        self.btn_nav_dashboard.setProperty("class", "sidebarNavBtn")
        self.btn_nav_dashboard.setCheckable(True)
        self.btn_nav_dashboard.setChecked(True)
        self.btn_nav_dashboard.setIcon(get_app_icon("dashboard.svg"))
        self.btn_nav_dashboard.clicked.connect(lambda: self.switch_screen(0))
        self.nav_btn_group.addButton(self.btn_nav_dashboard, 0)
        layout.addWidget(self.btn_nav_dashboard)

        self.btn_nav_new = QPushButton("  New Issue")
        self.btn_nav_new.setProperty("class", "sidebarNavBtn")
        self.btn_nav_new.setCheckable(True)
        self.btn_nav_new.setIcon(get_app_icon("new_issue.svg"))
        self.btn_nav_new.clicked.connect(lambda: self.switch_screen(1))
        self.nav_btn_group.addButton(self.btn_nav_new, 1)
        layout.addWidget(self.btn_nav_new)

        self.btn_nav_history = QPushButton("  History")
        self.btn_nav_history.setProperty("class", "sidebarNavBtn")
        self.btn_nav_history.setCheckable(True)
        self.btn_nav_history.setIcon(get_app_icon("history.svg"))
        self.btn_nav_history.clicked.connect(lambda: self.switch_screen(3))
        self.nav_btn_group.addButton(self.btn_nav_history, 3)
        layout.addWidget(self.btn_nav_history)

        layout.addStretch()

        # Bottom Provider Status Indicator
        self.status_card = QFrame()
        self.status_card.setObjectName("sidebarStatusCard")
        s_layout = QVBoxLayout(self.status_card)
        s_layout.setContentsMargins(10, 8, 10, 8)
        s_layout.setSpacing(3)

        s_title = QLabel("AI ENGINE")
        s_title.setObjectName("sidebarStatusLabel")
        self.lbl_provider_status = QLabel("Gemini: Ready")
        self.lbl_provider_status.setObjectName("sidebarStatusValue")
        s_layout.addWidget(s_title)
        s_layout.addWidget(self.lbl_provider_status)
        layout.addWidget(self.status_card)

        # Settings button
        self.settings_btn = QPushButton("⚙️ API Settings")
        self.settings_btn.setProperty("class", "sidebarNavBtn")
        self.settings_btn.setIcon(get_app_icon("settings.svg"))
        self.settings_btn.clicked.connect(self._open_settings_dialog)
        layout.addWidget(self.settings_btn)

        return sidebar_frame

    def _connect_signals(self) -> None:
        """Wire all signals across the 4 screens."""
        # Screen 1 -> Screen 2 (preselect problem type)
        self.screen_dashboard.navigate_to_new_issue.connect(self._on_dashboard_navigate_new)
        # Screen 1 -> Screen 4
        self.screen_dashboard.navigate_to_history.connect(lambda: self.switch_screen(3))
        # Screen 1 -> Screen 3 (recent issue inspection)
        self.screen_dashboard.view_session_details.connect(self._open_session_in_analysis)

        # Screen 2 -> Screen 3 (analysis complete)
        self.screen_new_troubleshooting.analysis_completed.connect(self._open_session_in_analysis)
        self.screen_new_troubleshooting.navigate_to_settings.connect(self._open_settings_dialog)

        # Screen 3 -> Screen 1 (back to dashboard)
        self.screen_analysis.navigate_to_dashboard.connect(lambda: self.switch_screen(0))
        # Screen 3 -> Screen 4 (view history)
        self.screen_analysis.navigate_to_history.connect(lambda: self.switch_screen(3))
        # Screen 3 -> Screen 2 (try again / edit)
        self.screen_analysis.try_again_requested.connect(self._on_try_again)

    def switch_screen(self, index: int) -> None:
        """Switch the stacked widget view and sync the sidebar button check states."""
        self.stacked_widget.setCurrentIndex(index)

        # Sync sidebar buttons
        if index == 0:
            self.btn_nav_dashboard.setChecked(True)
            self.screen_dashboard.refresh_dashboard()
        elif index == 1:
            self.btn_nav_new.setChecked(True)
        elif index == 3:
            self.btn_nav_history.setChecked(True)
            self.screen_history.reload_history()
        else:
            # Screen 3 (Analysis) - uncheck all main top nav buttons
            self.nav_btn_group.setExclusive(False)
            self.btn_nav_dashboard.setChecked(False)
            self.btn_nav_new.setChecked(False)
            self.btn_nav_history.setChecked(False)
            self.nav_btn_group.setExclusive(True)

    def _on_dashboard_navigate_new(self, problem_type: str) -> None:
        """Preselect the problem type in Screen 2 and switch view."""
        self.screen_new_troubleshooting.preselect_problem_type(problem_type)
        self.switch_screen(1)

    def _open_session_in_analysis(self, session_id: int) -> None:
        """Load session data into Screen 3 and switch view."""
        self.screen_analysis.load_session(session_id)
        self.switch_screen(2)

    def _on_try_again(self, payload: dict[str, Any]) -> None:
        """Populate Screen 2 with existing inputs and switch view."""
        self.screen_new_troubleshooting.set_inputs(
            language=payload.get("language", "Python"),
            problem_type=payload.get("problem_type", "Automatic Detection"),
            environment=payload.get("environment", "Development"),
            framework=payload.get("framework", ""),
            error_log=payload.get("error_log", ""),
        )
        self.switch_screen(1)

    def _update_sidebar_status(self) -> None:
        """Refresh the sidebar status card according to active provider and key state."""
        effective = settings.get_effective_provider()
        if effective == "demo":
            self.lbl_provider_status.setText("Demo Mode (Offline)")
            self.lbl_provider_status.setStyleSheet("color: #a855f7;")
        elif effective == "gemini":
            if settings.gemini_api_key:
                self.lbl_provider_status.setText("Gemini (Active)")
                self.lbl_provider_status.setStyleSheet("color: #10b981;")
            else:
                self.lbl_provider_status.setText("Gemini (Key Missing)")
                self.lbl_provider_status.setStyleSheet("color: #f59e0b;")
        elif effective == "openai":
            if settings.openai_api_key:
                self.lbl_provider_status.setText("OpenAI (Active)")
                self.lbl_provider_status.setStyleSheet("color: #10b981;")
            else:
                self.lbl_provider_status.setText("OpenAI (Key Missing)")
                self.lbl_provider_status.setStyleSheet("color: #f59e0b;")

    def _open_settings_dialog(self) -> None:
        """Show settings dialog and update sidebar status on close."""
        dlg = SettingsDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self._update_sidebar_status()
