import logging

from PyQt6.QtCore import Qt, QMimeData
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QSpacerItem, QSizePolicy, \
    QListView, QLineEdit, QHBoxLayout, QDialog, QPushButton

from table_modifier.config.state import state
from table_modifier.file_interface.excel import ExcelFileInterface
from table_modifier.file_interface.factory import FileInterfaceFactory
from table_modifier.localizer import String
from table_modifier.signals import EMIT


from PyQt6.QtGui import QDragEnterEvent, QDropEvent, QDrag, QPixmap, QMouseEvent
from PyQt6.QtWidgets import QListWidget, QListWidgetItem, QFrame

class DraggableLabel(QLabel):
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setFrameStyle(QFrame.Shape.Panel | QFrame.Shadow.Raised)
        self.setStyleSheet("background-color: lightgray; padding: 4px; margin: 2px;")
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setFixedSize(100, 40)

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            drag = QDrag(self)
            mime_data = QMimeData()
            mime_data.setText(self.text())
            drag.setMimeData(mime_data)

            pixmap = QPixmap(self.size())
            self.render(pixmap)
            drag.setPixmap(pixmap)
            drag.exec(Qt.DropAction.MoveAction)


class DropSlot(QLabel):
    def __init__(self, index, parent=None):
        super().__init__("", parent)
        self.index = index
        self.setAcceptDrops(True)
        self.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Sunken)
        self.setStyleSheet("background-color: white; border: 1px dashed gray;")
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setFixedSize(120, 40)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasText():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        text = event.mimeData().text()
        self.setText(text)
        self.setStyleSheet("background-color: lightblue; border: 1px solid blue;")
        event.acceptProposedAction()



class MapScreen(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.controls = None
        self.setLayout(QVBoxLayout())
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
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

        dialog = QDialog(self)
        dialog.setWindowTitle("Map Headers")
        layout = QHBoxLayout(dialog)

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

        dialog.setLayout(layout)
        dialog.resize(600, 400)
        dialog.exec()