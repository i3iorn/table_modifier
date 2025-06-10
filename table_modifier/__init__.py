import asyncio
import logging
import sys
from PyQt6.QtWidgets import QApplication, QMessageBox
from qasync import QEventLoop

from table_modifier.gui.main_window import MainWindow


logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)9s - %(name)30s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

def excepthook(exc_type, exc_value, exc_traceback):
    """
    Global exception handler for uncaught exceptions in the application.
    Displays an error message and logs the exception.
    """
    logging.critical("Unhandled exception", exc_info=(exc_type, exc_value, exc_traceback))
    error_message = f"An unexpected error occurred:\n{exc_value}"
    QMessageBox.critical(None, "Application Error", error_message)

# Set the custom exception hook
sys.excepthook = excepthook

app = QApplication(sys.argv)
loop = QEventLoop(app)
asyncio.set_event_loop(loop)

def run():
    """
    Run the application event loop.
    """
    with loop:
        main_window = MainWindow()

        main_window.show()
        loop.run_forever()
        app.exec()


if __name__ == "__main__":
    run()
