from PyQt6.QtCore import Qt, QPointF
from PyQt6.QtGui import QPainter, QPen
from PyQt6.QtWidgets import QWidget, QLabel

from table_modifier.gui.main_window.map_screen.drop_slot import DropSlot


class MappingCanvas(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.mappings: list[tuple[QLabel, DropSlot]] = []
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setStyleSheet("background: transparent;")

    def add_mapping(self, source: QLabel, target: DropSlot):
        self.mappings.append((source, target))
        self.update()

    def clear_mappings(self):
        self.mappings.clear()
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        pen = QPen(Qt.GlobalColor.darkBlue, 2)
        painter.setPen(pen)

        for source, target in self.mappings:
            if not source.isVisible() or not target.isVisible():
                continue

            try:
                start_center = source.rect().center()
                end_center = target.rect().center()

                start_global = source.mapToGlobal(start_center)
                end_global = target.mapToGlobal(end_center)

                start_local = self.mapFromGlobal(start_global)
                end_local = self.mapFromGlobal(end_global)

                painter.drawLine(QPointF(start_local), QPointF(end_local))
            except RuntimeError as e:
                # Sometimes happens if widget is being destroyed or re-parented
                continue

        painter.end()
