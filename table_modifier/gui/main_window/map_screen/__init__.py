import logging

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QListView,
    QLineEdit,
    QHBoxLayout,
    QDialog,
    QPushButton,
    QScrollArea,
)

from table_modifier.classifier import ColumnTypeClassifier, DetectorRegistry
from table_modifier.config.state import state
from table_modifier.constants import NO_MARGIN
from table_modifier.file_interface.excel import ExcelFileInterface
from table_modifier.file_interface.factory import FileInterfaceFactory
from table_modifier.gui.main_window.map_screen.draggable_label import DraggableLabel
from table_modifier.gui.main_window.map_screen.drop_slot import DropSlot
from table_modifier.localizer import String
from table_modifier.signals import ON


class MapScreen(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.skip_rows_input = None
        self.drop_slots = []

        # Canvas and drag-drop container
        self.map_widget = QScrollArea(self)
        self.map_widget.setWidgetResizable(True)
        self.drag_drop_container = QWidget()
        self.drag_drop_container.setStyleSheet("border: none;")
        self.drag_drop_layout = QHBoxLayout(self.drag_drop_container)
        self.drag_drop_layout.setContentsMargins(*NO_MARGIN)
        self.map_widget.setWidget(self.drag_drop_container)

        # Main UI setup
        self._init_layout()
        self._init_controls()
        self.layout().addWidget(self.map_widget)

    def _init_layout(self):
        main_layout = QVBoxLayout(self)
        self.setLayout(main_layout)

        # Title
        title = QLabel(String["MAP_SCREEN_TITLE"], self)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 24px; font-weight: bold;")
        main_layout.addWidget(title)

    def _init_controls(self):
        layout = self.layout()
        # Skip rows input
        self.skip_rows_input = QLineEdit(self)
        self.skip_rows_input.setPlaceholderText("Skip rows (e.g., 0,1,2)")
        self.skip_rows_input.setClearButtonEnabled(True)
        layout.addWidget(self.skip_rows_input)

        # Selected files view
        view = QListView(self)
        view.setModel(state.container.selected_files_model)
        view.setMaximumHeight(8 * 20)
        view.clicked.connect(self._on_item_clicked)
        layout.addWidget(view)

    def _drop_slots_available(self) -> bool:
        """Check if there are any available drop slots."""
        return any(slot.is_empty() for slot in self.drop_slots)

    def _on_item_clicked(self, index):
        if not index.isValid():
            return
        path = state.container.selected_files_model.data(
            index, role=Qt.ItemDataRole.UserRole
        )
        file_interface = FileInterfaceFactory.create(path)
        if isinstance(file_interface, ExcelFileInterface):
            self._show_sheet_dialog(file_interface)
        else:
            self._show_mapping(file_interface)

    def _show_sheet_dialog(self, file_interface: ExcelFileInterface):
        sheets = file_interface.get_sheets()
        if not sheets:
            self.logger.warning("No sheets found in Excel file.")
            return

        self.sheet_dialog = QDialog(self)
        layout = QVBoxLayout(self.sheet_dialog)
        self.sheet_dialog.setLayout(layout)
        layout.addWidget(QLabel("Select a sheet to map:"))

        for sheet in sheets:
            btn = QPushButton(sheet, self.sheet_dialog)
            btn.clicked.connect(lambda _, s=sheet: self._handle_sheet_selected(s))
            layout.addWidget(btn)

        self.sheet_dialog.exec()

    def _handle_sheet_selected(self, sheet_name: str):
        first_index = state.container.selected_files_model.index(0)
        path = state.container.selected_files_model.data(
            first_index, role=Qt.ItemDataRole.UserRole
        )
        file_interface = FileInterfaceFactory.create(path)
        file_interface.sheet_name = sheet_name
        self._show_mapping(file_interface)
        self.sheet_dialog.close()

    def _show_mapping(self, file_interface):
        self.logger.info(f"Mapping {file_interface}")
        headers = file_interface.get_headers()
        if not headers:
            self.logger.warning("No headers found.")
            return

        self._classify_columns(file_interface)
        self._clear_drag_drop()
        self._build_drag_drop(headers)
        ON("header.map.drop", self._on_header_drop)

    def _classify_columns(self, file_interface):
        classifier = ColumnTypeClassifier(DetectorRegistry)
        for col in file_interface.iter_columns(100):
            col_name = col.columns[0]
            result = classifier.classify(col[col_name].tolist(), col_name)
            self.logger.debug(f"Classified column '{col_name:<60s}': {str(result.candidates)} -- Example: {result.example_values}")

    def _clear_drag_drop(self):
        # Clear existing widgets and layouts
        for i in reversed(range(self.drag_drop_layout.count())):
            item = self.drag_drop_layout.itemAt(i)
            widget = item.widget()
            if widget:
                widget.deleteLater()
            else:
                layout = item.layout()
                if layout:
                    while layout.count():
                        child = layout.takeAt(0)
                        if child.widget():
                            child.widget().deleteLater()
        self.drop_slots.clear()

    def _build_drag_drop(self, headers):
        # --- LEFT COLUMN ---
        left_container = QWidget()
        left_layout = QVBoxLayout(left_container)
        left_layout.addWidget(QLabel("Available Headers"))
        for header in headers:
            label = DraggableLabel(header)
            left_layout.addWidget(label)

        left_layout.addStretch()

        left_scroll = QScrollArea()
        left_scroll.setWidgetResizable(True)
        left_scroll.setWidget(left_container)

        # --- RIGHT COLUMN ---
        right_container = QWidget()
        self.right_layout = QVBoxLayout(
            right_container)  # Store for drop slot addition
        self.right_layout.addWidget(QLabel("Target Mapping Order"))
        self._add_drop_slot(self.right_layout)
        self.right_layout.addStretch()

        right_scroll = QScrollArea()
        right_scroll.setWidgetResizable(True)
        right_scroll.setWidget(right_container)

        # Add scrollable containers to the main layout
        self.drag_drop_layout.addWidget(left_scroll)
        self.drag_drop_layout.addWidget(right_scroll)

    def _add_drop_slot(self, layout):
        slot = DropSlot(index=len(self.drop_slots))
        self.drop_slots.append(slot)
        layout.addWidget(slot)
        return slot

    def _on_header_drop(self, sender, text: str, **kwargs):
        # Remove stretch and add a new slot
        if not self._drop_slots_available():
            stretch = self.right_layout.takeAt(self.right_layout.count() - 1)
            self._add_drop_slot(self.right_layout)
            self.right_layout.addStretch()

    def _find_label_by_text(self, text):
        return next(
            (w for w in self.drag_drop_container.findChildren(DraggableLabel) if
             w.text() == text),
            None,
        )

    def get_new_order(self):
        return [slot.text() for slot in self.drop_slots if slot.text()]
