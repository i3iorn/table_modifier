import asyncio
import builtins
import sys

import pytest

import src  # this imports src.__init__ which binds excepthook/run/QApplication/etc.


def test_excepthook_no_app_writes_stderr(capsys):
    # Ensure no QApplication instance
    # Monkeypatch QApplication.instance to return None
    orig_instance = src.QApplication.instance
    try:
        src.QApplication.instance = classmethod(lambda cls: None)  # type: ignore[method-assign]
        # Trigger excepthook
        src.excepthook(RuntimeError, RuntimeError("boom"), None)
        out = capsys.readouterr()
        assert "An unexpected error occurred" in out.err
        assert "boom" in out.err
    finally:
        src.QApplication.instance = orig_instance  # type: ignore[assignment]


def test_excepthook_with_app_shows_messagebox(monkeypatch):
    called = {}

    class DummyApp:
        pass

    def fake_instance():
        return DummyApp()

    def fake_critical(parent, title, message):
        called["msg"] = message
        return None

    monkeypatch.setattr(src.QApplication, "instance", classmethod(lambda cls: fake_instance()))
    monkeypatch.setattr(src.QMessageBox, "critical", fake_critical)

    src.excepthook(RuntimeError, RuntimeError("oops"), None)
    assert "oops" in called.get("msg", "")


def test_run_monkeypatched_event_loop(monkeypatch):
    # Prepare dummies
    created = {"window": False, "loop": False}

    class DummyApp:
        def __init__(self, *args, **kwargs):
            pass

    class DummyLoop:
        def __init__(self, app):
            self.app = app

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def run_forever(self):
            created["loop"] = True

    class DummyWindow:
        def __init__(self, *args, **kwargs):
            created["window"] = True

        def show(self):
            pass

    # Patch symbols used inside run()
    monkeypatch.setattr(src, "QApplication", DummyApp)
    monkeypatch.setattr(src, "QEventLoop", DummyLoop)
    monkeypatch.setattr(src, "MainWindow", DummyWindow)
    monkeypatch.setattr(asyncio, "set_event_loop", lambda loop: None)

    # Execute
    src.run()
    assert created["window"] is True
    assert created["loop"] is True
