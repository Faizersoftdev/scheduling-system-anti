"""
Admin Dashboard — summary cards, quick actions, recent schedules.
Matches the Stitch admin_dashboard_header_fixed_single_line design.
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QSizePolicy
)
from PySide6.QtCore import Qt, Signal
from ui.components import StatCard, PageHeader


class DashboardView(QWidget):
    """Dashboard with stats overview and quick actions."""

    navigate_to = Signal(str)  # Emits target page name

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 24, 32, 24)
        layout.setSpacing(24)

        # ── Page header ──
        header = PageHeader("Dashboard")
        layout.addWidget(header)

        # ── Stat cards row ──
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(16)

        self.stat_instructors = StatCard("Active Instructors", "0", "👨‍🏫")
        self.stat_subjects = StatCard("Total Subjects", "0", "📚")
        self.stat_blocks = StatCard("Student Blocks", "0", "👥")
        self.stat_rooms = StatCard("Available Rooms", "0", "🏫")

        for card in [self.stat_instructors, self.stat_subjects, self.stat_blocks, self.stat_rooms]:
            card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            stats_layout.addWidget(card)

        layout.addLayout(stats_layout)

        # ── Quick Actions section ──
        actions_frame = QFrame()
        actions_frame.setObjectName("quickActionsCard")
        actions_frame.setProperty("class", "card")
        actions_layout = QVBoxLayout(actions_frame)
        actions_layout.setContentsMargins(24, 20, 24, 20)
        actions_layout.setSpacing(16)

        actions_title = QLabel("Quick Actions")
        actions_title.setObjectName("sectionTitleLabel")
        actions_layout.addWidget(actions_title)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(12)

        gen_btn = QPushButton("📅  Generate Schedule")
        gen_btn.setStyleSheet("""
            QPushButton {
                background-color: #1152d4; color: white;
                border: none; border-radius: 8px;
                padding: 12px 24px; font-size: 13px; font-weight: 600;
            }
            QPushButton:hover { background-color: #0d3fa3; }
        """)
        gen_btn.setCursor(Qt.PointingHandCursor)
        gen_btn.setMinimumHeight(44)
        gen_btn.clicked.connect(lambda: self.navigate_to.emit("schedule"))
        btn_row.addWidget(gen_btn)

        teacher_btn = QPushButton("👨‍🏫  Manage Teachers")
        teacher_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent; color: #1152d4;
                border: 1px solid #1152d4; border-radius: 8px;
                padding: 12px 24px; font-size: 13px; font-weight: 600;
            }
            QPushButton:hover { background-color: rgba(17, 82, 212, 0.1); }
        """)
        teacher_btn.setCursor(Qt.PointingHandCursor)
        teacher_btn.setMinimumHeight(44)
        teacher_btn.clicked.connect(lambda: self.navigate_to.emit("teachers"))
        btn_row.addWidget(teacher_btn)

        req_btn = QPushButton("📋  Class Requirements")
        req_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent; color: #1152d4;
                border: 1px solid #1152d4; border-radius: 8px;
                padding: 12px 24px; font-size: 13px; font-weight: 600;
            }
            QPushButton:hover { background-color: rgba(17, 82, 212, 0.1); }
        """)
        req_btn.setCursor(Qt.PointingHandCursor)
        req_btn.setMinimumHeight(44)
        req_btn.clicked.connect(lambda: self.navigate_to.emit("requirements"))
        btn_row.addWidget(req_btn)

        actions_layout.addLayout(btn_row)
        layout.addWidget(actions_frame)

        # ── Recent Schedules section ──
        recent_frame = QFrame()
        recent_frame.setProperty("class", "card")
        recent_layout = QVBoxLayout(recent_frame)
        recent_layout.setContentsMargins(24, 20, 24, 20)
        recent_layout.setSpacing(12)

        recent_title = QLabel("Recent Schedules")
        recent_title.setObjectName("sectionTitleLabel")
        recent_layout.addWidget(recent_title)

        self.recent_container = QVBoxLayout()
        self.recent_container.setSpacing(8)
        recent_layout.addLayout(self.recent_container)

        self.no_schedules_label = QLabel("No schedules generated yet. Use 'Generate Schedule' to create one.")
        self.no_schedules_label.setObjectName("mutedLabel")
        self.recent_container.addWidget(self.no_schedules_label)

        layout.addWidget(recent_frame)
        layout.addStretch()

    def refresh_data(self):
        """Reload stats and recent schedules from database."""
        from database import get_dashboard_stats, get_all_schedules

        stats = get_dashboard_stats()
        self.stat_instructors.set_value(stats["instructors"])
        self.stat_subjects.set_value(stats["subjects"])
        self.stat_blocks.set_value(stats["blocks"])
        self.stat_rooms.set_value(stats["rooms"])

        # Refresh recent schedules
        schedules = get_all_schedules()

        # Clear current items
        while self.recent_container.count():
            item = self.recent_container.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not schedules:
            lbl = QLabel("No schedules generated yet. Use 'Generate Schedule' to create one.")
            lbl.setObjectName("mutedLabel")
            self.recent_container.addWidget(lbl)
        else:
            for sched in schedules[:5]:  # Show last 5
                row = QFrame()
                row.setObjectName("scheduleRow")
                row_layout = QHBoxLayout(row)
                row_layout.setContentsMargins(12, 8, 12, 8)

                name_label = QLabel(f"📅  {sched['name']}")
                name_label.setObjectName("schedRowName")
                row_layout.addWidget(name_label)

                date_label = QLabel(sched['created_at'])
                date_label.setObjectName("schedRowDate")
                row_layout.addWidget(date_label)

                row_layout.addStretch()

                status_label = QLabel(sched['status'])
                status_label.setObjectName("schedRowStatus")
                row_layout.addWidget(status_label)

                view_btn = QPushButton("View")
                view_btn.setProperty("class", "primaryBtn smallBtn")
                view_btn.setCursor(Qt.PointingHandCursor)
                view_btn.clicked.connect(lambda checked, s=sched: self.navigate_to.emit("schedule"))
                row_layout.addWidget(view_btn)

                self.recent_container.addWidget(row)
