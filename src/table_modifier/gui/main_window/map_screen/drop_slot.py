from typing import List

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QDragEnterEvent, QDropEvent, QMouseEvent
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QFrame,
    QLineEdit,
    QHBoxLayout,
)

from src.table_modifier.signals import EMIT


class DropSlot(QWidget):
    def __init__(self, index: int, parent=None):
        super().__init__(parent)
        self.index = index
        self.setObjectName("dropSlot")
        self.setAcceptDrops(True)
        self.sources: List[str] = []
        self._default_sep = " "

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)

        # Display of combined sources
        self.display = QLabel("", self)
        self.display.setFrameStyle(QFrame.Shape.NoFrame)
        self.display.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.display.setWordWrap(True)
        layout.addWidget(self.display)

        # Separator editor row
        sep_row = QHBoxLayout()
        sep_label = QLabel("Sep:", self)
        self.sep_input = QLineEdit(self)
        self.sep_input.setPlaceholderText(self._default_sep)
        self.sep_input.setMaxLength(8)
        self.sep_input.setFixedWidth(80)
        self.sep_input.textChanged.connect(self._on_sep_changed)
        sep_row.addWidget(sep_label)
        sep_row.addWidget(self.sep_input)
        sep_row.addStretch(1)
        layout.addLayout(sep_row)

        # initial property for QSS
        self.setProperty("filled", False)
        self._refresh_display()
        self._repolish()

    # Drag-n-drop API
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasText():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        text = event.mimeData().text().strip()
        if text:
            self.add_source(text)
        event.acceptProposedAction()

    # Mouse interactions
    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            # Clear all on double click
            self.clear()
        event.accept()

    # Public API expected by MapScreen
    def is_empty(self) -> bool:
        return len(self.sources) == 0

    def clear(self) -> None:
        self.sources.clear()
        self._refresh_display()
        self._update_filled()
        EMIT("header.map.drop", index=self.index, text="")

    # Compatibility: MapScreen may call set_text on double-click add
    def set_text(self, text: str) -> None:
        text = (text or "").strip()
        if not text:
            self.clear()
            return
        self.add_source(text)

    def text(self) -> str:
        # Legacy single-string representation
        return ", ".join(self.sources)

    # New richer API
    def add_source(self, text: str) -> None:
        if text in self.sources:
            return
        self.sources.append(text)
        self._refresh_display()
        self._update_filled()
        EMIT("header.map.drop", index=self.index, text=text)

    def has_source(self, text: str) -> bool:
        return text in self.sources

    def remove_source(self, text: str) -> None:
        if text in self.sources:
            self.sources.remove(text)
            self._refresh_display()
            self._update_filled()
            EMIT("header.map.drop", index=self.index, text="")

    def get_sources(self) -> List[str]:
        return list(self.sources)

    def get_separator(self) -> str:
        return self.sep_input.text() if self.sep_input.text() != "" else self._default_sep

    def set_from(self, sources: List[str], separator: str | None = None) -> None:
        self.sources = [s for s in (sources or []) if s]
        if separator is not None:
            self.sep_input.setText(str(separator))
        self._refresh_display()
        self._update_filled()

    # Internals
    def _refresh_display(self) -> None:
        if self.sources:
            # Show sources separated by current separator
            sep = self.get_separator()
            preview = f" {sep} ".join(self.sources)
            self.display.setText(preview)
        else:
            self.display.setText("<drop headers here>")

    def _update_filled(self) -> None:
        self.setProperty("filled", not self.is_empty())
        self._repolish()

    def _on_sep_changed(self, _text: str) -> None:
        # Update preview immediately when separator changes
        self._refresh_display()

    def _repolish(self) -> None:
        st = self.style()
        st.unpolish(self)
        st.polish(self)
        self.update()
