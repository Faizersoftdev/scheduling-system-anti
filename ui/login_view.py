"""
Login page — centered card with logo, username/password fields.
Matches the Stitch login_screen_text_updated design.
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFrame, QSpacerItem, QSizePolicy
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap
import os
from config import LOGO_PATH, SCHOOL_NAME, SCHOOL_FULL_NAME


class LoginView(QWidget):
    """Login screen with centered card layout."""

    login_success = Signal(dict)      # Emits user dict on successful login
    switch_to_register = Signal()      # Navigate to registration

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("authBackground")
        self._build_ui()

    def _build_ui(self):
        # Outer layout — centers the card
        outer = QVBoxLayout(self)
        outer.setAlignment(Qt.AlignCenter)

        # ── Card frame ──
        card = QFrame()
        card.setObjectName("loginCard")
        card.setFixedWidth(440)
        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(16)
        card_layout.setContentsMargins(40, 36, 40, 36)

        # Logo
        if os.path.exists(LOGO_PATH):
            logo_label = QLabel()
            pixmap = QPixmap(LOGO_PATH)
            logo_label.setPixmap(pixmap.scaled(
                70, 70, Qt.KeepAspectRatio, Qt.SmoothTransformation
            ))
            logo_label.setAlignment(Qt.AlignCenter)
            card_layout.addWidget(logo_label)

        # School name
        school_label = QLabel(SCHOOL_NAME)
        school_label.setAlignment(Qt.AlignCenter)
        school_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #1152d4; margin-top: 4px;")
        card_layout.addWidget(school_label)

        # Full school name
        full_name_label = QLabel(SCHOOL_FULL_NAME)
        full_name_label.setAlignment(Qt.AlignCenter)
        full_name_label.setWordWrap(True)
        full_name_label.setStyleSheet("font-size: 11px; color: #64748b; margin-bottom: 8px;")
        card_layout.addWidget(full_name_label)

        # Title
        title = QLabel("Sign In")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 18px; font-weight: 600; color: #1e293b; margin-top: 8px;")
        card_layout.addWidget(title)

        subtitle = QLabel("Enter your credentials to access the system")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("font-size: 12px; color: #64748b; margin-bottom: 12px;")
        card_layout.addWidget(subtitle)

        # ── Username field ──
        username_label = QLabel("Username")
        username_label.setStyleSheet("font-size: 12px; font-weight: 500; color: #64748b;")
        card_layout.addWidget(username_label)

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Enter your username")
        card_layout.addWidget(self.username_input)

        # ── Password field ──
        password_label = QLabel("Password")
        password_label.setStyleSheet("font-size: 12px; font-weight: 500; color: #64748b;")
        card_layout.addWidget(password_label)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Enter your password")
        self.password_input.setEchoMode(QLineEdit.Password)
        card_layout.addWidget(self.password_input)

        # Error message
        self.error_label = QLabel("")
        self.error_label.setProperty("class", "errorLabel")
        self.error_label.setAlignment(Qt.AlignCenter)
        self.error_label.hide()
        card_layout.addWidget(self.error_label)

        # ── Sign In button ──
        card_layout.addSpacing(4)
        self.login_btn = QPushButton("Sign In")
        self.login_btn.setProperty("class", "primaryBtn")
        self.login_btn.setCursor(Qt.PointingHandCursor)
        self.login_btn.setMinimumHeight(42)
        self.login_btn.clicked.connect(self._handle_login)
        card_layout.addWidget(self.login_btn)

        # ── Register link ──
        card_layout.addSpacing(8)
        register_row = QHBoxLayout()
        register_row.setAlignment(Qt.AlignCenter)

        reg_text = QLabel("Don't have an account?")
        reg_text.setStyleSheet("font-size: 12px; color: #64748b;")
        register_row.addWidget(reg_text)

        reg_link = QPushButton("Create Account")
        reg_link.setStyleSheet(
            "QPushButton { border: none; color: #1152d4; font-size: 12px; "
            "font-weight: 600; text-decoration: underline; background: transparent; }"
            "QPushButton:hover { color: #0d3fa3; }"
        )
        reg_link.setCursor(Qt.PointingHandCursor)
        reg_link.clicked.connect(self.switch_to_register.emit)
        register_row.addWidget(reg_link)

        card_layout.addLayout(register_row)

        outer.addWidget(card)

        # Enter key to submit
        self.password_input.returnPressed.connect(self._handle_login)
        self.username_input.returnPressed.connect(lambda: self.password_input.setFocus())

    def _handle_login(self):
        username = self.username_input.text().strip()
        password = self.password_input.text()

        if not username or not password:
            self._show_error("Please enter both username and password.")
            return

        from database import authenticate_user
        user = authenticate_user(username, password)
        if user:
            self.error_label.hide()
            self.username_input.clear()
            self.password_input.clear()
            self.login_success.emit(user)
        else:
            self._show_error("Invalid username or password.")

    def _show_error(self, msg: str):
        self.error_label.setText(msg)
        self.error_label.show()

    def focus_username(self):
        """Focus the username field when the view is shown."""
        self.username_input.setFocus()
