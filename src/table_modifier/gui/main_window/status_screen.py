from typing import Any, Optional
import os
from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QProgressBar,
    QVBoxLayout,
    QWidget,
    QPlainTextEdit,
    QLineEdit,
    QFileDialog,
    QCheckBox,
)

from src.table_modifier.config.state import state
from src.table_modifier.file_interface.factory import FileInterfaceFactory
from src.table_modifier.gui.main_window.map_screen.utils import parse_skip_rows
from src.table_modifier.localization import String
from src.table_modifier.processing.transform import apply_mapping
from src.table_modifier.signals import ON, EMIT
from src.table_modifier.processing.engine import ensure_engine_listener


class StatusScreen(QWidget):
    """Processing status tab showing current mapping summary and progress.

    Displays summary, controls, progress, and log. Integrates with processing engine.
    """

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._timer: Optional[QTimer] = None
        self._output_file: Optional[str] = None
        self._init_ui()
        # Ensure engine is listening for start/cancel events
        ensure_engine_listener()
        ON("status.update", self._on_status_update)
        ON("progress.update", self._on_progress_update)
        ON("processing.current.updated", self._on_current_updated)
        ON("processing.complete", self._on_complete)
        ON("processing.canceled", self._on_canceled)
        ON("processing.error", self._on_error)

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)

        title = QLabel(String["STATUS_TITLE"], self)
        title.setObjectName("screenTitle")
        layout.addWidget(title)

        # Summary text
        self.summary = QLabel(String["STATUS_SUMMARY_DEFAULT"], self)
        self.summary.setWordWrap(True)
        layout.addWidget(self.summary)

        # Output path row
        out_row = QHBoxLayout()
        out_row.addWidget(QLabel(String.get("STATUS_OUTPUT", "Output:"), self))
        self.output_path = QLineEdit(self)
        self.output_path.setPlaceholderText(String.get("STATUS_OUTPUT_PLACEHOLDER", "Choose output file (optional)"))
        self.output_path.setClearButtonEnabled(True)
        self.output_path.textChanged.connect(self._on_output_changed)
        out_row.addWidget(self.output_path, 1)
        browse = QPushButton(String.get("STATUS_BROWSE", "Browse"), self)
        browse.clicked.connect(self._on_browse)
        out_row.addWidget(browse)
        layout.addLayout(out_row)

        # Strict mode
        strict_row = QHBoxLayout()
        self.strict_chk = QCheckBox(String.get("STATUS_STRICT", "Strict mode (fail on missing columns)"), self)
        self.strict_chk.stateChanged.connect(self._on_strict_changed)
        strict_row.addWidget(self.strict_chk)
        strict_row.addStretch(1)
        layout.addLayout(strict_row)

        # Progress bar + text
        prog_row = QHBoxLayout()
        self.progress = QProgressBar(self)
        self.progress.setMinimum(0)
        self.progress.setMaximum(100)
        prog_row.addWidget(self.progress, 1)
        self.progress_label = QLabel("0%", self)
        prog_row.addWidget(self.progress_label)
        layout.addLayout(prog_row)

        # Elapsed & throughput
        metrics_row = QHBoxLayout()
        self.elapsed_label = QLabel("Elapsed: -", self)
        metrics_row.addWidget(self.elapsed_label)
        self.throughput_label = QLabel("Throughput: - rows/s", self)
        metrics_row.addWidget(self.throughput_label)
        metrics_row.addStretch(1)
        layout.addLayout(metrics_row)

        # Control buttons
        buttons = QHBoxLayout()
        self.start_button = QPushButton(String.get("STATUS_START", "Start"), self)
        self.start_button.clicked.connect(self._on_start)
        buttons.addWidget(self.start_button)
        self.cancel_button = QPushButton(String.get("STATUS_CANCEL", "Cancel"), self)
        self.cancel_button.clicked.connect(self._on_cancel)
        self.cancel_button.setEnabled(False)
        buttons.addWidget(self.cancel_button)
        self.preview_button = QPushButton(String.get("STATUS_PREVIEW", "Preview"), self)
        self.preview_button.clicked.connect(self._on_preview)
        buttons.addWidget(self.preview_button)
        # Open output button (disabled until completion)
        self.open_button = QPushButton(String.get("STATUS_OPEN_OUTPUT", "Open output"), self)
        self.open_button.setEnabled(False)
        self.open_button.clicked.connect(self._on_open_output)
        buttons.addWidget(self.open_button)
        layout.addLayout(buttons)

        # Log output
        self.log = QPlainTextEdit(self)
        self.log.setReadOnly(True)
        layout.addWidget(self.log)

        # Initialize from state
        self._sync_from_state()

    def _sync_from_state(self) -> None:
        out = state.controls.get("processing.output_path")
        if out:
            self.output_path.setText(str(out))
        self.strict_chk.setChecked(bool(state.controls.get("processing.strict")))
        # Show last metrics if present
        last_elapsed = state.controls.get("processing.last_elapsed")
        last_throughput = state.controls.get("processing.last_throughput")
        if last_elapsed is not None:
            self.elapsed_label.setText(f"Elapsed: {last_elapsed:.2f}s")
        if last_throughput is not None:
            self.throughput_label.setText(f"Throughput: {last_throughput:.2f} rows/s")

    def _on_browse(self) -> None:
        file, _ = QFileDialog.getSaveFileName(self, String.get("STATUS_SELECT_OUTPUT", "Select Output File"))
        if file:
            self.output_path.setText(file)

    def _on_output_changed(self, text: str) -> None:
        if text:
            state.update_control("processing.output_path", text)
        else:
            # Clear override
            all_ctrl = dict(state.controls)
            all_ctrl.pop("processing.output_path", None)
            state.controls = all_ctrl

    def _on_strict_changed(self, _state: int) -> None:
        state.update_control("processing.strict", self.strict_chk.isChecked())

    def _on_status_update(self, sender: Any, msg: str, **kwargs: Any) -> None:
        self.log.appendPlainText(str(msg))

    def _on_progress_update(self, sender: Any, value: int, **kwargs: Any) -> None:
        v = max(0, min(100, int(value)))
        self.progress.setValue(v)
        self.progress_label.setText(f"{v}%")

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
        # Suggest a default output path if empty
        if not self.output_path.text() and source:
            base = source.split("::")[0]
            from pathlib import Path

            p = Path(base)
            self.output_path.setPlaceholderText(str(p.with_name(f"{p.stem}_processed{p.suffix}")))

    def _on_start(self) -> None:
        self._set_running(True)
        self.log.appendPlainText(String.get("STATUS_PROCESSING_STARTED", "Processing started"))
        # clear previous output button state
        self.open_button.setEnabled(False)
        self._output_file = None
        EMIT("processing.start")

    def _on_cancel(self) -> None:
        self.cancel_button.setEnabled(False)
        EMIT("processing.cancel")

    def _on_complete(self, sender: Any, **kwargs: Any) -> None:
        # kwargs may include path, elapsed, throughput
        path = kwargs.get("path")
        elapsed = kwargs.get("elapsed")
        throughput = kwargs.get("throughput")
        if elapsed is not None:
            try:
                self.elapsed_label.setText(f"Elapsed: {float(elapsed):.2f}s")
            except Exception:
                pass
        if throughput is not None:
            try:
                self.throughput_label.setText(f"Throughput: {float(throughput):.2f} rows/s")
            except Exception:
                pass
        if path:
            self._output_file = path
            self.open_button.setEnabled(True)
        self.progress.setValue(100)
        self.progress_label.setText("100%")
        self.log.appendPlainText(String.get("STATUS_PROCESSING_COMPLETE", "Processing complete"))
        self._set_running(False)

    def _on_canceled(self, sender: Any, **kwargs: Any) -> None:
        self.log.appendPlainText(String.get("STATUS_PROCESSING_CANCELED", "Processing canceled"))
        self._set_running(False)

    def _on_error(self, sender: Any, msg: str = "", **kwargs: Any) -> None:
        if msg:
            self.log.appendPlainText(f"Error: {msg}")
        self._set_running(False)

    def _set_running(self, running: bool) -> None:
        self.start_button.setEnabled(not running)
        self.cancel_button.setEnabled(running)
        self.output_path.setEnabled(not running)
        self.strict_chk.setEnabled(not running)
        self.preview_button.setEnabled(not running)
        if not running:
            self.progress.setValue(0)
            self.progress_label.setText("0%")

    def _on_preview(self) -> None:
        current = state.controls.get("processing.current") or {}
        source_id: str = current.get("source") or ""
        mapping = current.get("mapping") or []
        skips = current.get("skip_rows") or []
        if not source_id or not mapping:
            self.log.appendPlainText("Nothing to preview: missing source or mapping")
            return
        path, sheet = (source_id.rsplit("::", 1) + [None])[:2] if "::" in source_id else (source_id, None)
        try:
            iface = FileInterfaceFactory.create(path)
            if hasattr(iface, "sheet_name") and sheet:
                iface.sheet_name = sheet
            # Apply skip rows
            try:
                iface.set_rows_to_skip(skips)
            except Exception:
                # fall back to header skip if contiguous
                srt = sorted(set(int(r) for r in skips if int(r) >= 0))
                if srt == list(range(len(srt))):
                    iface.set_header_rows_to_skip(len(srt))
            # Load a small chunk
            chunk = next(iface.iter_load(chunksize=500))
            out = apply_mapping(chunk, mapping)
            self.log.appendPlainText("Preview (first 5 rows):")
            self.log.appendPlainText(out.head(5).to_string(index=False))
        except StopIteration:
            self.log.appendPlainText("No data to preview.")
        except Exception as e:
            self.log.appendPlainText(f"Preview failed: {e}")

    def _on_open_output(self) -> None:
        if not self._output_file:
            # fallback to output path field
            path = self.output_path.text() or state.controls.get("processing.output_path")
        else:
            path = self._output_file
        if not path:
            self.log.appendPlainText("No output file to open.")
            return
        try:
            # On Windows, os.startfile is the simplest way
            if os.name == "nt":
                os.startfile(path)
            else:
                # Fallback: use xdg-open / open
                import subprocess

                opener = "xdg-open" if os.name == "posix" else "open"
                subprocess.Popen([opener, path])
        except Exception as e:
            self.log.appendPlainText(f"Failed to open output: {e}")

