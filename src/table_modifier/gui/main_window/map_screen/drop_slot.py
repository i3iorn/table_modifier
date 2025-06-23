from PyQt6.QtCore import Qt
from PyQt6.QtGui import QDragEnterEvent, QDropEvent, QMouseEvent
from PyQt6.QtWidgets import QLabel, QFrame

from src.table_modifier.signals import EMIT, ON


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
        ON("header.map.double_click", self._on_doubleclick)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasText():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        text = event.mimeData().text()
        self._update_text(text)
        event.acceptProposedAction()

    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.deleteLater()
        event.accept()

    def is_empty(self) -> bool:
        return not self.has_content

    def _on_doubleclick(self, sender, text: str, **kwargs):
        if not self.has_content:
            self._update_text(text)
            return True
        return False

    def _update_text(self, text: str):
        self.setText(text)
        self.has_content = bool(text.strip())
        self.update_style()
        EMIT("header.map.drop", index=self.index, text=text)

    def update_style(self):
        if self.has_content:
            self.setStyleSheet("border: 2px solid green; border-radius: 6px;")
        else:
            self.setStyleSheet("border: 2px solid #ccc; border-radius: 6px;")
