"""
Class Requirements page — manage block-subject assignments.
Matches the Stitch class_requirements_updated_header design.
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QTableWidgetItem, QDialog, QComboBox, QLineEdit,
    QMessageBox, QScrollArea, QCheckBox, QSizePolicy, QSpinBox
)
from PySide6.QtCore import Qt, Signal
from ui.components import PageHeader, StyledTable, SearchBar


class AssignSubjectsDialog(QDialog):
    """Dialog to assign subjects to a block."""

    def __init__(self, block, parent=None):
        super().__init__(parent)
        self.block = block
        self.setWindowTitle(f"Assign Subjects — {block['block_name']}")
        self.setFixedWidth(500)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(28, 24, 28, 24)

        title = QLabel(f"Subjects for {self.block['block_name']}")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(title)

        subtitle = QLabel("Select subjects this block needs to take:")
        subtitle.setStyleSheet("font-size: 12px; color: #94a3b8; margin-bottom: 8px;")
        layout.addWidget(subtitle)

        # Get current assignments
        from database import get_block_with_subjects, get_all_subjects
        block_data = get_block_with_subjects(self.block["id"])
        all_subjects = get_all_subjects()
        current_ids = set()
        if block_data and "subjects" in block_data:
            current_ids = {s["id"] for s in block_data["subjects"]}

        # Subject checkboxes in scrollable area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setMaximumHeight(300)

        scroll_widget = QWidget()
        self.subjects_layout = QVBoxLayout(scroll_widget)
        self.subjects_layout.setSpacing(6)
        self.subjects_layout.setContentsMargins(12, 12, 12, 12)

        self.subject_checkboxes = {}
        for subj in all_subjects:
            cb = QCheckBox(f"{subj['code']} — {subj['name']} ({subj['units']} units)")
            cb.setChecked(subj["id"] in current_ids)
            self.subject_checkboxes[subj["id"]] = cb
            self.subjects_layout.addWidget(cb)

        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)

        # Buttons
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent; color: #60a5fa;
                border: 1px solid #60a5fa; border-radius: 8px;
                padding: 10px 24px; font-size: 13px; font-weight: 600;
            }
            QPushButton:hover { background-color: rgba(96, 165, 250, 0.1); }
        """)
        cancel_btn.setCursor(Qt.PointingHandCursor)
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(cancel_btn)

        save_btn = QPushButton("Save Assignments")
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #1152d4; color: white;
                border: none; border-radius: 8px;
                padding: 10px 24px; font-size: 13px; font-weight: 600;
            }
            QPushButton:hover { background-color: #0d3fa3; }
        """)
        save_btn.setCursor(Qt.PointingHandCursor)
        save_btn.clicked.connect(self._save)
        btn_row.addWidget(save_btn)

        layout.addLayout(btn_row)

    def _save(self):
        from database import assign_subject_to_block, remove_subject_from_block, get_block_with_subjects

        block_data = get_block_with_subjects(self.block["id"])
        current_ids = set()
        if block_data and "subjects" in block_data:
            current_ids = {s["id"] for s in block_data["subjects"]}

        selected_ids = {sid for sid, cb in self.subject_checkboxes.items() if cb.isChecked()}

        # Add new assignments
        for sid in selected_ids - current_ids:
            assign_subject_to_block(self.block["id"], sid)

        # Remove deselected
        for sid in current_ids - selected_ids:
            remove_subject_from_block(self.block["id"], sid)

        self.accept()


class AddBlockDialog(QDialog):
    """Dialog to add a new student block."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add New Block")
        self.setFixedWidth(420)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(28, 24, 28, 24)

        title = QLabel("Add New Student Block")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(title)

        # Program name
        layout.addWidget(self._label("Program Name"))
        self.program_input = QLineEdit()
        self.program_input.setPlaceholderText("e.g. BEED, BTVTED, BSED")
        layout.addWidget(self.program_input)

        # Year level
        layout.addWidget(self._label("Year Level"))
        self.year_input = QSpinBox()
        self.year_input.setMinimum(1)
        self.year_input.setMaximum(5)
        self.year_input.setValue(1)
        layout.addWidget(self.year_input)

        # Section
        layout.addWidget(self._label("Section"))
        self.section_input = QLineEdit()
        self.section_input.setPlaceholderText("e.g. A, B, C")
        layout.addWidget(self.section_input)

        # Preview
        self.preview_label = QLabel("")
        self.preview_label.setStyleSheet("font-size: 12px; color: #60a5fa; font-weight: 500;")
        layout.addWidget(self.preview_label)

        self.program_input.textChanged.connect(self._update_preview)
        self.year_input.valueChanged.connect(self._update_preview)
        self.section_input.textChanged.connect(self._update_preview)

        # Buttons
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent; color: #60a5fa;
                border: 1px solid #60a5fa; border-radius: 8px;
                padding: 10px 24px; font-size: 13px; font-weight: 600;
            }
            QPushButton:hover { background-color: rgba(96, 165, 250, 0.1); }
        """)
        cancel_btn.setCursor(Qt.PointingHandCursor)
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(cancel_btn)

        save_btn = QPushButton("Create Block")
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #22c55e; color: white;
                border: none; border-radius: 8px;
                padding: 10px 24px; font-size: 13px; font-weight: 600;
            }
            QPushButton:hover { background-color: #16a34a; }
        """)
        save_btn.setCursor(Qt.PointingHandCursor)
        save_btn.clicked.connect(self._save)
        btn_row.addWidget(save_btn)

        layout.addLayout(btn_row)

    def _label(self, text):
        lbl = QLabel(text)
        lbl.setStyleSheet("font-size: 12px; font-weight: 500; color: #94a3b8;")
        return lbl

    def _update_preview(self):
        prog = self.program_input.text().strip().upper()
        year = self.year_input.value()
        sec = self.section_input.text().strip().upper()
        if prog and sec:
            self.preview_label.setText(f"Preview: {prog} {year}-{sec}")
        else:
            self.preview_label.setText("")

    def _save(self):
        prog = self.program_input.text().strip().upper()
        sec = self.section_input.text().strip().upper()
        year = self.year_input.value()

        if not prog:
            QMessageBox.warning(self, "Validation", "Program name is required.")
            return
        if not sec:
            QMessageBox.warning(self, "Validation", "Section is required.")
            return

        from database import add_block
        success, msg = add_block(prog, year, sec)
        if success:
            self.accept()
        else:
            QMessageBox.warning(self, "Error", msg)


class RequirementsView(QWidget):
    """Class requirements management — blocks with their subject assignments."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 24, 32, 24)
        layout.setSpacing(16)

        # ── Page header with Add Block button ──
        header = PageHeader("Class Requirements")
        self.add_block_btn = header.add_action_button("+ Add Block", "successBtn")
        self.add_block_btn.clicked.connect(self._add_block)
        layout.addWidget(header)

        # ── Info label ──
        info = QLabel("Assign subjects to each student block. Each subject's units determine the weekly hours scheduled.")
        info.setStyleSheet("color: #94a3b8; font-size: 13px; margin-bottom: 4px;")
        info.setWordWrap(True)
        layout.addWidget(info)

        # ── Search ──
        self.search = SearchBar("Search by block, subject, or instructor...")
        self.search.search_changed.connect(self._filter_table)
        layout.addWidget(self.search)

        # ── Blocks table ──
        self.table = StyledTable(["Block", "Subjects Assigned", "Total Hours/Week", "Actions"])
        self.table.set_column_widths({0: 160, 2: 140, 3: 280})
        layout.addWidget(self.table)

    def refresh_data(self):
        """Reload all block data from database."""
        from database import get_all_blocks, get_block_with_subjects

        blocks = get_all_blocks()
        self.table.setRowCount(len(blocks))

        for row, block in enumerate(blocks):
            block_data = get_block_with_subjects(block["id"])
            subjects = block_data.get("subjects", []) if block_data else []

            self.table.setItem(row, 0, QTableWidgetItem(block["block_name"]))

            # Subject list
            subj_names = ", ".join(s["code"] for s in subjects) if subjects else "None assigned"
            self.table.setItem(row, 1, QTableWidgetItem(subj_names))

            # Total hours
            total_hours = sum(s["units"] for s in subjects) if subjects else 0
            self.table.setItem(row, 2, QTableWidgetItem(f"{total_hours} hrs"))

            # Action buttons
            action_widget = QWidget()
            action_layout = QHBoxLayout(action_widget)
            action_layout.setContentsMargins(4, 2, 4, 2)
            action_layout.setSpacing(6)
            action_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

            assign_btn = QPushButton("Assign Subjects")
            assign_btn.setFixedSize(130, 32)
            assign_btn.setCursor(Qt.PointingHandCursor)
            assign_btn.setStyleSheet("""
                QPushButton {
                    background-color: #1152d4; color: #ffffff;
                    border: none; border-radius: 6px;
                    font-size: 12px; font-weight: 600;
                    padding: 4px 12px;
                }
                QPushButton:hover { background-color: #0d3fa3; }
            """)
            assign_btn.clicked.connect(
                lambda checked, b=block: self._assign_subjects(b)
            )
            action_layout.addWidget(assign_btn)

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
            del_btn.clicked.connect(
                lambda checked, bid=block["id"], bname=block["block_name"]: self._delete_block(bid, bname)
            )
            action_layout.addWidget(del_btn)
            action_layout.addStretch()

            self.table.setCellWidget(row, 3, action_widget)

    def _assign_subjects(self, block):
        dialog = AssignSubjectsDialog(block, self)
        if dialog.exec() == QDialog.Accepted:
            self.refresh_data()

    def _add_block(self):
        dialog = AddBlockDialog(self)
        if dialog.exec() == QDialog.Accepted:
            self.refresh_data()

    def _delete_block(self, block_id, block_name):
        reply = QMessageBox.question(
            self, "Delete Block",
            f"Are you sure you want to delete '{block_name}'?\n"
            f"This will also remove all subject assignments and schedule entries for this block.",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            from database import delete_block
            delete_block(block_id)
            self.refresh_data()

    def _filter_table(self, text: str):
        text = text.lower()
        for row in range(self.table.rowCount()):
            match = False
            for col in range(self.table.columnCount() - 1):
                item = self.table.item(row, col)
                if item and text in item.text().lower():
                    match = True
                    break
            self.table.setRowHidden(row, not match)
