from typing import Optional

from PyQt6.QtCore import Qt, QMimeData
from PyQt6.QtGui import QMouseEvent, QDrag, QPixmap
from PyQt6.QtWidgets import QLabel, QFrame

from src.table_modifier.signals import ON, EMIT


class DraggableLabel(QLabel):
    """A label that can be dragged into a DropSlot to form a mapping.

    Visual state:
    - Default: neutral border
    - While dragging: blue border
    - Mapped (present in any drop slot): green border
    """

    def __init__(self, text: str, parent: Optional[QFrame] = None):
        super().__init__(text, parent)
        self.setFrameStyle(QFrame.Shape.Panel | QFrame.Shadow.Raised)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setFixedSize(200, 40)
        self.setWordWrap(True)
        # Keep a base style and append border tweaks so we don't lose background/etc on updates
        self._base_style = (
            "background: #f0f0f0;"
            "border: 2px solid #ccc;"
            "border-radius: 6px;"
        )
        self.is_dragging = False
        self.update_style()
        # Update visuals on drops, double-click inserts, and any mapping change
        ON("header.map.drop", self.update_style)
        ON("header.map.double_click", self.update_style)
        ON("header.map.changed", self.update_style)

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

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        EMIT("header.map.double_click", text=self.text())
        event.accept()

    def update_style(self, sender=None, **kwargs):
        """Update visual style according to mapping state and interaction.

        Priority order:
        1) If explicit order is provided (from 'header.map.changed'), mark green when in order
        2) If a drop happened for this label's text, mark green
        3) If currently dragging, mark blue
        4) Default neutral
        """
        border_color = "#ccc"
        if "order" in kwargs:
            try:
                if self.text() in (kwargs.get("order") or []):
                    border_color = "green"
            except Exception:
                pass
        elif kwargs.get("text", None) == self.text():
            border_color = "green"
        elif self.is_dragging:
            border_color = "#3399ff"
        # apply combined style
        self.setStyleSheet(f"{self._base_style} border: 2px solid {border_color}; border-radius: 6px;")
