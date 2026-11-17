"""Reusable UI components: Cards, Badges, Stat Cards, and Loading Overlay."""

from __future__ import annotations

from typing import Any, Callable

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QFont, QIcon, QPainter
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from config.settings import get_resource_path


def get_app_icon(name: str) -> QIcon:
    """Load an icon safely from assets/icons; fallback to empty QIcon if missing."""
    icon_path = get_resource_path(f"assets/icons/{name}")
    if icon_path.exists():
        return QIcon(str(icon_path))
    return QIcon()


class CardWidget(QFrame):
    """Clean rounded card container."""

    def __init__(self, title: str | None = None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setProperty("class", "cardFrame")
        self.layout_box = QVBoxLayout(self)
        self.layout_box.setContentsMargins(16, 16, 16, 16)
        self.layout_box.setSpacing(10)

        if title:
            self.title_label = QLabel(title)
            self.title_label.setProperty("class", "sectionHeading")
            self.layout_box.addWidget(self.title_label)


class BadgeWidget(QLabel):
    """Pill badge for color-coded severity, status, or category."""

    def __init__(self, text: str, badge_type: str = "neutral", parent: QWidget | None = None) -> None:
        super().__init__(text, parent)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.set_badge(text, badge_type)

    def set_badge(self, text: str, badge_type: str) -> None:
        """Update badge text and visual class."""
        self.setText(f"  {text}  ")
        normalized = badge_type.lower().replace(" ", "-")
        self.setProperty("class", f"badge badge-{normalized}")
        self.style().unpolish(self)
        self.style().polish(self)


class StatCard(QFrame):
    """Metric card showing a large number and a descriptive label."""

    def __init__(self, label: str, initial_value: str | int = 0, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setProperty("class", "statCard")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(4)

        self.val_label = QLabel(str(initial_value))
        self.val_label.setProperty("class", "statValue")
        self.desc_label = QLabel(label)
        self.desc_label.setProperty("class", "statLabel")

        layout.addWidget(self.val_label)
        layout.addWidget(self.desc_label)

    def set_value(self, value: str | int) -> None:
        self.val_label.setText(str(value))


class LoadingOverlay(QWidget):
    """Semi-transparent modal overlay shown during AI processing."""

    cancelled = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)

        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Dialog-like centered box
        card = QFrame()
        card.setProperty("class", "cardFrame")
        card.setMinimumWidth(360)
        card.setMaximumWidth(450)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(24, 24, 24, 24)
        card_layout.setSpacing(14)
        card_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        title = QLabel("Analyzing Error")
        title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(title)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # Indeterminate spinner/bounce
        self.progress_bar.setFixedHeight(8)
        self.progress_bar.setTextVisible(False)
        card_layout.addWidget(self.progress_bar)

        self.status_label = QLabel("Initializing analysis...")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("color: #64748b; font-size: 12px;")
        self.status_label.setWordWrap(True)
        card_layout.addWidget(self.status_label)

        self.cancel_btn = QPushButton("Cancel Request")
        self.cancel_btn.setProperty("class", "secondaryBtn")
        self.cancel_btn.clicked.connect(self.cancelled.emit)
        card_layout.addWidget(self.cancel_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        main_layout.addWidget(card)
        self.hide()

    def set_message(self, message: str) -> None:
        """Update the progress text."""
        self.status_label.setText(message)

    def paintEvent(self, event: Any) -> None:
        """Dim background with semi-transparent dark shade."""
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(15, 23, 42, 140))
        super().paintEvent(event)


class EmptyStateWidget(QWidget):
    """Friendly empty state display with icon, title, description, and optional action."""

    def __init__(
        self,
        title: str,
        description: str,
        action_text: str | None = None,
        action_callback: Callable[[], None] | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setContentsMargins(20, 40, 20, 40)
        layout.setSpacing(10)

        title_lbl = QLabel(title)
        title_lbl.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        title_lbl.setStyleSheet("color: #475569;")
        title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_lbl)

        desc_lbl = QLabel(description)
        desc_lbl.setStyleSheet("color: #94a3b8; font-size: 12px;")
        desc_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc_lbl.setWordWrap(True)
        layout.addWidget(desc_lbl)

        if action_text and action_callback:
            btn = QPushButton(action_text)
            btn.setProperty("class", "primaryBtn")
            btn.clicked.connect(action_callback)
            layout.addWidget(btn, alignment=Qt.AlignmentFlag.AlignCenter)
