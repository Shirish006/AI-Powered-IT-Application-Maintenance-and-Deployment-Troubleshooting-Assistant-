"""Screen 4 - Troubleshooting History (Search, Filters, Detailed Inspector, & Deletion)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from database.db_manager import DBManager
from modules.languages import list_supported_languages
from ui.widgets import BadgeWidget, CardWidget, EmptyStateWidget, get_app_icon


class HistoryDetailDialog(QDialog):
    """Modal inspection dialog showing the full saved session without calling AI."""

    status_changed = Signal(int, str)  # ID, new status

    def __init__(self, session_data: dict[str, Any], db: DBManager, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.session = session_data
        self.db = db
        self.setWindowTitle(f"Troubleshooting Session Details - #{self.session['id']}")
        self.setMinimumSize(850, 680)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(14)

        # Header summary and badges
        top_layout = QHBoxLayout()
        summary_title = QLabel(f"#{self.session['id']} - {self.session.get('error_summary', '')}")
        summary_title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        summary_title.setWordWrap(True)
        top_layout.addWidget(summary_title)
        top_layout.addStretch()

        # Status editor
        status_lbl = QLabel("Status:")
        status_lbl.setStyleSheet("font-weight: 600;")
        top_layout.addWidget(status_lbl)

        self.status_combo = QComboBox()
        self.status_combo.addItems(["Unresolved", "In Progress", "Solved"])
        self.status_combo.setCurrentText(self.session.get("resolution_status", "Unresolved"))
        self.status_combo.currentTextChanged.connect(self._on_status_changed)
        top_layout.addWidget(self.status_combo)

        main_layout.addLayout(top_layout)

        # Badges row
        badges_layout = QHBoxLayout()
        badges_layout.setSpacing(8)
        self.badge_status = BadgeWidget(
            self.session.get("resolution_status", "Unresolved"),
            self.session.get("resolution_status", "Unresolved"),
        )
        badges_layout.addWidget(self.badge_status)
        badges_layout.addWidget(BadgeWidget(self.session.get("programming_language", ""), "neutral"))
        badges_layout.addWidget(BadgeWidget(self.session.get("problem_type", ""), "neutral"))
        badges_layout.addWidget(BadgeWidget(self.session.get("environment", ""), "neutral"))
        badges_layout.addWidget(BadgeWidget(self.session.get("error_category", ""), "neutral"))
        badges_layout.addWidget(
            BadgeWidget(f"Severity: {self.session.get('severity', '')}", self.session.get("severity", "Medium"))
        )
        badges_layout.addStretch()
        main_layout.addLayout(badges_layout)

        # Scroll area for details
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_content = QWidget()
        content_layout = QVBoxLayout(scroll_content)
        content_layout.setSpacing(14)

        # Explanation
        c_exp = CardWidget(title="AI Error Explanation")
        lbl_exp = QLabel(self.session.get("error_explanation", ""))
        lbl_exp.setWordWrap(True)
        lbl_exp.setStyleSheet("color: #334155; font-size: 13px; line-height: 1.4;")
        c_exp.layout_box.addWidget(lbl_exp)
        content_layout.addWidget(c_exp)

        # Confirmed Facts vs Possible Causes
        c_fc = CardWidget(title="Confirmed Facts & Possible Causes")
        facts = self.session.get("confirmed_facts", [])
        causes = self.session.get("possible_causes", [])
        facts_text = "\n".join(f"• {f}" for f in facts) if facts else "None"
        causes_text = "\n".join(f"• {c}" for c in causes) if causes else "None"

        lbl_fc = QLabel(f"<b>Confirmed Facts:</b>\n{facts_text}\n\n<b>Possible Hypotheses:</b>\n{causes_text}")
        lbl_fc.setWordWrap(True)
        lbl_fc.setStyleSheet("color: #475569; font-size: 12px;")
        c_fc.layout_box.addWidget(lbl_fc)
        content_layout.addWidget(c_fc)

        # Troubleshooting Steps
        c_steps = CardWidget(title="Troubleshooting Instructions")
        steps = self.session.get("troubleshooting_steps", [])
        steps_formatted = "\n\n".join(f"{i}. {s.lstrip('0123456789.- ')}" for i, s in enumerate(steps, 1)) if steps else "None"
        lbl_steps = QLabel(steps_formatted)
        lbl_steps.setWordWrap(True)
        lbl_steps.setStyleSheet("color: #1e293b; font-size: 13px; line-height: 1.5;")
        c_steps.layout_box.addWidget(lbl_steps)
        content_layout.addWidget(c_steps)

        # Suggested Solution
        c_sol = CardWidget(title="Suggested Solution")
        txt_sol = QTextEdit()
        txt_sol.setReadOnly(True)
        txt_sol.setPlainText(self.session.get("suggested_solution", ""))
        txt_sol.setStyleSheet("font-family: Consolas, monospace; background-color: #f8fafc;")
        txt_sol.setMaximumHeight(140)
        c_sol.layout_box.addWidget(txt_sol)
        content_layout.addWidget(c_sol)

        # Verification Steps
        c_ver = CardWidget(title="Verification Steps")
        vsteps = self.session.get("verification_steps", [])
        v_formatted = "\n\n".join(f"{i}. {v.lstrip('0123456789.- ')}" for i, v in enumerate(vsteps, 1)) if vsteps else "None"
        lbl_ver = QLabel(v_formatted)
        lbl_ver.setWordWrap(True)
        lbl_ver.setStyleSheet("color: #1e293b; font-size: 13px;")
        c_ver.layout_box.addWidget(lbl_ver)
        content_layout.addWidget(c_ver)

        # Original Log
        c_log = CardWidget(title="Original Redacted Error Log")
        txt_log = QTextEdit()
        txt_log.setReadOnly(True)
        txt_log.setPlainText(self.session.get("original_error_log", ""))
        txt_log.setStyleSheet("font-family: Consolas, monospace; background-color: #0f172a; color: #f8fafc;")
        txt_log.setMaximumHeight(120)
        c_log.layout_box.addWidget(txt_log)
        content_layout.addWidget(c_log)

        scroll.setWidget(scroll_content)
        main_layout.addWidget(scroll)

        # Close button
        btn_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        btn_box.rejected.connect(self.reject)
        main_layout.addWidget(btn_box)

    def _on_status_changed(self, new_status: str) -> None:
        """Update status directly in SQLite."""
        session_id = self.session["id"]
        try:
            self.db.update_status(session_id, new_status)
            self.session["resolution_status"] = new_status
            self.badge_status.set_badge(new_status, new_status)
            self.status_changed.emit(session_id, new_status)
        except Exception as e:
            QMessageBox.critical(self, "Update Failed", f"Could not update status: {e}")


class HistoryScreen(QWidget):
    """Full-featured history log with parameterized search, multiple filters, and inspection."""

    view_session_requested = Signal(int)  # Session ID

    def __init__(self, db_manager: DBManager, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.db = db_manager

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(28, 28, 28, 28)
        main_layout.setSpacing(16)

        # 1. Header
        header_layout = QHBoxLayout()
        title_box = QVBoxLayout()
        title_box.setSpacing(4)
        title = QLabel("Troubleshooting History")
        title.setProperty("class", "screenTitle")
        subtitle = QLabel("Search, inspect, and manage persistent diagnostic logs and verified resolutions")
        subtitle.setProperty("class", "screenSubtitle")
        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        header_layout.addLayout(title_box)

        header_layout.addStretch()

        self.refresh_btn = QPushButton("🔄 Refresh")
        self.refresh_btn.setProperty("class", "secondaryBtn")
        self.refresh_btn.clicked.connect(self.reload_history)
        header_layout.addWidget(self.refresh_btn)

        main_layout.addLayout(header_layout)

        # 2. Search & Filters Card
        filter_card = CardWidget()
        f_layout = filter_card.layout_box

        f_grid = QHBoxLayout()
        f_grid.setSpacing(10)

        # Search Bar
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search error text, summary, category, framework...")
        self.search_input.setClearButtonEnabled(True)
        self.search_input.textChanged.connect(self.reload_history)
        f_grid.addWidget(self.search_input, stretch=2)

        # Language Filter
        lbl_lang = QLabel("Language:")
        lbl_lang.setStyleSheet("font-weight: 500; color: #64748b;")
        f_grid.addWidget(lbl_lang)
        self.filter_lang = QComboBox()
        self.filter_lang.addItem("All")
        self.filter_lang.addItems(list_supported_languages())
        self.filter_lang.currentTextChanged.connect(self.reload_history)
        f_grid.addWidget(self.filter_lang)

        # Problem Type Filter
        lbl_type = QLabel("Type:")
        lbl_type.setStyleSheet("font-weight: 500; color: #64748b;")
        f_grid.addWidget(lbl_type)
        self.filter_type = QComboBox()
        self.filter_type.addItems(["All", "Maintenance", "Deployment"])
        self.filter_type.currentTextChanged.connect(self.reload_history)
        f_grid.addWidget(self.filter_type)

        # Status Filter
        lbl_status = QLabel("Status:")
        lbl_status.setStyleSheet("font-weight: 500; color: #64748b;")
        f_grid.addWidget(lbl_status)
        self.filter_status = QComboBox()
        self.filter_status.addItems(["All", "Unresolved", "In Progress", "Solved"])
        self.filter_status.currentTextChanged.connect(self.reload_history)
        f_grid.addWidget(self.filter_status)

        f_layout.addLayout(f_grid)
        main_layout.addWidget(filter_card)

        # 3. History Table & Empty States
        table_card = CardWidget()
        t_layout = table_card.layout_box

        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "ID",
            "Date / Time",
            "Language",
            "Problem Type",
            "Environment",
            "Error Category",
            "Error Summary",
            "Status",
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.cellDoubleClicked.connect(self._on_row_double_clicked)
        t_layout.addWidget(self.table)

        # Empty state widgets
        self.empty_state_none = EmptyStateWidget(
            title="No Troubleshooting History",
            description="Run your first troubleshooting session to see persistent diagnostic records here.",
        )
        t_layout.addWidget(self.empty_state_none)

        self.empty_state_filtered = EmptyStateWidget(
            title="No Matching Records",
            description="No sessions match the current search query and filter criteria.",
            action_text="Reset Filters",
            action_callback=self._reset_filters,
        )
        t_layout.addWidget(self.empty_state_filtered)

        # Action Buttons under Table
        action_bar = QHBoxLayout()
        action_bar.setSpacing(10)

        self.view_details_btn = QPushButton("👁️ View Full Details")
        self.view_details_btn.setProperty("class", "primaryBtn")
        self.view_details_btn.clicked.connect(self._on_view_details_clicked)
        action_bar.addWidget(self.view_details_btn)

        self.delete_btn = QPushButton("🗑️ Delete Record")
        self.delete_btn.setProperty("class", "dangerBtn")
        self.delete_btn.clicked.connect(self._on_delete_clicked)
        action_bar.addWidget(self.delete_btn)

        action_bar.addStretch()

        self.export_selected_btn = QPushButton("💾 Export Report...")
        self.export_selected_btn.setProperty("class", "secondaryBtn")
        self.export_selected_btn.clicked.connect(self._on_export_selected_clicked)
        action_bar.addWidget(self.export_selected_btn)

        t_layout.addLayout(action_bar)
        main_layout.addWidget(table_card)

        # Initial load
        self.reload_history()

    def _reset_filters(self) -> None:
        """Reset search and filter dropdowns."""
        self.search_input.clear()
        self.filter_lang.setCurrentIndex(0)
        self.filter_type.setCurrentIndex(0)
        self.filter_status.setCurrentIndex(0)

    def reload_history(self) -> None:
        """Query SQLite with active search term and filters."""
        search = self.search_input.text().strip()
        lang = self.filter_lang.currentText()
        ptype = self.filter_type.currentText()
        status = self.filter_status.currentText()

        records = self.db.list_sessions(
            search=search if search else None,
            language=lang,
            problem_type=ptype,
            status=status,
            limit=200,
        )

        total_in_db = self.db.counts_by_status().get("total", 0)

        if total_in_db == 0:
            self.table.hide()
            self.empty_state_filtered.hide()
            self.empty_state_none.show()
            self.view_details_btn.setEnabled(False)
            self.delete_btn.setEnabled(False)
            self.export_selected_btn.setEnabled(False)
            return

        if not records:
            self.table.hide()
            self.empty_state_none.hide()
            self.empty_state_filtered.show()
            self.view_details_btn.setEnabled(False)
            self.delete_btn.setEnabled(False)
            self.export_selected_btn.setEnabled(False)
            return

        self.empty_state_none.hide()
        self.empty_state_filtered.hide()
        self.table.show()
        self.view_details_btn.setEnabled(True)
        self.delete_btn.setEnabled(True)
        self.export_selected_btn.setEnabled(True)

        self.table.setRowCount(len(records))

        for row, item in enumerate(records):
            # ID
            id_item = QTableWidgetItem(f"#{item['id']}")
            id_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 0, id_item)

            # Date/Time
            dt_str = item.get("timestamp", "")
            if "T" in dt_str:
                dt_str = dt_str.replace("T", " ")[:16]
            self.table.setItem(row, 1, QTableWidgetItem(dt_str))

            # Language
            self.table.setItem(row, 2, QTableWidgetItem(item.get("programming_language", "")))

            # Problem Type
            prob_type = item.get("problem_type", "")
            if item.get("detected_problem_type") and item.get("problem_type") == "Automatic Detection":
                prob_type = f"{item['detected_problem_type']} (auto)"
            self.table.setItem(row, 3, QTableWidgetItem(prob_type))

            # Environment
            self.table.setItem(row, 4, QTableWidgetItem(item.get("environment", "")))

            # Category
            self.table.setItem(row, 5, QTableWidgetItem(item.get("error_category", "")))

            # Summary
            self.table.setItem(row, 6, QTableWidgetItem(item.get("error_summary", "")))

            # Status Badge
            status_text = item.get("resolution_status", "Unresolved")
            badge = BadgeWidget(status_text, status_text)
            self.table.setCellWidget(row, 7, badge)

    def _get_selected_session_id(self) -> int | None:
        """Return the integer ID of the currently selected row, or None."""
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            return None
        row = selected_rows[0].row()
        id_item = self.table.item(row, 0)
        if not id_item:
            return None
        try:
            return int(id_item.text().replace("#", ""))
        except ValueError:
            return None

    def _on_row_double_clicked(self, row: int, col: int) -> None:
        """Double click opens details dialog."""
        id_item = self.table.item(row, 0)
        if id_item:
            try:
                session_id = int(id_item.text().replace("#", ""))
                self._open_details_dialog(session_id)
            except ValueError:
                pass

    def _on_view_details_clicked(self) -> None:
        """Button click opens details dialog."""
        session_id = self._get_selected_session_id()
        if session_id is None:
            QMessageBox.information(self, "No Selection", "Please select a row in the table to view its details.")
            return
        self._open_details_dialog(session_id)

    def _open_details_dialog(self, session_id: int) -> None:
        """Retrieve complete session from SQLite and show inspection dialog."""
        session = self.db.get_session(session_id)
        if not session:
            QMessageBox.warning(self, "Not Found", f"Session #{session_id} not found.")
            return
        dlg = HistoryDetailDialog(session, self.db, self)
        dlg.status_changed.connect(lambda sid, status: self.reload_history())
        dlg.exec()

    def _on_delete_clicked(self) -> None:
        """Delete selected session with confirmation."""
        session_id = self._get_selected_session_id()
        if session_id is None:
            QMessageBox.information(self, "No Selection", "Please select a row to delete.")
            return

        reply = QMessageBox.question(
            self,
            "Confirm Deletion",
            f"Are you sure you want to permanently delete troubleshooting session #{session_id}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.db.delete_session(session_id)
                self.reload_history()
                QMessageBox.information(self, "Deleted", f"Session #{session_id} deleted successfully.")
            except Exception as e:
                QMessageBox.critical(self, "Delete Failed", f"Could not delete session: {e}")

    def _on_export_selected_clicked(self) -> None:
        """Export selected record to markdown file."""
        session_id = self._get_selected_session_id()
        if session_id is None:
            QMessageBox.information(self, "No Selection", "Please select a row to export.")
            return

        session = self.db.get_session(session_id)
        if not session:
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Session Report",
            f"troubleshooting_session_{session['id']}.md",
            "Markdown Files (*.md);;Text Files (*.txt)",
        )
        if not file_path:
            return

        facts_md = "\n".join(f"- {f}" for f in session.get("confirmed_facts", []))
        causes_md = "\n".join(f"- {c}" for c in session.get("possible_causes", []))
        steps_md = "\n".join(f"{i}. {step}" for i, step in enumerate(session.get("troubleshooting_steps", []), 1))
        vsteps_md = "\n".join(f"{i}. {v}" for i, v in enumerate(session.get("verification_steps", []), 1))

        content = f"""# AI IT Troubleshooting Report - Session #{session['id']}

- **Date / Time:** {session.get('timestamp', '')}
- **Language:** {session.get('programming_language', '')}
- **Problem Type:** {session.get('problem_type', '')} (Detected: {session.get('detected_problem_type', '')})
- **Environment:** {session.get('environment', '')}
- **Framework:** {session.get('application_framework', 'N/A')}
- **Category:** {session.get('error_category', '')}
- **Severity:** {session.get('severity', '')}
- **Status:** {session.get('resolution_status', '')}

## Error Summary
{session.get('error_summary', '')}

## Explanation
{session.get('error_explanation', '')}

## Confirmed Facts
{facts_md}

## Possible Causes
{causes_md}

## Troubleshooting Steps
{steps_md}

## Suggested Solution
```
{session.get('suggested_solution', '')}
```

## Verification Steps
{vsteps_md}

## Original Redacted Log
```
{session.get('original_error_log', '')}
```
"""
        try:
            Path(file_path).write_text(content, encoding="utf-8")
            QMessageBox.information(self, "Exported", f"Exported session report to:\n{file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Export Failed", f"Could not write file: {e}")
