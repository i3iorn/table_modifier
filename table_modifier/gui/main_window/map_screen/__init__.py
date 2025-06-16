import logging

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QSpacerItem,
    QSizePolicy,
    QListView,
    QLineEdit,
    QHBoxLayout,
    QDialog,
    QPushButton,
    QScrollArea,
)

from table_modifier.classifier import ColumnTypeClassifier, DetectorRegistry
from table_modifier.config.state import state
from table_modifier.file_interface.excel import ExcelFileInterface
from table_modifier.file_interface.factory import FileInterfaceFactory
from table_modifier.gui.main_window.map_screen.canvas import MappingCanvas
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
        self.sheet_dialog = None

        # Canvas and drag-drop container
        self.map_widget = QScrollArea(self)
        self.map_widget.setWidgetResizable(True)
        self.drag_drop_container = QWidget()
        self.drag_drop_layout = QHBoxLayout(self.drag_drop_container)
        self.map_widget.setWidget(self.drag_drop_container)

        # Main UI setup
        self._init_layout()
        self._init_controls()
        self.layout().addWidget(self.map_widget)

        self.canvas = MappingCanvas(self)
        self.canvas.setGeometry(0, 0, self.width(), self.height())

    def _init_layout(self):
        main_layout = QVBoxLayout(self)
        self.setLayout(main_layout)

        # Title
        title = QLabel(String["MAP_SCREEN_TITLE"], self)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 24px; font-weight: bold;")
        main_layout.addWidget(title)

        # Spacer for controls
        """
        main_layout.addItem(
            QSpacerItem(1, 1, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        )
        """

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

        dialog = QDialog(self)
        layout = QVBoxLayout(dialog)
        dialog.setLayout(layout)
        layout.addWidget(QLabel("Select a sheet to map:"))

        for sheet in sheets:
            btn = QPushButton(sheet, dialog)
            btn.clicked.connect(lambda _, s=sheet: self._handle_sheet_selected(s))
            layout.addWidget(btn)

        dialog.exec()

    def _handle_sheet_selected(self, sheet_name: str):
        self.sheet_dialog.accept() if self.sheet_dialog else None
        first_index = state.container.selected_files_model.index(0)
        path = state.container.selected_files_model.data(
            first_index, role=Qt.ItemDataRole.UserRole
        )
        file_interface = FileInterfaceFactory.create(path)
        self._show_mapping(file_interface, sheet_name)

    def _show_mapping(self, file_interface, sheet_name=None):
        self.logger.info(f"Mapping {file_interface} sheet={sheet_name}")
        headers = file_interface.get_headers(sheet_name)
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
            self.logger.info(classifier.classify(list(col)).candidates)

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
        # Left: available headers
        left_layout = QVBoxLayout()
        left_layout.addWidget(QLabel("Available Headers"))
        for header in headers:
            left_layout.addWidget(DraggableLabel(header))
        left_layout.addStretch()

        # Right: target mapping slots
        right_layout = QVBoxLayout()
        right_layout.addWidget(QLabel("Target Mapping Order"))
        self._add_drop_slot(right_layout)
        right_layout.addStretch()

        self.drag_drop_layout.addLayout(left_layout)
        self.drag_drop_layout.addLayout(right_layout)

    def _add_drop_slot(self, layout):
        slot = DropSlot(index=len(self.drop_slots))
        self.drop_slots.append(slot)
        layout.addWidget(slot)
        return slot

    def _on_header_drop(self, sender, index: int, text: str, **kwargs):
        src = self._find_label_by_text(text)
        if src:
            self.canvas.add_mapping(src, self.drop_slots[index])
        # Extend slots
        right_layout = self.drag_drop_layout.itemAt(1).layout()
        right_layout.removeItem(right_layout.itemAt(right_layout.count() - 1))
        self._add_drop_slot(right_layout)
        right_layout.addStretch()

    def _find_label_by_text(self, text):
        return next(
            (w for w in self.drag_drop_container.findChildren(DraggableLabel) if
             w.text() == text),
            None,
        )

    def get_new_order(self):
        return [slot.text() for slot in self.drop_slots if slot.text()]

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.canvas.setGeometry(0, 0, self.width(), self.height())
