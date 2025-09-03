import logging
from typing import List, Optional, Dict, Any, Union

from PyQt6.QtCore import Qt, QModelIndex, QObject
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QListView,
    QLineEdit,
    QHBoxLayout,
    QDialog,
    QPushButton,
    QScrollArea, QLayout,
)

from src.table_modifier.classifier import ColumnTypeClassifier, DetectorRegistry
from src.table_modifier.config.state import state
from src.table_modifier.constants import NO_MARGIN
from src.table_modifier.file_interface.base import BaseInterface
from src.table_modifier.file_interface.excel import ExcelFileInterface
from src.table_modifier.file_interface.factory import FileInterfaceFactory
from src.table_modifier.gui.main_window.map_screen.draggable_label import DraggableLabel
from src.table_modifier.gui.main_window.map_screen.drop_slot import DropSlot
from src.table_modifier.localization import String
from src.table_modifier.signals import ON, EMIT
from src.table_modifier.gui.main_window.map_screen.utils import is_valid_skip_rows, parse_skip_rows


class MapScreen(QWidget):
    def __init__(self, parent: QObject = None) -> None:
        super().__init__(parent)
        self.logger = logging.getLogger(self.__class__.__name__)
        self.skip_rows_input: Optional[QLineEdit] = None
        self.drop_slots: List[DropSlot] = []
        self.left_labels: List[DraggableLabel] = []
        self.filter_input: Optional[QLineEdit] = None
        self.current_source_id: Optional[str] = None
        self._unsubs: List[callable] = []

        # Canvas and drag-drop container
        self.map_widget = QScrollArea(self)
        self.map_widget.setWidgetResizable(True)
        self.drag_drop_container = QWidget()
        self.drag_drop_container.setStyleSheet("border: none;")
        self.drag_drop_layout = QHBoxLayout(self.drag_drop_container)
        self.drag_drop_layout.setContentsMargins(*NO_MARGIN)
        self.map_widget.setWidget(self.drag_drop_container)

        # Main UI setup
        self._init_layout()
        self._init_controls()
        self.layout().addWidget(self.map_widget)
        # Footer buttons at the bottom of the tab
        self._init_footer()

    def _init_layout(self) -> None:
        main_layout = QVBoxLayout(self)
        self.setLayout(main_layout)

        # Title
        title = QLabel(String["MAP_SCREEN_TITLE"], self)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setObjectName("screenTitle")
        main_layout.addWidget(title)

    def _init_controls(self) -> None:
        layout = self.layout()
        # Skip rows input
        self.skip_rows_input = QLineEdit(self)
        self.skip_rows_input.setPlaceholderText("Skip rows (e.g., 0,1,2)")
        self.skip_rows_input.setClearButtonEnabled(True)
        self.skip_rows_input.textChanged.connect(self._on_skip_rows_changed)
        layout.addWidget(self.skip_rows_input)

        # Selected files view
        view = QListView(self)
        view.setModel(state.container.selected_files_model)
        view.setMaximumHeight(8 * 10)
        view.clicked.connect(self._on_item_clicked)
        layout.addWidget(view)

    def _init_footer(self) -> None:
        footer = QHBoxLayout()
        footer.addStretch(1)
        # Clear all button moved to footer
        clear_btn = QPushButton(String["MAP_CLEAR_ALL"], self)
        clear_btn.clicked.connect(self._clear_all_slots)
        footer.addWidget(clear_btn)
        # Single Process button replaces Next/Done/Complete
        process_btn = QPushButton(String.get("MAP_PROCESS", "Process"), self)
        process_btn.clicked.connect(self._on_ready_to_process)
        footer.addWidget(process_btn)
        self.layout().addLayout(footer)

    def _drop_slots_available(self) -> bool:
        """Check if there are any available drop slots."""
        return any(slot.is_empty() for slot in self.drop_slots)

    def _on_item_clicked(self, index: QModelIndex) -> None:
        if not index.isValid():
            return
        path = state.container.selected_files_model.data(
            index, role=Qt.ItemDataRole.UserRole
        )
        file_interface = FileInterfaceFactory.create(path)
        if isinstance(file_interface, ExcelFileInterface):
            self._show_sheet_dialog(file_interface)
        else:
            self._show_mapping(file_interface)

    def _show_sheet_dialog(self, file_interface: ExcelFileInterface) -> None:
        sheets = file_interface.get_sheets()
        if not sheets:
            self.logger.warning("No sheets found in Excel file.")
            return

        self.sheet_dialog = QDialog(self)
        layout = QVBoxLayout(self.sheet_dialog)
        self.sheet_dialog.setLayout(layout)
        layout.addWidget(QLabel(String["DIALOG_SELECT_SHEET"]))

        for sheet in sheets:
            btn = QPushButton(sheet, self.sheet_dialog)
            btn.clicked.connect(lambda _, s=sheet: self._handle_sheet_selected(s))
            layout.addWidget(btn)

        self.sheet_dialog.exec()

    def _handle_sheet_selected(self, sheet_name: str) -> None:
        first_index = state.container.selected_files_model.index(0)
        path = state.container.selected_files_model.data(
            first_index, role=Qt.ItemDataRole.UserRole
        )
        file_interface = FileInterfaceFactory.create(path)
        file_interface.sheet_name = sheet_name
        self._show_mapping(file_interface)
        self.sheet_dialog.close()

    def _source_id_for(self, file_interface: BaseInterface) -> str:
        sid = getattr(file_interface, "path", None) or str(file_interface)
        sheet = getattr(file_interface, "sheet_name", None)
        return f"{sid}::{sheet}" if sheet else f"{sid}"

    def _show_mapping(self, file_interface: BaseInterface) -> None:
        self.logger.info(f"Mapping {file_interface}")
        headers = file_interface.get_headers()
        if not headers:
            self.logger.warning("No headers found.")
            return

        self.current_source_id = self._source_id_for(file_interface)

        self._classify_columns(file_interface)
        self._clear_drag_drop()
        self._build_drag_drop(headers)

        # Wire events
        self._unsubs.append(ON("header.map.drop", self._on_header_drop))
        self._unsubs.append(ON("header.map.double_click", self._on_header_double_click))
        self._unsubs.append(ON("drop_slot.reorder", self._on_drop_slot_reorder))

        # Restore previously saved mapping and skip rows if available
        saved_struct = state.controls.get("map.mapping.by_source", {}).get(self.current_source_id)
        saved_legacy = state.controls.get("map.order.by_source", {}).get(self.current_source_id)
        saved = saved_struct if saved_struct is not None else saved_legacy
        if saved is not None:
            self._apply_saved_order(saved)
        saved_skip = state.controls.get("map.skip_rows.by_source", {}).get(self.current_source_id)
        if saved_skip is not None:
            self.skip_rows_input.setText(saved_skip)

        # Emit initial mapping-changed for visual sync
        self._emit_mapping_changed()

    def _classify_columns(self, file_interface: BaseInterface) -> None:
        classifier = ColumnTypeClassifier(DetectorRegistry)
        for col in file_interface.iter_columns(100):
            col_name = col.columns[0]
            result = classifier.classify(col[col_name].tolist(), col_name)
            self.logger.debug(f"Classified column '{col_name:<60s}': {str(result.candidates)} -- Example: {result.example_values}")

    def _clear_drag_drop(self) -> None:
        # Unsubscribe previous handlers
        for unsub in self._unsubs:
            try:
                unsub()
            except Exception:
                pass
        self._unsubs.clear()
        # Clear existing widgets and layouts
        for i in reversed(range(self.drag_drop_layout.count())):
            item = self.drag_drop_layout.itemAt(i)
            widget = item.widget()
            if widget:
                widget.deleteLater()
            else:
                layout = item.layout()
                if layout:
                    while layout.count():
                        child = layout.takeAt(0)
                        if child.widget():
                            child.widget().deleteLater()
        self.drop_slots.clear()
        self.left_labels.clear()
        self.filter_input = None

    def _build_drag_drop(self, headers: List[str]) -> None:
        # --- LEFT COLUMN ---
        left_container = QWidget()
        left_layout = QVBoxLayout(left_container)
        left_layout.addWidget(QLabel(String["MAP_AVAILABLE_HEADERS"]))

        # filter input
        self.filter_input = QLineEdit()
        self.filter_input.setPlaceholderText(String["MAP_FILTER_PLACEHOLDER"])
        self.filter_input.textChanged.connect(self._filter_headers)
        left_layout.addWidget(self.filter_input)

        for header in headers:
            label = DraggableLabel(header)
            # Keep QSS objectName set by DraggableLabel; attach header via property instead
            label.setProperty("header_label", header)
            self.left_labels.append(label)
            left_layout.addWidget(label)

        left_layout.addStretch()

        left_scroll = QScrollArea()
        left_scroll.setWidgetResizable(True)
        left_scroll.setWidget(left_container)

        # --- RIGHT COLUMN ---
        right_container = QWidget()
        self.right_layout = QVBoxLayout(right_container)
        self.drop_layout = QVBoxLayout()
        self.right_layout.addLayout(self.drop_layout)

        # Initial drop slot and stretch
        self._add_drop_slot(self.drop_layout)
        self.drop_layout.addStretch()

        # Add "Add Fixed Value" button at the bottom
        add_fixed_btn = QPushButton("Add Fixed Value", right_container)
        add_fixed_btn.clicked.connect(self._on_add_fixed_value)
        self.right_layout.addWidget(add_fixed_btn)

        right_scroll = QScrollArea()
        right_scroll.setWidgetResizable(True)
        right_scroll.setWidget(right_container)

        # Add scrollable containers to the main layout
        self.drag_drop_layout.addWidget(left_scroll)
        self.drag_drop_layout.addWidget(right_scroll)

    def _on_add_fixed_value(self) -> None:
        slot = self._add_drop_slot(self.drop_layout)
        slot.set_text("<Fixed Value>")

    def _filter_headers(self, text: str) -> None:
        needle = (text or "").strip().lower()
        for lbl in self.left_labels:
            lbl.setVisible(needle in lbl.text().lower())

    def _add_drop_slot(self, layout: QLayout) -> DropSlot:
        slot = DropSlot(index=len(self.drop_slots))
        self.drop_slots.append(slot)
        layout.addWidget(slot)
        return slot

    def _on_header_double_click(self, sender, text: str, **kwargs) -> None:
        # Fill first empty slot, or create one if none
        target = next((s for s in self.drop_slots if s.is_empty()), None)
        if target is None:
            # remove trailing stretch, add a slot, then re-add stretch
            self.drop_layout.takeAt(self.drop_layout.count() - 1)
            target = self._add_drop_slot(self.drop_layout)
            self.drop_layout.addStretch()
        target.set_text(text)
        # Drop event handler will run and call _emit_mapping_changed

    def _on_header_drop(self, sender, text: str, index: Optional[int] = None, **kwargs) -> None:
        # Allow headers to be used in multiple destinations; only dedupe within slot handled by DropSlot
        # If there are no empty slots, add one
        if not self._drop_slots_available():
            self.drop_layout.takeAt(self.drop_layout.count() - 1)
            self._add_drop_slot(self.drop_layout)
            self.drop_layout.addStretch()
        # Persist and notify
        self._persist_mapping()
        self._emit_mapping_changed()

    def _find_label_by_text(self, text: str) -> Optional[DraggableLabel]:
        return next(
            (w for w in self.drag_drop_container.findChildren(DraggableLabel) if
             w.text() == text),
            None,
        )

    # New structured mapping helpers
    def _current_mapping(self) -> List[Dict[str, Any]]:
        mapping: List[Dict[str, Any]] = []
        for slot in self.drop_slots:
            if not slot.is_empty():
                mapping.append({
                    "sources": slot.get_sources(),
                    "separator": slot.get_separator(),
                })
        return mapping

    def _flatten_used_sources(self) -> List[str]:
        seen = set()
        flat: List[str] = []
        for entry in self._current_mapping():
            for s in entry.get("sources", []):
                if s not in seen:
                    seen.add(s)
                    flat.append(s)
        return flat

    def get_new_order(self) -> List[str]:
        # Backwards-compatible API: return flattened list of used sources
        return self._flatten_used_sources()

    def _emit_mapping_changed(self) -> None:
        EMIT("header.map.changed", order=self._flatten_used_sources(), source=self.current_source_id)

    def _persist_mapping(self) -> None:
        if not self.current_source_id:
            return
        # Save structured mapping
        all_struct = state.controls.get("map.mapping.by_source", {})
        all_struct = dict(all_struct)
        all_struct[self.current_source_id] = self._current_mapping()
        state.update_control("map.mapping.by_source", all_struct)
        # Maintain legacy flattened string for old consumers
        all_legacy = state.controls.get("map.order.by_source", {})
        all_legacy = dict(all_legacy)
        all_legacy[self.current_source_id] = ",".join(self._flatten_used_sources())
        state.update_control("map.order.by_source", all_legacy)

    def _apply_saved_order(self, saved: Union[str, List[str]] = None) -> None:
        try:
            # New format: list of dicts
            if isinstance(saved, list):
                # Make sure we have enough slots
                needed = max(1, len(saved))
                while len(self.drop_slots) < needed:
                    self.right_layout.takeAt(self.right_layout.count() - 1)
                    self._add_drop_slot(self.right_layout)
                    self.right_layout.addStretch()
                for i, entry in enumerate(saved):
                    sources = list(entry.get("sources", [])) if isinstance(entry, dict) else []
                    sep = entry.get("separator") if isinstance(entry, dict) else None
                    if i < len(self.drop_slots):
                        self.drop_slots[i].set_from(sources, sep)
                return
            # Legacy format: comma-separated string of single-source slots
            if isinstance(saved, str):
                items = [s.strip() for s in saved.split(",") if s.strip()]
                needed = max(1, len(items))
                while len(self.drop_slots) < needed:
                    self.right_layout.takeAt(self.right_layout.count() - 1)
                    self._add_drop_slot(self.right_layout)
                    self.right_layout.addStretch()
                for i, text in enumerate(items):
                    if i < len(self.drop_slots):
                        self.drop_slots[i].set_from([text], " ")
        except Exception:
            return

    def _clear_all_slots(self) -> None:
        """Remove all drop slots in the right column."""
        while self.drop_slots:
            self.drop_slots.pop().deleteLater()
        self._add_drop_slot(self.drop_layout)
        self.drop_layout.addStretch()
        self._persist_mapping()
        self._emit_mapping_changed()

    def _on_skip_rows_changed(self, text: str) -> None:
        # visual validation
        ok = is_valid_skip_rows(text)
        self.skip_rows_input.setStyleSheet(
            "" if ok or not text else "border: 2px solid #e57373; border-radius: 4px;"
        )
        # persist raw text for source
        if self.current_source_id is None:
            return
        all_skips = state.controls.get("map.skip_rows.by_source", {})
        all_skips = dict(all_skips)
        all_skips[self.current_source_id] = text
        state.update_control("map.skip_rows.by_source", all_skips)

    def _on_ready_to_process(self) -> None:
        """Validate mapping and skip rows, persist current processing context, and navigate to Status tab."""
        mapping = self._current_mapping()
        raw_skips = self.skip_rows_input.text().strip() if self.skip_rows_input else ""
        if raw_skips and not is_valid_skip_rows(raw_skips):
            EMIT("status.update", msg="Invalid skip rows expression.")
            return
        try:
            skip_rows = parse_skip_rows(raw_skips)
        except Exception as e:
            EMIT("status.update", msg=f"Invalid skip rows: {e}")
            return
        if not mapping:
            EMIT("status.update", msg="No headers mapped; please add at least one.")
            return
        # Persist a structured processing context in state and notify
        state.update_control(
            "processing.current",
            {
                "source": self.current_source_id,
                "mapping": mapping,
                # Keep legacy field for simple UIs
                "order": self._flatten_used_sources(),
                "skip_rows": skip_rows,
            },
        )
        EMIT("processing.current.updated")

    def _on_drop_slot_reorder(self, sender, source: int, target: int, **kwargs) -> None:
        if source == target or source < 0 or target < 0 or source >= len(self.drop_slots) or target >= len(self.drop_slots):
            return
        slot = self.drop_slots.pop(source)
        self.drop_slots.insert(target, slot)
        # Remove all widgets from drop_layout
        for i in reversed(range(self.drop_layout.count())):
            item = self.drop_layout.itemAt(i)
            widget = item.widget()
            if widget:
                self.drop_layout.removeWidget(widget)
                widget.setParent(None)
        # Re-add slots in new order
        for idx, slot in enumerate(self.drop_slots):
            slot.index = idx
            self.drop_layout.addWidget(slot)
        self.drop_layout.addStretch()
        self._persist_mapping()
        self._emit_mapping_changed()
