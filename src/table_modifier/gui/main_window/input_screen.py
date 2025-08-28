"""Input screen for selecting source folder and files."""

from typing import Optional

from platformdirs import user_downloads_dir

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QVBoxLayout, QSpacerItem, QSizePolicy, QWidget, QLabel

from src.table_modifier.gui.main_window.file_selector import FileSelectorWidget
from src.table_modifier.gui.main_window.folder_selector import FolderSelectorWidget
from src.table_modifier.localization import String
from src.table_modifier.signals import EMIT


class InputScreen(QWidget):
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.main_layout = QVBoxLayout()
        self.setLayout(self.main_layout)
        self.init_ui()

    def init_ui(self) -> None:
        title_label = QLabel(String["INPUT_SCREEN_TITLE"], self)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("font-size: 24px; font-weight: bold;")
        self.main_layout.addWidget(title_label)

        self.init_folder_selector()
        self.init_file_selector()

        # Emit default directory selection to initialize downstream widgets.
        EMIT("directory.updated", directory=user_downloads_dir())

    def init_folder_selector(self) -> None:
        self.folder_selector = FolderSelectorWidget(self)
        self.main_layout.addWidget(self.folder_selector)

    def init_file_selector(self) -> None:
        self.file_selector = FileSelectorWidget(self)
        self.main_layout.addWidget(self.file_selector)
