import inspect
import logging
import threading
import time
from collections import defaultdict
from typing import Callable, Dict, List, Optional, Any
from blinker import Signal


DEFAULT_DEBOUNCE_MS = 500


class EventBus:
    """Thread-safe hierarchical event bus with namespace-based signals."""

    def __init__(self) -> None:
        self._signals: Dict[str, Signal] = {}
        self._wildcard_map: Dict[str, List[Callable]] = defaultdict(list)
        self._lock = threading.RLock()
        self._last_emit_time: Dict[str, float] = {}
        self._logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    def _get_signal(self, name: str) -> Signal:
        with self._lock:
            if name not in self._signals:
                self._signals[name] = Signal(name)
            return self._signals[name]

    def emit(self, name: str, sender: Optional[Any] = None, debounce: bool = True, **kwargs) -> None:
        """
        Emit a namespaced signal, triggering all exact and wildcard matches.

        Args:
            name (str): Namespaced signal name, like "auth.user.login".
            sender (Any, optional): Sender object (defaults to inferred).
            **kwargs: Extra payload.
        """
        # Debounce logic: skip if called too soon
        current_time = time.thread_time()
        if debounce:
            last_time = self._last_emit_time.get(name, 0)
            if last_time and (current_time - last_time < DEFAULT_DEBOUNCE_MS / 1000):
                return

        self._last_emit_time[name] = current_time

        # Infer sender if not provided
        sender = sender or self._infer_sender()

        # To avoid holding lock while dispatching handlers (which could deadlock),
        # first collect handlers while holding lock, then call outside.

        with self._lock:
            exact_signal = self._signals.get(name)
            wildcard_handlers = []
            for pattern, handlers in self._wildcard_map.items():
                if self._match(name, pattern):
                    wildcard_handlers.extend(handlers)

        # Dispatch exact handlers
        if exact_signal:
            self._logger.debug(f"[EventBus] Emitting signal '{name}' with sender '{sender}' and kwargs: {kwargs}")
            exact_signal.send(sender, **kwargs)

        # Dispatch wildcard handlers
        for handler in wildcard_handlers:
            try:
                handler(sender, **kwargs)
            except Exception as e:
                self._logger.error(f"Error in wildcard handler for '{name}': {e}", exc_info=True)

    def on(self, name: str, handler: Callable) -> None:
        """
        Subscribe a handler to a signal name or wildcard.

        Args:
            name (str): Signal name (e.g., "x.y.z" or "x.y.*").
            handler (Callable): The handler to invoke.
        """
        with self._lock:
            if "*" in name:
                self._wildcard_map[name].append(handler)
            else:
                self._get_signal(name).connect(handler)

    def off(self, name: str, handler: Callable) -> None:
        """
        Unsubscribe a handler from a signal or wildcard.

        Args:
            name (str): Signal name or wildcard.
            handler (Callable): Handler to remove.
        """
        with self._lock:
            if "*" in name:
                if handler in self._wildcard_map.get(name, []):
                    self._wildcard_map[name].remove(handler)
            else:
                signal = self._signals.get(name)
                if signal:
                    signal.disconnect(handler)

    def _match(self, name: str, pattern: str) -> bool:
        """Simple pattern match for wildcards like 'x.y.*'."""
        if pattern.endswith(".*"):
            prefix = pattern[:-1]
            return name.startswith(prefix)
        return name == pattern

    def _infer_sender(self) -> str:
        """
        Infer the sender from the call stack.

        Returns:
            str: String identifier for the sender (e.g., 'module:Class.method').
        """
        frame = inspect.currentframe()
        if frame is None:
            return "unknown"

        caller_frame = frame.f_back.f_back  # Skip emit() and EMIT()
        if caller_frame is None:
            return "unknown"

        module = inspect.getmodule(caller_frame)
        mod_name = module.__name__ if module else "unknown_module"

        func_name = caller_frame.f_code.co_name
        self_obj = caller_frame.f_locals.get("self")

        if self_obj:
            cls_name = type(self_obj).__name__
            return f"{mod_name}:{cls_name}.{func_name}"
        return f"{mod_name}:{func_name}"


# Global instance and APIs
_event_bus = EventBus()

def EMIT(name: str, **kwargs) -> None:
    """Emit a signal globally with automatic sender detection."""
    _event_bus.emit(name, **kwargs)

def ON(name: str, handler: Callable) -> None:
    """Subscribe to a signal globally."""
    _event_bus.on(name, handler)

def OFF(name: str, handler: Callable) -> None:
    """Unsubscribe a handler globally."""
    _event_bus.off(name, handler)
