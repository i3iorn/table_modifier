import inspect
import logging
import threading
from collections import defaultdict
from typing import Callable, Dict, List, Optional, Any
from blinker import Signal


DEFAULT_DEBOUNCE_MS = 500


class EventBus:
    """Thread-safe hierarchical event bus with namespace-based signals.

    Handlers receive the following call signature:
        handler(sender, signal: str, **kwargs) -> None
    """

    def __init__(self) -> None:
        self._signals: Dict[str, Signal] = {}
        self._wildcard_map: Dict[str, List[Callable]] = defaultdict(list)
        self._lock = threading.RLock()
        self._last_emit_time: Dict[str, float] = {}
        self._logger = logging.getLogger(self.__class__.__name__)

    def _get_signal(self, name: str) -> Signal:
        with self._lock:
            if name not in self._signals:
                self._signals[name] = Signal(name)
            return self._signals[name]

    def emit(self, name: str, sender: Optional[Any] = None, delay_ms: Optional[int] = None, **kwargs) -> None:
        """
        Emit a namespaced signal, triggering all exact and wildcard matches.

        Args:
            name (str): Namespaced signal name, like "auth.user.login".
            sender (Any, optional): Sender object (defaults to inferred).
            delay_ms (Optional[int]): If provided and > 0, schedule emit after this many milliseconds.
            **kwargs: Extra payload delivered to handlers.
        """
        # Infer sender if not provided, capture now to preserve caller context for delayed emits
        sender = sender or self._infer_sender()

        if delay_ms is not None and delay_ms > 0:
            self._logger.debug(
                f"[EventBus] Scheduling delayed emit for '{name}' in {delay_ms}ms with kwargs: {kwargs}"
            )

            def _delayed_dispatch():
                try:
                    self._dispatch(name, sender, kwargs)
                except Exception as e:
                    self._logger.error(f"Error during delayed emit for '{name}': {e}", exc_info=True)

            timer = threading.Timer(delay_ms / 1000.0, _delayed_dispatch)
            timer.daemon = True
            timer.start()
            return

        # Immediate dispatch
        self._dispatch(name, sender, kwargs)

    def _dispatch(self, name: str, sender: Optional[Any], kwargs: Dict[str, Any]) -> None:
        """Internal: perform the actual dispatch of an already-prepared event."""
        # To avoid holding lock while dispatching handlers (which could deadlock),
        # first collect handlers while holding lock, then call outside.
        with self._lock:
            exact_signal = self._signals.get(name)
            wildcard_handlers: List[Callable] = []
            for pattern, handlers in self._wildcard_map.items():
                if self._match(name, pattern):
                    wildcard_handlers.extend(handlers.copy())

        # Dispatch exact handlers
        if exact_signal:
            self._logger.debug(
                f"[EventBus] Emitting signal '{name}' with sender '{sender}' and kwargs: {kwargs}"
            )
            exact_signal.send(sender, signal=name, **kwargs)

        # Dispatch wildcard handlers
        for handler in wildcard_handlers:
            try:
                handler(sender, signal=name, **kwargs)
            except Exception as e:
                self._logger.error(
                    f"Error in wildcard handler for '{name}': {e}", exc_info=True
                )

        self._logger.debug(f"[EventBus] Handlers for '{name}' emitted successfully.")

    def on(self, name: str, handler: Callable) -> Callable[[], None]:
        """
        Subscribe a handler to a signal name or wildcard and return an unsubscribe.

        Args:
            name (str): Signal name (e.g., "x.y.z" or "x.y.*").
            handler (Callable): The handler to invoke.

        Returns:
            Callable[[], None]: A function that unsubscribes this handler when called.
        """
        with self._lock:
            if name.endswith("*"):
                self._wildcard_map[name].append(handler)
            elif "*" in name:
                raise ValueError(
                    "Wildcards must end with '*' (e.g., 'x.y.*'). Use 'x.y.*' for wildcard subscriptions."
                )
            else:
                self._get_signal(name).connect(handler)

        def _unsubscribe() -> None:
            self.off(name, handler)

        return _unsubscribe

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

        # Walk back until we find the first frame that's not within this module
        # and not the helper functions 'emit' or global 'EMIT'.
        skip_funcs = {"emit", "EMIT"}
        f = frame.f_back
        while f:
            func_name = f.f_code.co_name
            module = inspect.getmodule(f)
            mod_name = module.__name__ if module else None
            if mod_name != __name__ and func_name not in skip_funcs:
                break
            f = f.f_back

        caller_frame = f
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


def EMIT(name: str, delay_ms: Optional[int] = None, **kwargs) -> None:
    """
    Emit a signal globally.

    This function allows you to emit a signal with a specific name and optional keyword
    arguments. It uses the global event bus instance to handle the emission.

    Args:
        name (str): The name of the signal to emit.
        delay_ms (Optional[int]): If provided and > 0, schedule emit after this many milliseconds.
        **kwargs (**Any): Additional keyword arguments to pass with the signal.

    Returns:
        None
    """
    _event_bus.emit(name, delay_ms=delay_ms, **kwargs)


def ON(name: str, handler: Callable) -> Callable[[], None]:
    """
    Subscribe a handler globally to a signal and return an unsubscribe function.

    This function allows you to register a handler for a specific signal name. The handler
    will be called whenever the signal is emitted.

    Args:
        name (str): The name of the signal to subscribe to (supports 'x.y.*').
        handler (Callable): The handler function to call when the signal is emitted.

    Returns:
        Callable[[], None]: Call to unsubscribe the handler.
    """
    return _event_bus.on(name, handler)


def OFF(name: str, handler: Callable) -> None:
    """
    Unsubscribe a handler globally from a signal.

    This function allows you to remove a previously registered handler for a specific
    signal name. The handler will no longer be called when the signal is emitted.

    Args:
        name (str): The name of the signal to unsubscribe from.
        handler (Callable): The handler function to remove.

    Returns:
        None
    """
    _event_bus.off(name, handler)
