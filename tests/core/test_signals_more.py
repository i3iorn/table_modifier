import pytest

from src.table_modifier.signals import EMIT, ON, OFF


def test_wildcard_handler_exception_is_caught_and_does_not_crash():
    called = {"ok": False}

    def bad_handler(sender, signal: str, **kwargs):
        raise RuntimeError("boom")

    def good_handler(sender, signal: str, **kwargs):
        called["ok"] = True

    unsub_bad = ON("x.y.*", bad_handler)
    unsub_good = ON("x.y.*", good_handler)
    try:
        EMIT("x.y.z")  # should not raise despite bad_handler
        assert called["ok"] is True
    finally:
        unsub_bad()
        unsub_good()


def test_off_nonexistent_signal_no_error():
    # OFF should be safe even if nothing connected
    def handler(sender, signal: str, **kwargs):
        pass
    # Try unsubscribing an never-subscribed handler on exact signal
    OFF("no.such.signal", handler)
    # And on wildcard
    OFF("no.such.*", handler)

