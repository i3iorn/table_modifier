from pathlib import Path

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel, QLineEdit, QCompleter, \
    QSpacerItem, QSizePolicy, QPushButton

from table_modifier.gui.emitter import signal_emitter


class FolderSelectorWidget(QWidget):
    """
    A widget for selecting a folder.
    This widget can be used to select a folder and display its contents.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.open_button = None
        self._debounce_folder_timer = None
        self.folder_input = None
        self.setLayout(QHBoxLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.layout().setSpacing(0)
        
        self.init_ui()
        
    def init_ui(self):
        self._debounce_folder_timer = QTimer(self)
        self._debounce_folder_timer.setSingleShot(True)
        self._debounce_folder_timer.timeout.connect(self._process_folder_selection)

        self.layout().addWidget(
            QLabel("Select a folder: ", self)
        )
        self.folder_input = QLineEdit(self)
        
        # Set up a completer for the line edit to allow folder name completion
        completer = QCompleter(self)
        completer.setCompletionMode(QCompleter.CompletionMode.UnfilteredPopupCompletion)
        completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.folder_input.setCompleter(completer)
        self.folder_input.setPlaceholderText("Type folder name...")
        self.folder_input.setClearButtonEnabled(True)
        self.folder_input.setMinimumWidth(200)
        self.folder_input.textChanged.connect(lambda: self._debounce_folder_timer.start(300))

        self.layout().addWidget(self.folder_input)
        self.folder_input.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        self.open_button = QPushButton("Folder", self)
        self.open_button.setToolTip("Select folder")
        self.open_button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.open_button.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Maximum)
        self.open_button.clicked.connect(self.folder_input.setFocus)
        self.layout().addWidget(self.open_button)

        self.open_button.clicked.connect(self.on_open_button_clicked)

    def _process_folder_selection(self):
        """
        Process the folder selection after a debounce period.

        This method is called when the user stops typing in the folder input field.
        It can be used to update the state or perform actions based on the selected folder.
        """
        folder = self.folder_input.text().strip()
        if folder and Path(folder).is_dir():
            signal_emitter.folderUpdated.emit(folder)

    def on_open_button_clicked(self):
        """
        Handle the click event of the open button.

        This method is called when the open button is clicked. It opens the filedialog
        to select a folder and updates the input field with the selected folder path.
        """
        from PyQt6.QtWidgets import QFileDialog
        folder = QFileDialog.getExistingDirectory(self, "Select Folder", self.folder_input.text().strip())
        if folder:
            self.folder_input.setFocus()
            self.folder_input.setText(folder)
            self._process_folder_selection()