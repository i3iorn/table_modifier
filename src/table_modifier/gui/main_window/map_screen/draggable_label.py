from typing import Optional

from PyQt6.QtCore import Qt, QMimeData
from PyQt6.QtGui import QMouseEvent, QDrag, QPixmap
from PyQt6.QtWidgets import QLabel, QFrame

from src.table_modifier.signals import ON, EMIT


class DraggableLabel(QLabel):
    """A label that can be dragged into a DropSlot to form a mapping.

    Visual state is driven by QSS using dynamic properties:
    - property 'dragging': true while being dragged
    - property 'mapped': true when present in any drop slot (per 'order')
    """

    def __init__(self, text: str, parent: Optional[QFrame] = None):
        super().__init__(text, parent)
        self.setObjectName("draggableLabel")
        self.setFrameStyle(QFrame.Shape.Panel | QFrame.Shadow.Raised)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setFixedSize(200, 40)
        self.setWordWrap(True)
        # initial properties
        self.setProperty("dragging", False)
        self.setProperty("mapped", False)
        self._repolish()
        # Update visuals on drops, double-click inserts, and any mapping change
        ON("header.map.drop", self.update_style)
        ON("header.map.double_click", self.update_style)
        ON("header.map.changed", self.update_style)

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.setProperty("dragging", True)
            self._repolish()

            drag = QDrag(self)
            mime_data = QMimeData()
            mime_data.setText(self.text())
            drag.setMimeData(mime_data)

            pixmap = QPixmap(self.size())
            self.render(pixmap)
            drag.setPixmap(pixmap)

            drag.exec(Qt.DropAction.MoveAction)

            self.setProperty("dragging", False)
            self._repolish()

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        EMIT("header.map.double_click", text=self.text())
        event.accept()

    def update_style(self, sender=None, **kwargs):
        """Update dynamic properties according to mapping state and interaction."""
        mapped = False
        if "order" in kwargs:
            try:
                mapped = self.text() in (kwargs.get("order") or [])
            except Exception:
                mapped = False
        elif kwargs.get("text", None) == self.text():
            mapped = True
        self.setProperty("mapped", bool(mapped))
        self._repolish()

    def _repolish(self) -> None:
        # Re-apply style to reflect dynamic property changes
        st = self.style()
        st.unpolish(self)
        st.polish(self)
        self.update()
