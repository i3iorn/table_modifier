import asyncio
import logging
import sys
from typing import Any, Optional, Type

from PyQt6.QtWidgets import QApplication, QMessageBox
from qasync import QEventLoop

from src.table_modifier.gui.main_window import MainWindow


logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)9s - %(name)30s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


def excepthook(
    exc_type: Type[BaseException],
    exc_value: BaseException,
    exc_traceback: Optional[Any],
) -> None:
    """
    Global exception handler for uncaught exceptions in the application.

    - Logs the full exception with traceback at CRITICAL level.
    - Shows a message box if a QApplication is active; otherwise, writes to stderr.
    """
    logging.critical("Unhandled exception", exc_info=(exc_type, exc_value, exc_traceback))
    error_message = f"An unexpected error occurred:\n{exc_value}"
    app = QApplication.instance()
    if app is not None:
        QMessageBox.critical(None, "Application Error", error_message)
    else:
        # Fallback for early exceptions before QApplication is created
        sys.stderr.write(error_message + "\n")


# Set the custom exception hook as early as possible
sys.excepthook = excepthook


def run() -> None:
    """
    Run the application event loop.

    Notes:
    - qasync integrates the asyncio loop with Qt; we drive the UI via loop.run_forever().
    - Creation of QApplication and the event loop happens here to avoid side effects on import.
    """
    app = QApplication(sys.argv)
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)

    with loop:
        main_window = MainWindow()
        main_window.show()
        loop.run_forever()


if __name__ == "__main__":
    run()
