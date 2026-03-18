"""
Reusable UI components: HeaderWidget, SidebarWidget, StatCard, etc.
Designed to match the Stitch design mockups for SLTCFPDI.
"""
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton,
    QFrame, QSizePolicy, QSpacerItem, QLineEdit, QTableWidget,
    QHeaderView, QAbstractItemView
)
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QPixmap, QIcon, QFont
import os
from config import LOGO_PATH, SCHOOL_NAME, COLOR_PRIMARY


class HeaderWidget(QWidget):
    """Blue header bar matching Stitch design — logo + school name + page title."""

    theme_toggled = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("headerWidget")
        self.setFixedHeight(70)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 0, 20, 0)
        layout.setSpacing(12)

        # School logo
        self.logo_label = QLabel()
        if os.path.exists(LOGO_PATH):
            pixmap = QPixmap(LOGO_PATH)
            self.logo_label.setPixmap(pixmap.scaled(
                40, 40, Qt.KeepAspectRatio, Qt.SmoothTransformation
            ))
        self.logo_label.setFixedSize(40, 40)
        layout.addWidget(self.logo_label)

        # Title section
        title_layout = QVBoxLayout()
        title_layout.setSpacing(0)
        title_layout.setContentsMargins(0, 0, 0, 0)

        self.title_label = QLabel(f"{SCHOOL_NAME} — Scheduling Automation Program")
        self.title_label.setObjectName("headerTitle")
        title_layout.addWidget(self.title_label)

        self.subtitle_label = QLabel("Automated Class Scheduling System")
        self.subtitle_label.setObjectName("headerSubtitle")
        title_layout.addWidget(self.subtitle_label)

        layout.addLayout(title_layout)
        layout.addStretch()

        # User info area (right side)
        self.user_label = QLabel("Admin")
        self.user_label.setStyleSheet("color: rgba(255,255,255,0.9); font-size: 13px;")
        layout.addWidget(self.user_label)

        # Theme toggle button
        self.theme_btn = QPushButton("🌙")
        self.theme_btn.setStyleSheet("""
            QPushButton { background: transparent; border: none; font-size: 16px; padding: 4px; }
            QPushButton:hover { background: rgba(255,255,255,0.2); border-radius: 4px; }
        """)
        self.theme_btn.setCursor(Qt.PointingHandCursor)
        self.theme_btn.clicked.connect(self.theme_toggled.emit)
        layout.addWidget(self.theme_btn)

    def set_user(self, name: str):
        self.user_label.setText(name)


class SidebarWidget(QWidget):
    """Left navigation sidebar with page buttons."""

    navigation_requested = Signal(str)

    PAGES = [
        ("dashboard", "Dashboard", "📊"),
        ("teachers", "Teachers", "👨‍🏫"),
        ("requirements", "Requirements", "📋"),
        ("schedule", "Schedule", "📅"),
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("sidebarWidget")
        self.setFixedWidth(220)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 20, 12, 20)
        layout.setSpacing(4)

        # Navigation label
        nav_label = QLabel("NAVIGATION")
        nav_label.setStyleSheet(
            "color: #94a3b8; font-size: 10px; font-weight: 700; "
            "letter-spacing: 1px; padding: 8px 16px;"
        )
        layout.addWidget(nav_label)

        # Navigation buttons
        self.buttons = {}
        for key, label, icon in self.PAGES:
            btn = QPushButton(f"  {icon}  {label}")
            btn.setProperty("class", "sidebarBtn")
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(lambda checked, k=key: self._on_clicked(k))
            layout.addWidget(btn)
            self.buttons[key] = btn

        layout.addStretch()

        # Logout button at bottom
        logout_btn = QPushButton("  🚪  Logout")
        logout_btn.setProperty("class", "sidebarBtn")
        logout_btn.setCursor(Qt.PointingHandCursor)
        logout_btn.setStyleSheet(
            "QPushButton { color: #ef4444; } "
            "QPushButton:hover { background-color: #fef2f2; color: #dc2626; }"
        )
        logout_btn.clicked.connect(lambda: self.navigation_requested.emit("logout"))
        layout.addWidget(logout_btn)

    def _on_clicked(self, key: str):
        self.navigation_requested.emit(key)

    def set_active(self, key: str):
        for k, btn in self.buttons.items():
            btn.setProperty("active", "true" if k == key else "false")
            btn.style().unpolish(btn)
            btn.style().polish(btn)


class StatCard(QFrame):
    """Dashboard stat card — value + label with optional icon."""

    def __init__(self, label: str, value: str = "0", icon: str = "", parent=None):
        super().__init__(parent)
        self.setProperty("class", "statCard")
        self.setMinimumSize(180, 100)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(4)

        # Icon
        if icon:
            self.icon_label = QLabel(icon)
            self.icon_label.setObjectName("statIcon")
            self.icon_label.setStyleSheet("font-size: 24px; background: transparent; border: none;")
            layout.addWidget(self.icon_label)

        # Value
        self.value_label = QLabel(str(value))
        self.value_label.setObjectName("statValue")
        self.value_label.setStyleSheet("font-weight: bold; font-size: 28px; background: transparent; border: none;")
        layout.addWidget(self.value_label)

        # Label
        self.desc_label = QLabel(label)
        self.desc_label.setObjectName("statLabel")
        self.desc_label.setStyleSheet("font-size: 12px; background: transparent; border: none;")
        layout.addWidget(self.desc_label)

    def set_value(self, value):
        self.value_label.setText(str(value))



class StyledTable(QTableWidget):
    """Pre-configured table widget matching Stitch design tables."""

    def __init__(self, columns: list, parent=None):
        super().__init__(parent)
        self.setColumnCount(len(columns))
        self.setHorizontalHeaderLabels(columns)

        # Header config
        header = self.horizontalHeader()
        header.setDefaultAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        header.setStretchLastSection(True)
        header.setSectionResizeMode(QHeaderView.Stretch)

        # Table config
        self.verticalHeader().setVisible(False)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.setAlternatingRowColors(False)
        self.setShowGrid(False)
        self.setWordWrap(False)
        self.verticalHeader().setDefaultSectionSize(48)

    def set_column_widths(self, widths: dict):
        """Set specific column widths. Keys are column indices."""
        header = self.horizontalHeader()
        for col, width in widths.items():
            header.setSectionResizeMode(col, QHeaderView.Fixed)
            self.setColumnWidth(col, width)


class SearchBar(QWidget):
    """Search bar with icon placeholder styling."""

    search_changed = Signal(str)

    def __init__(self, placeholder: str = "Search...", parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.input = QLineEdit()
        self.input.setPlaceholderText(f"🔍  {placeholder}")
        self.input.setMinimumWidth(250)
        self.input.textChanged.connect(self.search_changed.emit)
        layout.addWidget(self.input)

    def text(self):
        return self.input.text()


class PageHeader(QWidget):
    """Standard page header with title + optional action buttons."""

    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 16)

        self.title_label = QLabel(title)
        self.title_label.setStyleSheet(
            "font-size: 22px; font-weight: bold;"
        )
        layout.addWidget(self.title_label)

        layout.addStretch()

        self.actions_layout = QHBoxLayout()
        self.actions_layout.setSpacing(8)
        layout.addLayout(self.actions_layout)

    # Style map for inline styling
    BUTTON_STYLES = {
        "primaryBtn": """
            QPushButton {
                background-color: #1152d4; color: #ffffff;
                border: none; border-radius: 8px;
                padding: 10px 24px; font-size: 13px; font-weight: 600;
            }
            QPushButton:hover { background-color: #0d3fa3; }
        """,
        "secondaryBtn": """
            QPushButton {
                background-color: #ffffff; color: #1152d4;
                border: 1px solid #1152d4; border-radius: 8px;
                padding: 10px 24px; font-size: 13px; font-weight: 600;
            }
            QPushButton:hover { background-color: #e8eefb; }
        """,
        "successBtn": """
            QPushButton {
                background-color: #22c55e; color: #ffffff;
                border: none; border-radius: 8px;
                padding: 10px 24px; font-size: 13px; font-weight: 600;
            }
            QPushButton:hover { background-color: #16a34a; }
        """,
        "dangerBtn": """
            QPushButton {
                background-color: #ef4444; color: #ffffff;
                border: none; border-radius: 8px;
                padding: 8px 16px; font-size: 12px; font-weight: 600;
            }
            QPushButton:hover { background-color: #dc2626; }
        """,
    }

    def add_action_button(self, text: str, style_class: str = "primaryBtn") -> QPushButton:
        btn = QPushButton(text)
        btn.setCursor(Qt.PointingHandCursor)
        style = self.BUTTON_STYLES.get(style_class, self.BUTTON_STYLES["primaryBtn"])
        btn.setStyleSheet(style)
        self.actions_layout.addWidget(btn)
        return btn


def create_form_field(label_text: str, widget=None, parent=None) -> tuple:
    """Create a labeled form field. Returns (container, input_widget)."""
    container = QVBoxLayout()
    container.setSpacing(4)

    label = QLabel(label_text)
    label.setProperty("class", "fieldLabel")
    container.addWidget(label)

    if widget is None:
        widget = QLineEdit()
    container.addWidget(widget)

    return container, widget
