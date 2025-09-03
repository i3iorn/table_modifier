from typing import Optional

from PyQt6.QtCore import Qt, QMimeData, QPoint
from PyQt6.QtGui import QMouseEvent, QDrag, QPixmap, QKeyEvent
from PyQt6.QtWidgets import QLabel, QFrame, QLineEdit, QApplication

from src.table_modifier.signals import ON, EMIT


class DraggableLabel(QLabel):
    """A label that can be edited and dragged."""

    def __init__(self, text: str, parent: Optional[QFrame] = None):
        super().__init__(text, parent)
        self.setObjectName("draggableLabel")
        self.setFrameStyle(QFrame.Shape.Panel | QFrame.Shadow.Raised)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setFixedSize(200, 40)
        self.setWordWrap(True)

        self._editor = QLineEdit(self)
        self._editor.setFixedSize(self.size())
        self._editor.setMouseTracking(True)
        self._editor.setCursor(Qt.CursorShape.IBeamCursor)
        self._editor.hide()
        self._editor.returnPressed.connect(self.conclude_edit)
        self._editor.focusOutEvent = self._editor_focus_out_event

        self._drag_start_pos = QPoint()

        self.setProperty("dragging", False)
        self.setProperty("mapped", False)
        self._repolish()

        ON("header.map.drop", self.update_style)
        ON("header.map.double_click", self.update_style)
        ON("header.map.changed", self.update_style)

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_start_pos = event.pos()

    def mouseMoveEvent(self, event: QMouseEvent):
        if not (event.buttons() & Qt.MouseButton.LeftButton):
            return

        distance = (event.pos() - self._drag_start_pos).manhattanLength()
        if distance < QApplication.startDragDistance():
            return

        self.conclude_edit()

        # Start drag
        self.setProperty("dragging", True)
        self._repolish()

        drag = QDrag(self)
        mime_data = QMimeData()
        mime_data.setData("application/x-header-text", self.text().encode())
        drag.setMimeData(mime_data)

        pixmap = QPixmap(self.size())
        self.render(pixmap)
        drag.setPixmap(pixmap)

        drag.exec(Qt.DropAction.MoveAction)

        self.setProperty("dragging", False)
        self._repolish()

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            if not self._editor.isVisible():
                self._editor.setText(self.text())
                self._editor.show()
                self._editor.setFocus()

    def conclude_edit(self) -> None:
        if self._editor.isVisible():
            self.setText(self._editor.text())
            self._editor.clear()
            self._editor.hide()
            self._repolish()

    def _editor_focus_out_event(self, event):
        self.conclude_edit()
        QLineEdit.focusOutEvent(self._editor, event)

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        EMIT("header.map.double_click", text=self.text())
        event.accept()

    def update_style(self, sender=None, **kwargs):
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
        st = self.style()
        st.unpolish(self)
        st.polish(self)
        self.update()
