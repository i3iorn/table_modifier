import time
from typing import Any, List

from src.table_modifier.signals import EMIT, ON


def test_emit_with_delay_delivers_later():
    calls: List[Any] = []

    def handler(sender: Any, signal: str, **kwargs: Any) -> None:
        calls.append((signal, kwargs))

    unsub = ON("unit.delay.test", handler)
    try:
        # Schedule with small delay
        EMIT("unit.delay.test", delay_ms=120, payload=42)
        # Immediately: should not be delivered yet
        time.sleep(0.03)
        assert calls == []
        # After delay window + margin: should be delivered
        time.sleep(0.15)
        assert calls == [("unit.delay.test", {"payload": 42})]
    finally:
        unsub()

