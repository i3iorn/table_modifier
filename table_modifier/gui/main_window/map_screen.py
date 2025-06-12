import logging

from PyQt6.QtCore import Qt, QMimeData, QPointF
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QSpacerItem, QSizePolicy, \
    QListView, QLineEdit, QHBoxLayout, QDialog, QPushButton

from table_modifier.config.state import state
from table_modifier.file_interface.excel import ExcelFileInterface
from table_modifier.file_interface.factory import FileInterfaceFactory
from table_modifier.localizer import String
from table_modifier.signals import EMIT, ON

from PyQt6.QtGui import QDragEnterEvent, QDropEvent, QDrag, QPixmap, QMouseEvent, QPainter, QPen
from PyQt6.QtWidgets import QListWidget, QListWidgetItem, QFrame

class DraggableLabel(QLabel):
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setFrameStyle(QFrame.Shape.Panel | QFrame.Shadow.Raised)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setFixedSize(100, 40)
        self.setStyleSheet("border: 2px solid transparent; border-radius: 6px;")
        self.is_dragging = False
        self.update_style()
        ON("header.map.drop", self.update_style)

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_dragging = True
            self.update_style()

            drag = QDrag(self)
            mime_data = QMimeData()
            mime_data.setText(self.text())
            drag.setMimeData(mime_data)

            pixmap = QPixmap(self.size())
            self.render(pixmap)
            drag.setPixmap(pixmap)

            drag.exec(Qt.DropAction.MoveAction)

            self.is_dragging = False
            self.update_style()

    def update_style(self, sender=None, **kwargs):
        if sender and kwargs.get("text", None) == self.text():
            self.setStyleSheet("border: 2px solid green; border-radius: 6px;")
        else:
            if self.is_dragging:
                self.setStyleSheet("border: 2px solid #3399ff; border-radius: 6px;")
            else:
                self.setStyleSheet("border: 2px solid #ccc; border-radius: 6px;")



class DropSlot(QLabel):
    def __init__(self, index, parent=None):
        super().__init__("", parent)
        self.index = index
        self.setAcceptDrops(True)
        self.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Sunken)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setFixedSize(120, 40)
        self.has_content = False
        self.update_style()

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasText():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        text = event.mimeData().text()
        self.setText(text)
        self.has_content = True
        self.update_style()
        EMIT("header.map.drop", index=self.index, text=text)
        event.acceptProposedAction()

    def update_style(self):
        if self.has_content:
            self.setStyleSheet("border: 2px solid green; border-radius: 6px;")
        else:
            self.setStyleSheet("border: 2px solid #ccc; border-radius: 6px;")


class MappingCanvas(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.mappings: list[tuple[QLabel, DropSlot]] = []
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setStyleSheet("background: transparent;")

    def add_mapping(self, source: QLabel, target: DropSlot):
        self.mappings.append((source, target))
        self.update()

    def clear_mappings(self):
        self.mappings.clear()
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        pen = QPen(Qt.GlobalColor.darkBlue, 2)
        painter.setPen(pen)

        for source, target in self.mappings:
            if not source.isVisible() or not target.isVisible():
                continue

            try:
                start_center = source.rect().center()
                end_center = target.rect().center()

                start_global = source.mapToGlobal(start_center)
                end_global = target.mapToGlobal(end_center)

                start_local = self.mapFromGlobal(start_global)
                end_local = self.mapFromGlobal(end_global)

                painter.drawLine(QPointF(start_local), QPointF(end_local))
            except RuntimeError as e:
                # Sometimes happens if widget is being destroyed or re-parented
                continue

        painter.end()


class MapScreen(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.map_widget = None
        self.controls = None
        self.setLayout(QVBoxLayout())
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.canvas = MappingCanvas(self)
        self.canvas.setGeometry(0, 0, self.width(), self.height())
        self.init_ui()

    def init_ui(self):
        title_label = QLabel(String["MAP_SCREEN_TITLE"], self)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("font-size: 24px; font-weight: bold;")
        self.layout().addWidget(title_label)

        # Add controls
        self.skip_rows_input = QLineEdit(self)
        self.skip_rows_input.setPlaceholderText("Skip rows (e.g., 0,1,2)")
        self.skip_rows_input.setClearButtonEnabled(True)
        self.skip_rows_input.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.layout().addWidget(self.skip_rows_input)

        selected = QListView(self)
        selected.setModel(state.container.selected_files_model)
        selected.setMaximumHeight(8 * 20)
        self.layout().addWidget(selected)

        # Add a spacer to push the controls to the top
        spacer = QSpacerItem(1, 1, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        self.layout().addItem(spacer)

        selected.clicked.connect(self.on_item_clicked)

    def on_item_clicked(self, index):
        """
        Handle item click event in the selected files view.

        Args:
            index: QModelIndex
                The index of the clicked item in the selected files view.

        Returns:
            None
        """
        if index.isValid():
            file_path = state.container.selected_files_model.data(index, role=Qt.ItemDataRole.UserRole)
            file_interface = FileInterfaceFactory.create(file_path)
            if isinstance(file_interface, ExcelFileInterface):
                self.show_sheet_selection_dialog(file_interface)
            else:
                self.show_mapping(file_interface)

    def show_sheet_selection_dialog(self, file_interface):
        """
        Show a dialog to select a sheet from the Excel file.

        Args:
            file_interface: ExcelFileInterface
                The file interface for the selected Excel file.

        Returns:
            None
        """
        sheets = file_interface.get_sheets()
        if not sheets:
            self.logger.warning("No sheets found in the selected Excel file.")
            return

        self.sheet_dialog = QDialog(self)
        self.sheet_dialog.setWindowTitle("Select Sheet")
        self.sheet_dialog.setLayout(QVBoxLayout())
        label = QLabel("Select a sheet to map:")
        self.sheet_dialog.layout().addWidget(label)
        for sheet in sheets:
            button = QPushButton(sheet, self.sheet_dialog)
            button.clicked.connect(self.handle_mapping_response)
            self.sheet_dialog.layout().addWidget(button)

        self.sheet_dialog.exec()

    def handle_mapping_response(self):
        """
        Handle the response from the sheet selection dialog.

        This method is called when a sheet button is clicked in the sheet selection dialog.
        It retrieves the selected sheet name and calls the show_mapping method to display
        the mapping interface for that sheet.

        Returns:
            None
        """
        button: QPushButton = self.sender()
        if button:
            sheet_name = button
            file_interface = FileInterfaceFactory.create(state.container.selected_files_model.data(
                state.container.selected_files_model.index(0), role=Qt.ItemDataRole.UserRole))
            self.show_mapping(file_interface, sheet_name)

    def show_mapping(self, file_interface, sheet_name=None):
        self.logger.info(
            f"Showing mapping for {file_interface} with sheet {sheet_name}")

        headers = file_interface.get_headers(sheet_name)

        if not headers:
            self.logger.warning("No headers found.")
            return

        if self.map_widget:
            self.map_widget.close()
            self.map_widget = None

        self.map_widget = QWidget(self)
        self.map_widget.setWindowTitle("Map Headers")
        layout = QHBoxLayout(self.map_widget)

        # Left column (draggables)
        left_col = QVBoxLayout()
        left_label = QLabel("Available Headers")
        left_col.addWidget(left_label)

        for header in headers:
            label = DraggableLabel(header)
            left_col.addWidget(label)

        left_col.addStretch()

        # Right column (droppables)
        right_col = QVBoxLayout()
        right_label = QLabel("Target Mapping Order")
        right_col.addWidget(right_label)

        self.drop_slots = []
        for i in range(len(headers)):
            slot = DropSlot(index=i)
            self.drop_slots.append(slot)
            right_col.addWidget(slot)

        right_col.addStretch()

        layout.addLayout(left_col)
        layout.addLayout(right_col)

        self.map_widget.setLayout(layout)
        self.layout().addWidget(self.map_widget)
        ON("header.map.drop", self.on_header_drop)

    def on_header_drop(self, sender, **kwargs):
        """
        Handle the drop event for headers and draw mapping arrow.

        Args:
            sender: str (event name, unused)
            index: int
                The index of the drop slot.
            text: str
                The dropped header label.

        Returns:
            None
        """
        index = kwargs.get("index")
        text = kwargs.get("text")

        # Match DraggableLabel by text
        source_label = next((child for child in self.map_widget.findChildren(DraggableLabel) if child.text() == text),
                            None)

        if source_label:
            drop_slot = self.drop_slots[index]
            self.canvas.add_mapping(source_label, drop_slot)

    def get_new_order(self):
        """
        Get the new order of headers based on the drop slots.

        Returns:
            list: A list of headers in the new order.
        """
        new_order = []
        for slot in self.drop_slots:
            if slot.text():
                new_order.append(slot.text())
        return new_order

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.canvas.setGeometry(0, 0, self.width(), self.height())