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
    QRadioButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from config.settings import WINDOW_TITLE, settings
from database.db_manager import DBManager
from services.ai_service import AIService
from ui.analysis_screen import AnalysisScreen
from ui.dashboard import DashboardScreen
from ui.history_screen import HistoryScreen
from ui.new_troubleshooting import NewTroubleshootingScreen
from ui.widgets import get_app_icon


class SettingsDialog(QDialog):
    """Configuration dialog for switching between Online (Gemini AI) and Offline mode."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Operation Mode")
        self.setMinimumWidth(440)
        self.setModal(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        title = QLabel("Troubleshooting Mode")
        title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        layout.addWidget(title)

        desc = QLabel(
            "Select how you want the troubleshooting engine to operate.\n"
            "Online mode uses Google Gemini AI (Free). Offline mode runs 100% locally on your machine."
        )
        desc.setStyleSheet("color: #64748b; font-size: 12px;")
        desc.setWordWrap(True)
        layout.addWidget(desc)

        # Mode Selection
        self.radio_online = QRadioButton("🟢 Online Mode (Google Gemini AI - Free)")
        self.radio_online.setStyleSheet("font-size: 13px; font-weight: 600; padding: 6px 0;")
        self.radio_offline = QRadioButton("⚡ Offline Mode (Local Diagnostic Engine)")
        self.radio_offline.setStyleSheet("font-size: 13px; font-weight: 600; padding: 6px 0;")

        is_offline = settings.demo_mode_forced or settings.ai_provider == "demo"
        if is_offline:
            self.radio_offline.setChecked(True)
        else:
            self.radio_online.setChecked(True)

        layout.addWidget(self.radio_online)
        layout.addWidget(self.radio_offline)

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

    def _save_settings(self) -> None:
        """Persist mode settings."""
        if self.radio_online.isChecked():
            settings.ai_provider = "gemini"
            settings.demo_mode_forced = False
        else:
            settings.ai_provider = "demo"
            settings.demo_mode_forced = True

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

        # Bottom Mode Selector (Offline vs Online)
        self.mode_card = QFrame()
        self.mode_card.setObjectName("sidebarStatusCard")
        m_layout = QVBoxLayout(self.mode_card)
        m_layout.setContentsMargins(10, 10, 10, 10)
        m_layout.setSpacing(6)

        m_title = QLabel("TROUBLESHOOTING MODE")
        m_title.setObjectName("sidebarStatusLabel")
        m_layout.addWidget(m_title)

        self.mode_combo = QComboBox()
        self.mode_combo.setObjectName("sidebarModeCombo")
        self.mode_combo.addItems(["🟢 Online (Gemini AI)", "⚡ Offline (Local Mode)"])
        self.mode_combo.setStyleSheet("""
            QComboBox#sidebarModeCombo {
                background-color: #0f172a;
                color: #f8fafc;
                border: 1px solid #334155;
                border-radius: 6px;
                padding: 6px 10px;
                font-size: 12px;
                font-weight: 500;
            }
            QComboBox#sidebarModeCombo:hover {
                border-color: #38bdf8;
            }
            QComboBox#sidebarModeCombo::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox#sidebarModeCombo QAbstractItemView {
                background-color: #1e293b;
                color: #f8fafc;
                selection-background-color: #2563eb;
                selection-color: #ffffff;
                border: 1px solid #334155;
                outline: none;
            }
        """)

        is_offline = settings.demo_mode_forced or settings.ai_provider == "demo"
        self.mode_combo.setCurrentIndex(1 if is_offline else 0)
        self.mode_combo.currentIndexChanged.connect(self._on_sidebar_mode_changed)
        m_layout.addWidget(self.mode_combo)

        self.lbl_provider_status = QLabel("Gemini: Active (Free)" if not is_offline else "Offline Mode (Local)")
        self.lbl_provider_status.setObjectName("sidebarStatusValue")
        self.lbl_provider_status.setStyleSheet("color: #10b981;" if not is_offline else "color: #a855f7;")
        m_layout.addWidget(self.lbl_provider_status)

        layout.addWidget(self.mode_card)

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

    def _on_sidebar_mode_changed(self, index: int) -> None:
        """Handle user changing the mode dropdown in the sidebar."""
        if index == 0:  # Online
            settings.ai_provider = "gemini"
            settings.demo_mode_forced = False
            self.lbl_provider_status.setText("Gemini: Active (Free)")
            self.lbl_provider_status.setStyleSheet("color: #10b981;")
        else:  # Offline
            settings.ai_provider = "demo"
            settings.demo_mode_forced = True
            self.lbl_provider_status.setText("Offline Mode (Local)")
            self.lbl_provider_status.setStyleSheet("color: #a855f7;")
        settings.save_preferences()

    def _update_sidebar_status(self) -> None:
        """Refresh the sidebar status according to active provider."""
        is_offline = settings.demo_mode_forced or settings.ai_provider == "demo"
        if hasattr(self, "mode_combo"):
            self.mode_combo.blockSignals(True)
            self.mode_combo.setCurrentIndex(1 if is_offline else 0)
            self.mode_combo.blockSignals(False)
        if hasattr(self, "lbl_provider_status"):
            if is_offline:
                self.lbl_provider_status.setText("Offline Mode (Local)")
                self.lbl_provider_status.setStyleSheet("color: #a855f7;")
            else:
                self.lbl_provider_status.setText("Gemini: Active (Free)")
                self.lbl_provider_status.setStyleSheet("color: #10b981;")

    def _open_settings_dialog(self) -> None:
        """Show settings dialog and update sidebar status on close."""
        dlg = SettingsDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self._update_sidebar_status()
