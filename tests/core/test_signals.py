import pytest

from typing import Any, List

from src.table_modifier.signals import EMIT, ON, OFF


def test_signal_emit_and_on_basic():
    received: List[Any] = []

    def handler(sender: Any, signal: str, **kwargs: Any) -> None:
        received.append((signal, kwargs))

    unsub = ON("unit.test.event", handler)
    try:
        EMIT("unit.test.event", payload=123)
        assert received == [("unit.test.event", {"payload": 123})]
    finally:
        unsub()


def test_signal_wildcard_and_unsubscribe():
    received: List[str] = []

    def handler(sender: Any, signal: str, **kwargs: Any) -> None:
        received.append(signal)

    unsub1 = ON("unit.*", handler)
    unsub2 = ON("unit.more.*", handler)
    try:
        EMIT("unit.abc")
        EMIT("unit.more.xyz")
        assert "unit.abc" in received
        assert "unit.more.xyz" in received
        # Unsubscribe and ensure no further delivery
        unsub1()
        unsub2()
        received.clear()
        EMIT("unit.abc")
        assert received == []
    finally:
        try:
            unsub1()
            unsub2()
        except Exception:
            pass

