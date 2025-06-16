from PyQt6.QtCore import Qt, QMimeData
from PyQt6.QtGui import QMouseEvent, QDrag, QPixmap
from PyQt6.QtWidgets import QLabel, QFrame

from table_modifier.signals import ON


class DraggableLabel(QLabel):
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setFrameStyle(QFrame.Shape.Panel | QFrame.Shadow.Raised)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setFixedSize(200, 40)
        self.setWordWrap(True)
        self.setStyleSheet("""
        background: #f0f0f0;
        border: 2px solid transparent; 
        border-radius: 6px;
        """)
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
