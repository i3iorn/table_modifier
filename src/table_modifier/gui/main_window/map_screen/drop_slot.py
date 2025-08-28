from PyQt6.QtCore import Qt, QMimeData
from PyQt6.QtGui import QDragEnterEvent, QDropEvent, QMouseEvent, QDrag, QPixmap
from PyQt6.QtWidgets import QLabel, QFrame

from src.table_modifier.signals import EMIT


class DropSlot(QLabel):
    def __init__(self, index: int, parent=None):
        super().__init__("", parent)
        self.index = index
        self.setAcceptDrops(True)
        self.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Sunken)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setFixedSize(200, 40)
        self.setWordWrap(True)
        self.has_content = False
        self.setStyleSheet(
            """
        background: #f9f9f9;
        border: 2px solid #ccc; border-radius: 6px;
        """
        )
        self.update_style()

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasText():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        text = event.mimeData().text()
        self.set_text(text)
        event.acceptProposedAction()

    def mousePressEvent(self, event: QMouseEvent) -> None:
        # Allow dragging this slot's content to reorder/move mappings
        if event.button() == Qt.MouseButton.LeftButton and self.has_content:
            drag = QDrag(self)
            mime_data = QMimeData()
            mime_data.setText(self.text())
            drag.setMimeData(mime_data)
            pixmap = QPixmap(self.size())
            self.render(pixmap)
            drag.setPixmap(pixmap)
            drag.exec(Qt.DropAction.MoveAction)
        else:
            super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            # Clear content on double click instead of deleting the slot widget
            self.clear()
        event.accept()

    def is_empty(self) -> bool:
        return not self.has_content

    # Public API for MapScreen
    def clear(self) -> None:
        self.set_text("")

    def set_text(self, text: str) -> None:
        self.setText(text)
        self.has_content = bool(text.strip())
        self.update_style()
        # Notify about the change; MapScreen will dedupe, add slots if needed, and emit order-changed
        EMIT("header.map.drop", index=self.index, text=text)

    def update_style(self):
        if self.has_content:
            self.setStyleSheet("border: 2px solid green; border-radius: 6px;")
        else:
            self.setStyleSheet("border: 2px solid #ccc; border-radius: 6px;")
