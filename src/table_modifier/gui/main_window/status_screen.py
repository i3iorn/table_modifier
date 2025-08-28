from __future__ import annotations

from typing import Any, Optional

from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QProgressBar, QVBoxLayout, QWidget, QPlainTextEdit

from src.table_modifier.config.state import state
from src.table_modifier.localization import String
from src.table_modifier.signals import ON, EMIT


class StatusScreen(QWidget):
    """Processing status tab showing current mapping summary and progress.

    This is a preparation UI that reacts to app signals, ready to integrate with
    the actual processing pipeline. It displays a summary, a progress bar, and a log area.
    """

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._progress_value: int = 0
        self._timer: Optional[QTimer] = None
        self._init_ui()
        ON("status.update", self._on_status_update)
        ON("progress.update", self._on_progress_update)
        ON("processing.current.updated", self._on_current_updated)

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)

        title = QLabel(String["STATUS_TITLE"], self)
        title.setStyleSheet("font-size: 20px; font-weight: bold;")
        layout.addWidget(title)

        # Summary text
        self.summary = QLabel(String["STATUS_SUMMARY_DEFAULT"], self)
        self.summary.setWordWrap(True)
        layout.addWidget(self.summary)

        # Progress bar
        self.progress = QProgressBar(self)
        self.progress.setMinimum(0)
        self.progress.setMaximum(100)
        layout.addWidget(self.progress)

        # Control buttons
        buttons = QHBoxLayout()
        self.start_button = QPushButton(String["STATUS_START"], self)
        self.start_button.clicked.connect(self._on_start)
        buttons.addWidget(self.start_button)
        layout.addLayout(buttons)

        # Log output
        self.log = QPlainTextEdit(self)
        self.log.setReadOnly(True)
        layout.addWidget(self.log)

    def _on_status_update(self, sender: Any, msg: str, **kwargs: Any) -> None:
        # Also append to local log view
        self.log.appendPlainText(str(msg))

    def _on_progress_update(self, sender: Any, value: int, **kwargs: Any) -> None:
        self.progress.setValue(max(0, min(100, int(value))))

    def _on_current_updated(self, sender: Any, **kwargs: Any) -> None:
        current = state.controls.get("processing.current") or {}
        source = current.get("source")
        order = current.get("order", [])
        skips = current.get("skip_rows", [])
        self.summary.setText(
            String["STATUS_SUMMARY"].format(
                source=str(source or "-"),
                order=", ".join(order) if order else "-",
                skip_rows=", ".join(map(str, skips)) if skips else "-",
            )
        )

    def _on_start(self) -> None:
        # Placeholder demo progress; replace with real processing
        # Disable start to prevent re-entrancy
        self.start_button.setEnabled(False)
        self.log.appendPlainText(String["STATUS_PROCESSING_STARTED"])
        self._progress_value = 0
        self.progress.setValue(0)

        # Simulate work with a timer; emits periodic progress updates
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(150)

    def _tick(self) -> None:
        self._progress_value += 5
        if self._progress_value >= 100:
            self._progress_value = 100
            self.progress.setValue(100)
            if self._timer:
                self._timer.stop()
                self._timer = None
            self.log.appendPlainText(String["STATUS_PROCESSING_COMPLETE"])
            # Inform the app; e.g., could trigger export step next
            EMIT("processing.complete")
            # Re-enable start
            self.start_button.setEnabled(True)
        else:
            self.progress.setValue(self._progress_value)
            EMIT("status.update", msg=String["STATUS_PROGRESS"].format(value=self._progress_value))

