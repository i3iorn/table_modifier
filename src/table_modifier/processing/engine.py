import threading
import time
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Set

import pandas as pd

from src.table_modifier.config.state import state
from src.table_modifier.file_interface.excel import ExcelFileInterface
from src.table_modifier.file_interface.factory import FileInterfaceFactory
from src.table_modifier.processing.transform import apply_mapping
from src.table_modifier.signals import ON, EMIT


_listener_installed = False
_listener_lock = threading.Lock()
_cancel_event = threading.Event()


def _parse_source_id(source_id: str) -> Tuple[str, Optional[str]]:
    """Split a composite source ID of the form 'path::sheet' into (path, sheet).

    If no sheet part is present, returns (path, None).
    Uses rsplit to avoid interfering with Windows drive letters.
    """
    if not source_id:
        return source_id, None
    if "::" in source_id:
        path, sheet = source_id.rsplit("::", 1)
        return path, sheet or None
    return source_id, None


def _build_output_path(input_path: str) -> Path:
    p = Path(input_path)
    return p.with_name(f"{p.stem}_processed{p.suffix}")


def _create_output_interface_like(input_iface) -> Any:
    """Create an output interface of the same type as input_iface for writing results."""
    if isinstance(input_iface, ExcelFileInterface):
        # Excel requires instantiation with a path; we'll swap to the final path at save time.
        return ExcelFileInterface(input_iface.path.as_posix(), sheet_name=input_iface.sheet_name)
    # CSV and others should be handled by their classes via factory
    return FileInterfaceFactory.create(input_iface.path.as_posix())


def _apply_skip_rows(iface, skip_rows: List[int]) -> None:
    """Apply fine-grained skip rows to the file interface if supported."""
    try:
        # Prefer list-based skip; implementations should handle gracefully
        iface.set_rows_to_skip(skip_rows)
    except Exception:
        # Fallback: if contiguous prefix 0..n-1, use header_rows_to_skip
        unique_sorted = sorted(set(int(r) for r in (skip_rows or []) if int(r) >= 0))
        contiguous = unique_sorted == list(range(len(unique_sorted)))
        if contiguous:
            iface.set_header_rows_to_skip(len(unique_sorted))


def request_cancel() -> None:
    _cancel_event.set()


def clear_cancel() -> None:
    _cancel_event.clear()


def _on_processing_cancel(sender: Any, **kwargs: Any) -> None:
    request_cancel()


def _estimate_total_rows(input_iface, chunksize: int = 100_000) -> int:
    total = 0
    try:
        for chunk in input_iface.iter_load(chunksize=chunksize):
            total += len(chunk)
    except Exception:
        return 0
    return total


def _collect_all_sources(mapping: List[Dict[str, Any]]) -> Set[str]:
    s: Set[str] = set()
    for entry in mapping:
        for src in entry.get("sources", []) or []:
            if src:
                s.add(src)
    return s


def _compute_output_columns(mapping: List[Dict[str, Any]]) -> List[str]:
    cols: List[str] = []
    for i, entry in enumerate(mapping):
        sources = list(entry.get("sources", []))
        name = sources[0] if len(sources) == 1 and sources else f"Combined_{i+1}"
        cols.append(name)
    return cols


def _run_processing(current: Dict[str, Any]) -> None:
    clear_cancel()
    source_id: str = current.get("source")
    mapping: List[Dict[str, Any]] = current.get("mapping") or []
    skip_rows: List[int] = current.get("skip_rows") or []
    strict: bool = bool(state.controls.get("processing.strict"))
    strict_per_slot: bool = bool(state.controls.get("processing.strict_per_slot"))
    output_path_override: Optional[str] = state.controls.get("processing.output_path")

    # Read user-configured chunk size and delimiter
    try:
        configured_chunk = int(state.controls.get("processing.chunk_size") or 20000)
    except Exception:
        configured_chunk = 20000
    csv_delim = state.controls.get("processing.csv_delimiter") or ","

    if not source_id or not mapping:
        EMIT("status.update", msg="Nothing to process: missing source or mapping.")
        return

    path, sheet = _parse_source_id(source_id)
    try:
        input_iface = FileInterfaceFactory.create(path)
        # Apply configured delimiter if interface supports it
        if hasattr(input_iface, "_delimiter"):
            try:
                setattr(input_iface, "_delimiter", csv_delim)
            except Exception:
                pass
        # Set target sheet when available (robust across implementations)
        if sheet and hasattr(input_iface, "sheet_name"):
            try:
                setattr(input_iface, "sheet_name", sheet)
            except Exception:
                pass
        _apply_skip_rows(input_iface, skip_rows)
    except Exception as e:
        EMIT("status.update", msg=f"Failed to open source: {e}")
        EMIT("processing.error", msg=str(e))
        return

    # Validate sources vs headers early
    try:
        headers = input_iface.get_headers()
    except Exception as e:  # header probing can fail on odd files
        headers = None
        EMIT("status.update", msg=f"Could not read headers for validation: {e}")
    if headers is not None:
        all_sources = _collect_all_sources(mapping)
        missing_all = sorted(all_sources - set(headers))
        # Per-slot missing calculation
        missing_per_slot = []
        for idx, entry in enumerate(mapping):
            srcs = [s for s in (entry.get("sources") or []) if s]
            missing = sorted(set(srcs) - set(headers))
            if missing:
                missing_per_slot.append((idx, missing))

        if strict_per_slot and missing_per_slot:
            EMIT("status.update", msg=f"Strict per-slot mode: mapping slot(s) missing columns: {missing_per_slot}")
            EMIT("processing.error", msg="Missing required columns (per-slot strict)")
            return
        if strict and missing_all:
            EMIT("status.update", msg=f"Strict mode: missing columns: {missing_all}")
            EMIT("processing.error", msg="Missing required columns")
            return
        if missing_all:
            EMIT("status.update", msg=f"Warning: missing columns will be empty: {missing_all}")

    # Prepare output interface and processing
    out_path = Path(output_path_override) if output_path_override else _build_output_path(path)
    output_iface = _create_output_interface_like(input_iface)
    total_processed = 0
    total_rows = _estimate_total_rows(input_iface, chunksize=max(1000, configured_chunk * 5))

    EMIT("status.update", msg=f"Processing: {Path(path).name} -> {out_path.name}")

    any_data = False
    start_time = time.time()
    try:
        # Try chunked processing if available
        for chunk in input_iface.iter_load(chunksize=configured_chunk):
            if _cancel_event.is_set():
                EMIT("status.update", msg="Processing canceled by user.")
                break
            out_chunk = apply_mapping(chunk, mapping)
            # Validate columns quickly
            if out_chunk.columns.empty:
                continue
            any_data = True
            try:
                # Pass delimiter preference to CSV output if supported
                if hasattr(output_iface, "_delimiter"):
                    try:
                        setattr(output_iface, "_delimiter", csv_delim)
                    except Exception:
                        pass
                output_iface.append_df(out_chunk)
            except Exception:
                # Fallback: accumulate locally
                if getattr(output_iface, "_df", None) is None:
                    output_iface._df = out_chunk.copy()  # type: ignore[attr-defined]
                else:
                    output_iface._df = pd.concat([output_iface._df, out_chunk], ignore_index=True)  # type: ignore[attr-defined]
            total_processed += len(chunk)
            # Emit coarse progress using available total_rows
            if total_rows > 0:
                pct = int(min(99, max(1, (total_processed * 95) / max(1, total_rows)) + 5))
            else:
                pct = min(99, 5 + (total_processed // max(1, configured_chunk)))
            EMIT("progress.update", value=int(pct))

        # If canceled, still try to save partial output if any
        if not any_data:
            # Write empty file with headers derived from mapping
            empty = pd.DataFrame(columns=_compute_output_columns(mapping))
            try:
                output_iface.append_df(empty)
            except Exception:
                output_iface._df = empty  # type: ignore[attr-defined]

        # Save to output
        try:
            # Ensure parent dir exists
            out_path.parent.mkdir(parents=True, exist_ok=True)
            # For CSV outputs, many interfaces have save_as(file_path) signature
            output_iface.save_as(out_path.as_posix())
        except Exception as e:
            EMIT("status.update", msg=f"Failed to save output: {e}")
            EMIT("processing.error", msg=str(e))
            return

        elapsed = time.time() - start_time
        throughput = (total_processed / elapsed) if elapsed > 0 else 0
        # Persist metrics to state for UI or future runs
        try:
            state.update_control("processing.last_elapsed", elapsed)
            state.update_control("processing.last_throughput", throughput)
        except Exception:
            pass

        if _cancel_event.is_set():
            EMIT("progress.update", value=100)
            EMIT("processing.canceled", path=out_path.as_posix())
            return

        EMIT("progress.update", value=100)
        EMIT("status.update", msg=f"Done. Rows: {total_processed}. Wrote: {out_path}")
        EMIT("processing.complete", path=out_path.as_posix(), elapsed=elapsed, throughput=throughput)
    except Exception as e:
        EMIT("status.update", msg=f"Processing error: {e}")
        EMIT("processing.error", msg=str(e))


def _on_processing_start(sender: Any, **kwargs: Any) -> None:
    current = state.controls.get("processing.current") or {}
    # Run in background thread to avoid blocking UI
    t = threading.Thread(target=_run_processing, args=(current,), daemon=True)
    t.start()


def ensure_engine_listener() -> None:
    global _listener_installed
    with _listener_lock:
        if _listener_installed:
            return
        ON("processing.start", _on_processing_start)
        ON("processing.cancel", _on_processing_cancel)
        _listener_installed = True
