"""
Generated Schedule View — timetable grid, filters, generate/export.
Matches the Stitch generated_schedule_view_no_profile_icon design.
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QTableWidgetItem, QComboBox, QMessageBox,
    QTableWidget, QHeaderView, QAbstractItemView, QSizePolicy,
    QFileDialog, QApplication
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QBrush, QFont
from ui.components import PageHeader
from config import DAYS, DAY_ABBREVS, START_HOUR, END_HOUR

# Color palette for subjects in  the timetable
SUBJECT_COLORS = [
    "#3b82f6", "#ef4444", "#22c55e", "#f59e0b", "#8b5cf6",
    "#ec4899", "#06b6d4", "#f97316", "#14b8a6", "#6366f1",
    "#84cc16", "#e11d48", "#0ea5e9", "#a855f7", "#d946ef",
    "#10b981",
]


class ScheduleView(QWidget):
    """Generated schedule view with timetable grid, filters, and generation."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_schedule_id = None
        self.current_entries = []
        self._subject_color_map = {}
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 24, 32, 24)
        layout.setSpacing(16)

        # ── Page header ──
        header = PageHeader("Generated Schedule")
        self.generate_btn = header.add_action_button("⚡ Generate Schedule", "successBtn")
        self.export_btn = header.add_action_button("📥 Export CSV", "secondaryBtn")
        self.generate_btn.clicked.connect(self._generate_schedule)
        self.export_btn.clicked.connect(self._export_csv)
        layout.addWidget(header)

        # ── Filters row ──
        filter_frame = QFrame()
        filter_frame.setProperty("class", "card")
        filter_frame.setObjectName("filterBar")
        filter_frame.setMinimumHeight(64)
        filter_layout = QHBoxLayout(filter_frame)
        filter_layout.setContentsMargins(16, 8, 16, 8)
        filter_layout.setSpacing(12)

        lbl_filter = QLabel("Filter by:")
        lbl_filter.setObjectName("filterTitle")
        filter_layout.addWidget(lbl_filter)

        # Schedule selector
        lbl_sched = QLabel("Schedule:")
        lbl_sched.setObjectName("filterLabel")
        filter_layout.addWidget(lbl_sched)

        
        self.schedule_combo = QComboBox()
        self.schedule_combo.setMinimumWidth(200)
        self.schedule_combo.currentIndexChanged.connect(self._on_schedule_changed)
        filter_layout.addWidget(self.schedule_combo)

        # Block filter
        lbl_block = QLabel("Block:")
        lbl_block.setObjectName("filterLabel")
        filter_layout.addWidget(lbl_block)
        
        self.block_combo = QComboBox()
        self.block_combo.setMinimumWidth(150)
        self.block_combo.addItem("All Blocks", None)
        self.block_combo.currentIndexChanged.connect(self._apply_filters)
        filter_layout.addWidget(self.block_combo)

        # Instructor filter
        lbl_instr = QLabel("Instructor:")
        lbl_instr.setObjectName("filterLabel")
        filter_layout.addWidget(lbl_instr)
        
        self.instructor_combo = QComboBox()
        self.instructor_combo.setMinimumWidth(150)
        self.instructor_combo.addItem("All Instructors", None)
        self.instructor_combo.currentIndexChanged.connect(self._apply_filters)
        filter_layout.addWidget(self.instructor_combo)

        filter_layout.addStretch()
        layout.addWidget(filter_frame)


        # ── Timetable grid ──
        self.timetable = QTableWidget()
        self.timetable.setColumnCount(6)  # Mon-Sat
        self.timetable.setHorizontalHeaderLabels(DAY_ABBREVS)
        self.timetable.setRowCount(END_HOUR - START_HOUR)

        # Row headers: time slots
        time_labels = []
        for h in range(START_HOUR, END_HOUR):
            period = "AM" if h < 12 else "PM"
            display_h = h if h <= 12 else h - 12
            time_labels.append(f"{display_h}:00 {period}")
        self.timetable.setVerticalHeaderLabels(time_labels)

        # Table styling
        self.timetable.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.timetable.verticalHeader().setDefaultSectionSize(110)
        self.timetable.verticalHeader().setMinimumWidth(90)
        self.timetable.setSelectionMode(QAbstractItemView.NoSelection)
        self.timetable.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.timetable.setStyleSheet("""
            QTableWidget { background: #ffffff; border: 1px solid #e2e8f0; border-radius: 8px; }
            QTableWidget::item { padding: 4px; border: 1px solid #f1f5f9; }
            QHeaderView::section {
                background-color: #1152d4; color: white;
                font-weight: 600; font-size: 12px; padding: 8px;
                border: none;
            }
            QHeaderView::section:vertical {
                background-color: #f8fafc; color: #64748b;
                font-weight: 500; font-size: 11px;
                border-bottom: 1px solid #e2e8f0;
            }
        """)

        layout.addWidget(self.timetable)

        # ── Color Legend ──
        self.legend_frame = QFrame()
        self.legend_frame.setProperty("class", "card")
        self.legend_layout = QHBoxLayout(self.legend_frame)
        self.legend_layout.setContentsMargins(16, 8, 16, 8)
        self.legend_layout.setSpacing(16)
        
        legend_title = QLabel("Legend:")
        legend_title.setStyleSheet("font-weight: 600; font-size: 12px; color: #64748b;")
        self.legend_layout.addWidget(legend_title)
        self.legend_layout.addStretch()
        layout.addWidget(self.legend_frame)

        # ── Status bar ──
        self.status_label = QLabel("No schedule loaded. Click 'Generate Schedule' to create one.")
        self.status_label.setStyleSheet("color: #64748b; font-size: 12px; padding: 4px 0;")
        layout.addWidget(self.status_label)

    def refresh_data(self):
        """Reload schedule list, block/instructor combos."""
        from database import get_all_schedules, get_all_blocks, get_all_instructors

        # Refresh schedule combo
        self.schedule_combo.blockSignals(True)
        self.schedule_combo.clear()
        schedules = get_all_schedules()
        for s in schedules:
            self.schedule_combo.addItem(f"{s['name']} ({s['created_at']})", s['id'])
        self.schedule_combo.blockSignals(False)

        # Refresh block combo
        self.block_combo.blockSignals(True)
        current_block = self.block_combo.currentData()
        self.block_combo.clear()
        self.block_combo.addItem("All Blocks", None)
        for b in get_all_blocks():
            self.block_combo.addItem(b["block_name"], b["id"])
        # Restore selection
        for i in range(self.block_combo.count()):
            if self.block_combo.itemData(i) == current_block:
                self.block_combo.setCurrentIndex(i)
                break
        self.block_combo.blockSignals(False)

        # Refresh instructor combo
        self.instructor_combo.blockSignals(True)
        current_instr = self.instructor_combo.currentData()
        self.instructor_combo.clear()
        self.instructor_combo.addItem("All Instructors", None)
        for instr in get_all_instructors():
            self.instructor_combo.addItem(instr["full_name"], instr["id"])
        for i in range(self.instructor_combo.count()):
            if self.instructor_combo.itemData(i) == current_instr:
                self.instructor_combo.setCurrentIndex(i)
                break
        self.instructor_combo.blockSignals(False)

        # Load first schedule if available
        if schedules:
            self._load_schedule(schedules[0]["id"])
        else:
            self._clear_timetable()

    def _on_schedule_changed(self, index):
        schedule_id = self.schedule_combo.currentData()
        if schedule_id:
            self._load_schedule(schedule_id)

    def _load_schedule(self, schedule_id: int):
        from database import get_schedule_entries
        self.current_schedule_id = schedule_id
        self.current_entries = get_schedule_entries(schedule_id)
        self._build_color_map()
        self._apply_filters()

    def _build_color_map(self):
        """Assign colors to unique subjects."""
        unique_codes = list(set(e["subject_code"] for e in self.current_entries))
        unique_codes.sort()
        self._subject_color_map = {}
        for i, code in enumerate(unique_codes):
            self._subject_color_map[code] = SUBJECT_COLORS[i % len(SUBJECT_COLORS)]
        self._update_legend()

    def _update_legend(self):
        """Rebuild the color legend based on current color map."""
        # Clear existing legend items (keep the "Legend:" label at index 0)
        while self.legend_layout.count() > 1:
            item = self.legend_layout.takeAt(1)
            if item.widget():
                item.widget().deleteLater()

        for code, color in sorted(self._subject_color_map.items()):
            item_widget = QWidget()
            item_layout = QHBoxLayout(item_widget)
            item_layout.setContentsMargins(0, 0, 0, 0)
            item_layout.setSpacing(4)

            # Color swatch
            swatch = QLabel()
            swatch.setFixedSize(14, 14)
            swatch.setStyleSheet(f"background-color: {color}; border-radius: 3px; border: none;")
            item_layout.addWidget(swatch)

            # Subject code label
            code_label = QLabel(code)
            code_label.setStyleSheet("font-size: 11px; font-weight: 500; color: #64748b; border: none;")
            item_layout.addWidget(code_label)

            self.legend_layout.addWidget(item_widget)

        # Add conflict indicator
        conflict_widget = QWidget()
        conflict_layout = QHBoxLayout(conflict_widget)
        conflict_layout.setContentsMargins(0, 0, 0, 0)
        conflict_layout.setSpacing(4)
        conflict_swatch = QLabel()
        conflict_swatch.setFixedSize(14, 14)
        conflict_swatch.setStyleSheet("background-color: #ef4444; border-radius: 3px; border: 2px solid #dc2626;")
        conflict_layout.addWidget(conflict_swatch)
        conflict_label = QLabel("Conflict")
        conflict_label.setStyleSheet("font-size: 11px; font-weight: 500; color: #ef4444; border: none;")
        conflict_layout.addWidget(conflict_label)
        self.legend_layout.addWidget(conflict_widget)

        self.legend_layout.addStretch()

    def _apply_filters(self):
        """Rebuild timetable with current filters."""
        filter_block = self.block_combo.currentData()
        filter_instructor = self.instructor_combo.currentData()

        entries = self.current_entries
        if filter_block:
            entries = [e for e in entries if e["block_id"] == filter_block]
        if filter_instructor:
            entries = [e for e in entries if e["instructor_id"] == filter_instructor]

        self._render_timetable(entries)

    def _clear_timetable(self):
        for row in range(self.timetable.rowCount()):
            for col in range(self.timetable.columnCount()):
                self.timetable.setItem(row, col, QTableWidgetItem(""))
                self.timetable.removeCellWidget(row, col)

    def _render_timetable(self, entries: list):
        """Render entries into the timetable grid."""
        self._clear_timetable()

        day_to_col = {day: i for i, day in enumerate(DAYS)}

        for entry in entries:
            day = entry["day"]
            hour = entry["start_hour"]

            col = day_to_col.get(day)
            row = hour - START_HOUR

            if col is None or row < 0 or row >= self.timetable.rowCount():
                continue

            # Build cell text
            subject_code = entry["subject_code"]
            block_name = entry["block_name"]
            instructor = entry["instructor_name"].split(".")[-1].strip() if "." in entry["instructor_name"] else entry["instructor_name"]
            room = f"{entry['building']} {entry['room_name']}"

            cell_text = f"{subject_code}\n{block_name}\n{instructor}\n{room}"

            # Check if cell already has content (conflict or existing)
            existing_widget = self.timetable.cellWidget(row, col)
            if existing_widget:
                lbl = existing_widget.findChild(QLabel)
                if lbl:
                    lbl.setText(lbl.text() + "\n---\n" + cell_text)
                    lbl.setStyleSheet(f"""
                        QLabel {{
                            background-color: #ef4444;
                            color: white;
                            font-family: "Segoe UI", "Lexend", sans-serif;
                            font-size: 11px;
                            font-weight: bold;
                            border-radius: 6px;
                            padding: 4px;
                        }}
                    """)
                continue

            # Create a widget with the required background color
            color = self._subject_color_map.get(subject_code, "#1152d4")
            
            cell_widget = QWidget()
            cell_layout = QVBoxLayout(cell_widget)
            cell_layout.setContentsMargins(2, 2, 2, 2)
            lbl = QLabel(cell_text)
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setWordWrap(True)
            lbl.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            lbl.setStyleSheet(f"""
                QLabel {{
                    background-color: {color};
                    color: white;
                    font-family: "Segoe UI", "Lexend", sans-serif;
                    font-size: 11px;
                    font-weight: bold;
                    border-radius: 6px;
                    padding: 4px;
                }}
            """)
            cell_layout.addWidget(lbl)
            
            # Still set an empty item to ensure selection borders align (do this BEFORE setCellWidget)
            self.timetable.setItem(row, col, QTableWidgetItem(""))
            self.timetable.setCellWidget(row, col, cell_widget)

        count = len(entries)
        self.status_label.setText(f"Showing {count} schedule entries.")

    def _generate_schedule(self):
        """Run the scheduling algorithm."""
        from database import get_all_blocks, get_block_with_subjects
        
        # Check if any blocks have subjects assigned
        blocks = get_all_blocks()
        has_assignments = False
        for block in blocks:
            block_data = get_block_with_subjects(block["id"])
            if block_data and block_data.get("subjects"):
                has_assignments = True
                break
        
        if not has_assignments:
            QMessageBox.warning(
                self, "No Requirements",
                "No subjects have been assigned to any blocks yet.\n\n"
                "Please go to 'Requirements' and assign subjects to blocks first."
            )
            return

        reply = QMessageBox.question(
            self, "Generate Schedule",
            "This will create a new schedule based on current requirements.\nProceed?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes
        )
        if reply != QMessageBox.Yes:
            return

        QApplication.setOverrideCursor(Qt.WaitCursor)

        try:
            from scheduler import ScheduleGenerator
            gen = ScheduleGenerator()
            success, schedule_id, conflicts = gen.generate_and_save()

            QApplication.restoreOverrideCursor()

            if conflicts:
                conflict_msg = "\n".join(f"• {c}" for c in conflicts)
                QMessageBox.warning(
                    self, "Schedule Generated with Warnings",
                    f"Schedule was generated but with conflicts:\n\n{conflict_msg}"
                )
            else:
                QMessageBox.information(
                    self, "Success",
                    "Schedule generated successfully with no conflicts!"
                )

            self.refresh_data()

        except Exception as e:
            QApplication.restoreOverrideCursor()
            QMessageBox.critical(self, "Error", f"Failed to generate schedule:\n{str(e)}")

    def _export_csv(self):
        """Export current timetable view to CSV."""
        if not self.current_entries:
            QMessageBox.information(self, "No Data", "No schedule data to export.")
            return

        filepath, _ = QFileDialog.getSaveFileName(
            self, "Export Schedule", "schedule.csv", "CSV Files (*.csv)"
        )
        if not filepath:
            return

        filter_block = self.block_combo.currentData()
        filter_instructor = self.instructor_combo.currentData()
        entries = self.current_entries
        if filter_block:
            entries = [e for e in entries if e["block_id"] == filter_block]
        if filter_instructor:
            entries = [e for e in entries if e["instructor_id"] == filter_instructor]

        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write("Day,Time,Subject,Block,Instructor,Room,Building\n")
                for e in sorted(entries, key=lambda x: (x["day"], x["start_hour"])):
                    h = e["start_hour"]
                    period = "AM" if h < 12 else "PM"
                    dh = h if h <= 12 else h - 12
                    time_str = f"{dh}:00-{dh+1}:00 {period}"
                    f.write(
                        f"{e['day']},{time_str},{e['subject_code']},{e['block_name']},"
                        f"{e['instructor_name']},{e['room_name']},{e['building']}\n"
                    )
            QMessageBox.information(self, "Exported", f"Schedule exported to:\n{filepath}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to export:\n{str(e)}")
