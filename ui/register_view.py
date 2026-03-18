"""
Registration page — centered card with form fields.
Matches the Stitch registration_screen_updated design.
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFrame
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap
import os
from config import LOGO_PATH, SCHOOL_NAME, SCHOOL_FULL_NAME


class RegisterView(QWidget):
    """Registration screen with centered card layout."""

    registration_success = Signal()
    switch_to_login = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("authBackground")
        self._build_ui()

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setAlignment(Qt.AlignCenter)

        # ── Card frame ──
        card = QFrame()
        card.setObjectName("registerCard")
        card.setFixedWidth(440)
        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(12)
        card_layout.setContentsMargins(40, 32, 40, 32)

        # Logo
        if os.path.exists(LOGO_PATH):
            logo_label = QLabel()
            pixmap = QPixmap(LOGO_PATH)
            logo_label.setPixmap(pixmap.scaled(
                60, 60, Qt.KeepAspectRatio, Qt.SmoothTransformation
            ))
            logo_label.setAlignment(Qt.AlignCenter)
            card_layout.addWidget(logo_label)

        # School name
        school_label = QLabel(SCHOOL_NAME)
        school_label.setAlignment(Qt.AlignCenter)
        school_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #1152d4;")
        card_layout.addWidget(school_label)

        # Title
        title = QLabel("Create Account")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 16px; font-weight: 600; color: #1e293b; margin-top: 4px;")
        card_layout.addWidget(title)

        subtitle = QLabel("Register a new administrator account")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("font-size: 12px; color: #64748b; margin-bottom: 8px;")
        card_layout.addWidget(subtitle)

        # ── Form fields ──
        fields = [
            ("Full Name", "full_name_input", "Enter your full name", False),
            ("Email", "email_input", "Enter your email", False),
            ("Username", "username_input", "Choose a username", False),
            ("Password", "password_input", "Create a password", True),
            ("Confirm Password", "confirm_input", "Confirm your password", True),
        ]

        for label_text, attr_name, placeholder, is_password in fields:
            label = QLabel(label_text)
            label.setStyleSheet("font-size: 12px; font-weight: 500; color: #64748b;")
            card_layout.addWidget(label)

            inp = QLineEdit()
            inp.setPlaceholderText(placeholder)
            if is_password:
                inp.setEchoMode(QLineEdit.Password)
            setattr(self, attr_name, inp)
            card_layout.addWidget(inp)

        # Error/success message
        self.message_label = QLabel("")
        self.message_label.setAlignment(Qt.AlignCenter)
        self.message_label.setWordWrap(True)
        self.message_label.hide()
        card_layout.addWidget(self.message_label)

        # ── Register button ──
        card_layout.addSpacing(4)
        self.register_btn = QPushButton("Create Account")
        self.register_btn.setProperty("class", "primaryBtn")
        self.register_btn.setCursor(Qt.PointingHandCursor)
        self.register_btn.setMinimumHeight(42)
        self.register_btn.clicked.connect(self._handle_register)
        card_layout.addWidget(self.register_btn)

        # ── Login link ──
        card_layout.addSpacing(4)
        login_row = QHBoxLayout()
        login_row.setAlignment(Qt.AlignCenter)

        login_text = QLabel("Already have an account?")
        login_text.setStyleSheet("font-size: 12px; color: #64748b;")
        login_row.addWidget(login_text)

        login_link = QPushButton("Sign In")
        login_link.setStyleSheet(
            "QPushButton { border: none; color: #1152d4; font-size: 12px; "
            "font-weight: 600; text-decoration: underline; background: transparent; }"
            "QPushButton:hover { color: #0d3fa3; }"
        )
        login_link.setCursor(Qt.PointingHandCursor)
        login_link.clicked.connect(self.switch_to_login.emit)
        login_row.addWidget(login_link)

        card_layout.addLayout(login_row)
        outer.addWidget(card)

        # Enter key
        self.confirm_input.returnPressed.connect(self._handle_register)

    def _handle_register(self):
        full_name = self.full_name_input.text().strip()
        email = self.email_input.text().strip()
        username = self.username_input.text().strip()
        password = self.password_input.text()
        confirm = self.confirm_input.text()

        # Validation
        if not all([full_name, email, username, password, confirm]):
            self._show_message("Please fill in all fields.", error=True)
            return

        if password != confirm:
            self._show_message("Passwords do not match.", error=True)
            return

        if len(password) < 6:
            self._show_message("Password must be at least 6 characters.", error=True)
            return

        if "@" not in email:
            self._show_message("Please enter a valid email address.", error=True)
            return

        from database import register_user
        success, msg = register_user(username, email, password, full_name)
        if success:
            self._show_message(msg, error=False)
            # Clear fields
            for attr in ["full_name_input", "email_input", "username_input", "password_input", "confirm_input"]:
                getattr(self, attr).clear()
            self.registration_success.emit()
        else:
            self._show_message(msg, error=True)

    def _show_message(self, msg: str, error: bool = True):
        self.message_label.setText(msg)
        self.message_label.setProperty("class", "errorLabel" if error else "successLabel")
        self.message_label.style().unpolish(self.message_label)
        self.message_label.style().polish(self.message_label)
        self.message_label.show()
