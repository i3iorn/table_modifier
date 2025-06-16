from PyQt6.QtCore import Qt
from PyQt6.QtGui import QDragEnterEvent, QDropEvent
from PyQt6.QtWidgets import QLabel, QFrame

from table_modifier.signals import EMIT


class DropSlot(QLabel):
    def __init__(self, index, parent=None):
        super().__init__("", parent)
        self.index = index
        self.setAcceptDrops(True)
        self.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Sunken)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setFixedSize(200, 40)
        self.setWordWrap(True)
        self.has_content = False
        self.setStyleSheet("""
        background: #f9f9f9;
        """)
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
