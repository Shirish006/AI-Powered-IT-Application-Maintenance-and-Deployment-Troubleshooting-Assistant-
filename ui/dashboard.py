"""Screen 1 - Dashboard (Home Screen)."""

from __future__ import annotations

from typing import Any, Callable

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QScrollArea,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from database.db_manager import DBManager
from ui.widgets import BadgeWidget, CardWidget, EmptyStateWidget, StatCard, get_app_icon


class DashboardScreen(QWidget):
    """Main landing screen offering quick actions, metrics, and recent issues."""

    # Navigation signals
    navigate_to_new_issue = Signal(str)  # Problem type to preselect: "Automatic Detection", "Maintenance", "Deployment"
    navigate_to_history = Signal()
    view_session_details = Signal(int)  # Session ID

    def __init__(self, db_manager: DBManager, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.db = db_manager

        # Root scrollable layout
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        self.container = QWidget()
        self.main_layout = QVBoxLayout(self.container)
        self.main_layout.setContentsMargins(28, 28, 28, 28)
        self.main_layout.setSpacing(20)

        # 1. Header
        header_layout = QVBoxLayout()
        header_layout.setSpacing(4)
        title = QLabel("AI IT Troubleshooting Assistant")
        title.setProperty("class", "screenTitle")
        subtitle = QLabel("AI-Powered diagnosis for Application Maintenance and Deployment failures")
        subtitle.setProperty("class", "screenSubtitle")
        header_layout.addWidget(title)
        header_layout.addWidget(subtitle)
        self.main_layout.addLayout(header_layout)

        # 2. Metric Counters
        metrics_layout = QHBoxLayout()
        metrics_layout.setSpacing(14)
        self.stat_total = StatCard("Total Analyzed", 0)
        self.stat_unresolved = StatCard("Unresolved", 0)
        self.stat_in_progress = StatCard("In Progress", 0)
        self.stat_solved = StatCard("Solved", 0)

        metrics_layout.addWidget(self.stat_total)
        metrics_layout.addWidget(self.stat_unresolved)
        metrics_layout.addWidget(self.stat_in_progress)
        metrics_layout.addWidget(self.stat_solved)
        self.main_layout.addLayout(metrics_layout)

        # 3. Quick Action Cards
        actions_heading = QLabel("Quick Actions")
        actions_heading.setProperty("class", "sectionHeading")
        self.main_layout.addWidget(actions_heading)

        actions_grid = QGridLayout()
        actions_grid.setSpacing(14)

        card_new = self._create_action_card(
            title="New Troubleshooting",
            desc="Analyze error logs with automatic Maintenance / Deployment detection",
            icon_name="new_issue.svg",
            callback=lambda: self.navigate_to_new_issue.emit("Automatic Detection"),
        )
        card_history = self._create_action_card(
            title="Troubleshooting History",
            desc="Browse, search, and review previously resolved errors & solutions",
            icon_name="history.svg",
            callback=self.navigate_to_history.emit,
        )
        card_maint = self._create_action_card(
            title="Application Maintenance",
            desc="Directly diagnose syntax, runtime bugs, and logical application code issues",
            icon_name="maintenance.svg",
            callback=lambda: self.navigate_to_new_issue.emit("Maintenance"),
        )
        card_deploy = self._create_action_card(
            title="Application Deployment",
            desc="Directly troubleshoot Docker, container, dependency, and environment errors",
            icon_name="deployment.svg",
            callback=lambda: self.navigate_to_new_issue.emit("Deployment"),
        )

        actions_grid.addWidget(card_new, 0, 0)
        actions_grid.addWidget(card_maint, 0, 1)
        actions_grid.addWidget(card_deploy, 1, 0)
        actions_grid.addWidget(card_history, 1, 1)
        self.main_layout.addLayout(actions_grid)

        # 4. Recent Issues Section
        recent_card = CardWidget()
        recent_card_layout = recent_card.layout_box

        recent_header = QHBoxLayout()
        recent_title = QLabel("Recent Issues")
        recent_title.setProperty("class", "sectionHeading")
        recent_header.addWidget(recent_title)

        recent_header.addStretch()

        view_all_btn = QPushButton("View Full History →")
        view_all_btn.setProperty("class", "secondaryBtn")
        view_all_btn.clicked.connect(self.navigate_to_history.emit)
        recent_header.addWidget(view_all_btn)
        recent_card_layout.addLayout(recent_header)

        # Table for recent issues
        self.recent_table = QTableWidget()
        self.recent_table.setColumnCount(7)
        self.recent_table.setHorizontalHeaderLabels([
            "ID",
            "Date / Time",
            "Language",
            "Problem Type",
            "Category",
            "Error Summary",
            "Status",
        ])
        self.recent_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.recent_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)
        self.recent_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.recent_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.recent_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.recent_table.verticalHeader().setVisible(False)
        self.recent_table.setMinimumHeight(240)
        self.recent_table.cellDoubleClicked.connect(self._on_row_double_clicked)
        recent_card_layout.addWidget(self.recent_table)

        # Empty state container
        self.empty_state = EmptyStateWidget(
            title="No Troubleshooting Sessions Yet",
            description="Start diagnosing an error log or code issue using the Quick Actions above.",
            action_text="+ Analyze First Problem",
            action_callback=lambda: self.navigate_to_new_issue.emit("Automatic Detection"),
        )
        recent_card_layout.addWidget(self.empty_state)

        self.main_layout.addWidget(recent_card)
        self.main_layout.addStretch()

        # Set up root layout
        scroll.setWidget(self.container)
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.addWidget(scroll)

        # Load initial data
        self.refresh_dashboard()

    def _create_action_card(self, title: str, desc: str, icon_name: str, callback: Callable[[], None]) -> QPushButton:
        """Create a stylized clickable card button."""
        btn = QPushButton()
        btn.setProperty("class", "actionCardBtn")
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.clicked.connect(callback)

        layout = QHBoxLayout(btn)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(14)

        icon_lbl = QLabel()
        icon = get_app_icon(icon_name)
        if not icon.isNull():
            icon_lbl.setPixmap(icon.pixmap(32, 32))
        icon_lbl.setFixedSize(36, 36)
        layout.addWidget(icon_lbl)

        text_layout = QVBoxLayout()
        text_layout.setSpacing(4)
        t_lbl = QLabel(title)
        t_lbl.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        t_lbl.setStyleSheet("color: #0f172a;")
        d_lbl = QLabel(desc)
        d_lbl.setStyleSheet("color: #64748b; font-size: 11px;")
        d_lbl.setWordWrap(True)
        text_layout.addWidget(t_lbl)
        text_layout.addWidget(d_lbl)
        layout.addLayout(text_layout)

        layout.addStretch()
        return btn

    def refresh_dashboard(self) -> None:
        """Fetch latest counts and recent sessions from SQLite and refresh the UI."""
        counts = self.db.counts_by_status()
        self.stat_total.set_value(counts.get("total", 0))
        self.stat_unresolved.set_value(counts.get("unresolved", 0))
        self.stat_in_progress.set_value(counts.get("in_progress", 0))
        self.stat_solved.set_value(counts.get("solved", 0))

        recent_items = self.db.recent_sessions(limit=8)

        if not recent_items:
            self.recent_table.hide()
            self.empty_state.show()
            return

        self.empty_state.hide()
        self.recent_table.show()
        self.recent_table.setRowCount(len(recent_items))

        for row, item in enumerate(recent_items):
            # ID
            id_item = QTableWidgetItem(f"#{item['id']}")
            id_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.recent_table.setItem(row, 0, id_item)

            # Date/Time
            dt_str = item.get("timestamp", "")
            if "T" in dt_str:
                dt_str = dt_str.replace("T", " ")[:16]
            self.recent_table.setItem(row, 1, QTableWidgetItem(dt_str))

            # Language
            self.recent_table.setItem(row, 2, QTableWidgetItem(item.get("programming_language", "")))

            # Problem Type
            prob_type = item.get("problem_type", "")
            if item.get("detected_problem_type") and item.get("problem_type") == "Automatic Detection":
                prob_type = f"{item['detected_problem_type']} (auto)"
            self.recent_table.setItem(row, 3, QTableWidgetItem(prob_type))

            # Category
            self.recent_table.setItem(row, 4, QTableWidgetItem(item.get("error_category", "")))

            # Summary
            summary_item = QTableWidgetItem(item.get("error_summary", ""))
            self.recent_table.setItem(row, 5, summary_item)

            # Status Badge
            status_text = item.get("resolution_status", "Unresolved")
            badge = BadgeWidget(status_text, status_text)
            self.recent_table.setCellWidget(row, 6, badge)

    def _on_row_double_clicked(self, row: int, col: int) -> None:
        """Handle double-click on a recent issue row to open its details."""
        id_item = self.recent_table.item(row, 0)
        if id_item:
            session_id_str = id_item.text().replace("#", "")
            try:
                session_id = int(session_id_str)
                self.view_session_details.emit(session_id)
            except ValueError:
                pass
