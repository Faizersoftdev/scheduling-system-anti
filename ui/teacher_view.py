"""
Teacher Management page — table + add/edit/delete functionality.
Matches the Stitch teacher_management_profile_icon_removed design.
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QTableWidgetItem, QDialog, QLineEdit, QComboBox,
    QCheckBox, QScrollArea, QMessageBox, QSizePolicy
)
from PySide6.QtCore import Qt, Signal
from ui.components import PageHeader, StyledTable, SearchBar


class TeacherDialog(QDialog):
    """Dialog for adding/editing a teacher."""

    def __init__(self, parent=None, teacher=None):
        super().__init__(parent)
        self.teacher = teacher
        self.setWindowTitle("Edit Teacher" if teacher else "Add Teacher")
        self.setFixedWidth(480)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(28, 24, 28, 24)

        title = QLabel("Edit Teacher" if self.teacher else "Add New Teacher")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(title)

        # Full Name
        layout.addWidget(self._label("Full Name"))
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("e.g. Mr. J. Dela Cruz")
        if self.teacher:
            self.name_input.setText(self.teacher["full_name"])
        layout.addWidget(self.name_input)

        # Short Name
        layout.addWidget(self._label("Short Name / Nickname"))
        self.short_name_input = QLineEdit()
        self.short_name_input.setPlaceholderText("e.g. Dela Cruz")
        if self.teacher:
            self.short_name_input.setText(self.teacher.get("short_name", ""))
        layout.addWidget(self.short_name_input)

        # Status (edit only)
        if self.teacher:
            layout.addWidget(self._label("Status"))
            self.status_combo = QComboBox()
            self.status_combo.addItems(["Active", "Inactive"])
            self.status_combo.setCurrentText(self.teacher.get("status", "Active"))
            layout.addWidget(self.status_combo)

        # Subjects
        layout.addWidget(self._label("Assigned Subjects"))
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setMaximumHeight(200)
        scroll.setStyleSheet("QScrollArea { border: 1px solid #475569; border-radius: 8px; }")
        scroll_widget = QWidget()
        self.subjects_layout = QVBoxLayout(scroll_widget)
        self.subjects_layout.setSpacing(4)
        self.subjects_layout.setContentsMargins(8, 8, 8, 8)

        from database import get_all_subjects
        subjects = get_all_subjects()
        self.subject_checkboxes = {}

        current_subject_ids = set()
        if self.teacher and "subject_list" in self.teacher:
            current_subject_ids = {s["id"] for s in self.teacher["subject_list"]}

        for subj in subjects:
            cb = QCheckBox(f"{subj['code']} — {subj['name']}")
            if subj["id"] in current_subject_ids:
                cb.setChecked(True)
            self.subject_checkboxes[subj["id"]] = cb
            self.subjects_layout.addWidget(cb)

        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)

        # ── Quick Add Subject section ──
        add_subj_frame = QFrame()
        add_subj_frame.setStyleSheet("""
            QFrame { border: 1px solid #475569; border-radius: 8px; padding: 8px; }
        """)
        add_subj_layout = QVBoxLayout(add_subj_frame)
        add_subj_layout.setSpacing(8)

        add_subj_title = QLabel("➕ Quick Add New Subject")
        add_subj_title.setStyleSheet("font-size: 12px; font-weight: 600; color: #60a5fa; border: none;")
        add_subj_layout.addWidget(add_subj_title)

        row1 = QHBoxLayout()
        self.new_subj_code = QLineEdit()
        self.new_subj_code.setPlaceholderText("Code (e.g. MATH101)")
        self.new_subj_code.setMinimumWidth(140)
        row1.addWidget(self.new_subj_code)

        self.new_subj_name = QLineEdit()
        self.new_subj_name.setPlaceholderText("Name (e.g. Mathematics)")
        row1.addWidget(self.new_subj_name)
        add_subj_layout.addLayout(row1)

        row2 = QHBoxLayout()
        self.new_subj_units = QComboBox()
        self.new_subj_units.addItems(["1", "2", "3", "4", "5"])
        self.new_subj_units.setCurrentText("3")
        row2.addWidget(QLabel("Units:"))
        row2.addWidget(self.new_subj_units)

        self.new_subj_type = QComboBox()
        self.new_subj_type.addItems(["Lecture", "Laboratory", "PE"])
        row2.addWidget(QLabel("Type:"))
        row2.addWidget(self.new_subj_type)

        add_subj_btn = QPushButton("Add Subject")
        add_subj_btn.setCursor(Qt.PointingHandCursor)
        add_subj_btn.setStyleSheet("""
            QPushButton {
                background-color: #22c55e; color: white;
                border: none; border-radius: 6px;
                font-size: 11px; font-weight: 600;
                padding: 6px 12px;
            }
            QPushButton:hover { background-color: #16a34a; }
        """)
        add_subj_btn.clicked.connect(self._quick_add_subject)
        row2.addWidget(add_subj_btn)
        add_subj_layout.addLayout(row2)

        layout.addWidget(add_subj_frame)

        # Buttons
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setProperty("class", "secondaryBtn")
        cancel_btn.setCursor(Qt.PointingHandCursor)
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(cancel_btn)

        save_btn = QPushButton("Save Teacher")
        save_btn.setProperty("class", "primaryBtn")
        save_btn.setCursor(Qt.PointingHandCursor)
        save_btn.clicked.connect(self._save)
        btn_row.addWidget(save_btn)

        layout.addLayout(btn_row)

    def _quick_add_subject(self):
        """Add a new subject to the database and add it to the checkbox list."""
        code = self.new_subj_code.text().strip()
        name = self.new_subj_name.text().strip()
        units = int(self.new_subj_units.currentText())
        subj_type = self.new_subj_type.currentText()

        if not code or not name:
            QMessageBox.warning(self, "Validation", "Subject code and name are required.")
            return

        from database import add_subject, get_all_subjects
        success, msg = add_subject(code, name, units, subj_type)
        if not success:
            QMessageBox.warning(self, "Error", msg)
            return

        # Find the newly added subject's ID
        subjects = get_all_subjects()
        new_subj = next((s for s in subjects if s["code"] == code), None)
        if new_subj:
            cb = QCheckBox(f"{new_subj['code']} — {new_subj['name']}")
            cb.setChecked(True)  # Auto-check it for the teacher
            self.subject_checkboxes[new_subj["id"]] = cb
            self.subjects_layout.addWidget(cb)

        # Clear the input fields
        self.new_subj_code.clear()
        self.new_subj_name.clear()
        self.new_subj_units.setCurrentText("3")
        self.new_subj_type.setCurrentIndex(0)

        QMessageBox.information(self, "Success", f"Subject '{code}' added successfully!")

    def _label(self, text):
        lbl = QLabel(text)
        lbl.setStyleSheet("font-size: 12px; font-weight: 500; color: #94a3b8;")
        return lbl

    def _save(self):
        name = self.name_input.text().strip()
        short = self.short_name_input.text().strip()

        if not name:
            QMessageBox.warning(self, "Validation", "Full name is required.")
            return

        selected_ids = [sid for sid, cb in self.subject_checkboxes.items() if cb.isChecked()]

        from database import add_instructor, update_instructor

        if self.teacher:
            status = self.status_combo.currentText()
            update_instructor(self.teacher["id"], name, short, status, selected_ids)
        else:
            add_instructor(name, short, selected_ids)

        self.accept()

    def get_data(self):
        return {
            "full_name": self.name_input.text().strip(),
            "short_name": self.short_name_input.text().strip(),
        }


class TeacherView(QWidget):
    """Teacher management page with table, search, add/edit/delete."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 24, 32, 24)
        layout.setSpacing(16)

        # ── Page header with Add button ──
        header = PageHeader("Teacher Management")
        self.add_btn = header.add_action_button("+ Add Teacher", "primaryBtn")
        self.add_btn.clicked.connect(self._add_teacher)
        layout.addWidget(header)

        # ── Search bar ──
        self.search = SearchBar("Search teachers by name or subject...")
        self.search.search_changed.connect(self._filter_table)
        layout.addWidget(self.search)

        # ── Table ──
        self.table = StyledTable(["ID", "Full Name", "Short Name", "Subjects", "Status", "Actions"])
        self.table.set_column_widths({0: 50, 4: 80, 5: 140})
        layout.addWidget(self.table)

    def refresh_data(self):
        """Reload teachers from database."""
        from database import get_all_instructors
        teachers = get_all_instructors()

        self.table.setRowCount(len(teachers))
        for row, t in enumerate(teachers):
            self.table.setItem(row, 0, QTableWidgetItem(str(t["id"])))
            self.table.setItem(row, 1, QTableWidgetItem(t["full_name"]))
            self.table.setItem(row, 2, QTableWidgetItem(t.get("short_name", "")))
            self.table.setItem(row, 3, QTableWidgetItem(t.get("subjects", "") or ""))

            # Status badge
            status = t.get("status", "Active")
            status_item = QTableWidgetItem(status)
            if status == "Active":
                status_item.setForeground(Qt.darkGreen)
            else:
                status_item.setForeground(Qt.red)
            self.table.setItem(row, 4, status_item)

            # Action buttons
            action_widget = QWidget()
            action_layout = QHBoxLayout(action_widget)
            action_layout.setContentsMargins(4, 2, 4, 2)
            action_layout.setSpacing(6)
            action_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

            edit_btn = QPushButton("Edit")
            edit_btn.setFixedSize(65, 32)
            edit_btn.setCursor(Qt.PointingHandCursor)
            edit_btn.setStyleSheet("""
                QPushButton {
                    background-color: #ffffff; color: #1152d4;
                    border: 1px solid #1152d4; border-radius: 6px;
                    font-size: 12px; font-weight: 600;
                    padding: 4px 8px;
                }
                QPushButton:hover { background-color: #e8eefb; }
            """)
            edit_btn.clicked.connect(lambda checked, tid=t["id"]: self._edit_teacher(tid))
            action_layout.addWidget(edit_btn)

            del_btn = QPushButton("Delete")
            del_btn.setFixedSize(65, 32)
            del_btn.setCursor(Qt.PointingHandCursor)
            del_btn.setStyleSheet("""
                QPushButton {
                    background-color: #ef4444; color: #ffffff;
                    border: none; border-radius: 6px;
                    font-size: 12px; font-weight: 600;
                    padding: 4px 8px;
                }
                QPushButton:hover { background-color: #dc2626; }
            """)
            del_btn.clicked.connect(lambda checked, tid=t["id"], name=t["full_name"]: self._delete_teacher(tid, name))
            action_layout.addWidget(del_btn)
            action_layout.addStretch()

            self.table.setCellWidget(row, 5, action_widget)

    def _add_teacher(self):
        dialog = TeacherDialog(self)
        if dialog.exec() == QDialog.Accepted:
            self.refresh_data()

    def _edit_teacher(self, teacher_id):
        from database import get_instructor
        teacher = get_instructor(teacher_id)
        if teacher:
            dialog = TeacherDialog(self, teacher)
            if dialog.exec() == QDialog.Accepted:
                self.refresh_data()

    def _delete_teacher(self, teacher_id, name):
        reply = QMessageBox.question(
            self, "Delete Teacher",
            f"Are you sure you want to delete '{name}'?\nThis cannot be undone.",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            from database import delete_instructor
            delete_instructor(teacher_id)
            self.refresh_data()

    def _filter_table(self, text: str):
        text = text.lower()
        for row in range(self.table.rowCount()):
            match = False
            for col in range(self.table.columnCount() - 1):  # Skip actions
                item = self.table.item(row, col)
                if item and text in item.text().lower():
                    match = True
                    break
            self.table.setRowHidden(row, not match)
