"""
Scheduling Automation Program — Main Entry Point
SLTCFPDI - Southern Luzon Technological College Foundation Pioduran Incorporated

Launches the PySide6 desktop application with login → dashboard navigation.
"""
import sys
import os

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QStackedWidget, QMessageBox
)
from PySide6.QtCore import Qt, QFile, QTextStream
from PySide6.QtGui import QIcon, QFontDatabase

from config import (
    APP_TITLE, WINDOW_WIDTH, WINDOW_HEIGHT,
    WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT, LOGO_PATH,
    BASE_DIR
)
from database import init_db

# UI Views
from ui.login_view import LoginView
from ui.register_view import RegisterView
from ui.dashboard_view import DashboardView
from ui.teacher_view import TeacherView
from ui.requirements_view import RequirementsView
from ui.schedule_view import ScheduleView
from ui.components import HeaderWidget, SidebarWidget


class MainWindow(QMainWindow):
    """Main application window with stacked page navigation."""

    # Page indices
    PAGE_LOGIN = 0
    PAGE_REGISTER = 1
    PAGE_DASHBOARD = 2
    PAGE_TEACHERS = 3
    PAGE_REQUIREMENTS = 4
    PAGE_SCHEDULE = 5

    def __init__(self):
        super().__init__()
        self.current_user = None
        self.is_dark_mode = False
        self.setWindowTitle(APP_TITLE)
        self.resize(WINDOW_WIDTH, WINDOW_HEIGHT)
        self.setMinimumSize(WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT)

        # Set window icon
        if os.path.exists(LOGO_PATH):
            self.setWindowIcon(QIcon(LOGO_PATH))

        self._build_ui()
        self._connect_signals()

        # Start at login
        self._show_auth_mode()

    def _build_ui(self):
        # ── Central widget ──
        central = QWidget()
        self.setCentralWidget(central)
        self.main_layout = QVBoxLayout(central)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # ── Header (hidden on auth pages) ──
        self.header = HeaderWidget()
        self.main_layout.addWidget(self.header)

        # ── Body: sidebar + page stack ──
        body_widget = QWidget()
        self.body_layout = QHBoxLayout(body_widget)
        self.body_layout.setContentsMargins(0, 0, 0, 0)
        self.body_layout.setSpacing(0)

        # Sidebar (hidden on auth pages)
        self.sidebar = SidebarWidget()
        self.body_layout.addWidget(self.sidebar)

        # Stacked widget for all pages
        self.stack = QStackedWidget()
        self.body_layout.addWidget(self.stack)

        self.main_layout.addWidget(body_widget)

        # ── Create all views ──
        self.login_view = LoginView()
        self.register_view = RegisterView()
        self.dashboard_view = DashboardView()
        self.teacher_view = TeacherView()
        self.requirements_view = RequirementsView()
        self.schedule_view = ScheduleView()

        # Add to stack in order (indices must match PAGE_ constants)
        self.stack.addWidget(self.login_view)       # 0
        self.stack.addWidget(self.register_view)     # 1
        self.stack.addWidget(self.dashboard_view)    # 2
        self.stack.addWidget(self.teacher_view)      # 3
        self.stack.addWidget(self.requirements_view) # 4
        self.stack.addWidget(self.schedule_view)     # 5

    def _connect_signals(self):
        # Auth signals
        self.login_view.login_success.connect(self._on_login)
        self.login_view.switch_to_register.connect(
            lambda: self.stack.setCurrentIndex(self.PAGE_REGISTER)
        )
        self.register_view.registration_success.connect(
            lambda: self.stack.setCurrentIndex(self.PAGE_LOGIN)
        )
        self.register_view.switch_to_login.connect(
            lambda: self.stack.setCurrentIndex(self.PAGE_LOGIN)
        )

        # Sidebar navigation
        self.sidebar.navigation_requested.connect(self._navigate)

        # Dashboard quick actions
        self.dashboard_view.navigate_to.connect(self._navigate)

        # Theme toggling
        self.header.theme_toggled.connect(self._toggle_theme)

    def _show_auth_mode(self):
        """Show login or register pages (hide header + sidebar)."""
        self.header.hide()
        self.sidebar.hide()
        self.stack.setCurrentIndex(self.PAGE_LOGIN)
        self.login_view.focus_username()

    def _show_app_mode(self):
        """Show the main app with header + sidebar."""
        self.header.show()
        self.sidebar.show()
        self._navigate("dashboard")

    def _on_login(self, user: dict):
        """Handle successful login."""
        self.current_user = user
        self.header.set_user(user.get("full_name", user.get("username", "Admin")))
        self._show_app_mode()

    def _navigate(self, page_key: str):
        """Navigate to a page by key name."""
        if page_key == "logout":
            self._logout()
            return

        page_map = {
            "dashboard": self.PAGE_DASHBOARD,
            "teachers": self.PAGE_TEACHERS,
            "requirements": self.PAGE_REQUIREMENTS,
            "schedule": self.PAGE_SCHEDULE,
        }

        index = page_map.get(page_key)
        if index is not None:
            self.stack.setCurrentIndex(index)
            self.sidebar.set_active(page_key)

            # Refresh data on page show
            if page_key == "dashboard":
                self.dashboard_view.refresh_data()
            elif page_key == "teachers":
                self.teacher_view.refresh_data()
            elif page_key == "requirements":
                self.requirements_view.refresh_data()
            elif page_key == "schedule":
                self.schedule_view.refresh_data()

    def _toggle_theme(self):
        """Toggle dark mode and reload stylesheet."""
        self.is_dark_mode = not self.is_dark_mode
        self.header.theme_btn.setText("☀️" if self.is_dark_mode else "🌙")
        
        theme_file = "styles_dark.qss" if self.is_dark_mode else "styles.qss"
        qss_path = os.path.join(BASE_DIR, "ui", theme_file)
        
        if os.path.exists(qss_path):
            with open(qss_path, "r", encoding="utf-8") as f:
                QApplication.instance().setStyleSheet(f.read())

    def _logout(self):
        """Log out and return to login screen."""
        reply = QMessageBox.question(
            self, "Logout",
            "Are you sure you want to log out?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.current_user = None
            self._show_auth_mode()


def load_stylesheet(app: QApplication):
    """Load the QSS stylesheet."""
    qss_path = os.path.join(BASE_DIR, "ui", "styles.qss")
    if os.path.exists(qss_path):
        with open(qss_path, "r", encoding="utf-8") as f:
            app.setStyleSheet(f.read())


def main():
    # Initialize database
    init_db()

    # Create application
    app = QApplication(sys.argv)
    app.setApplicationName("Scheduling Automation Program")
    app.setOrganizationName("SLTCFPDI")

    # Load stylesheet
    load_stylesheet(app)

    # Create and show window
    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
