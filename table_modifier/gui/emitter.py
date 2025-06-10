from PyQt6.QtCore import QObject, pyqtSignal

from table_modifier.file_interface.protocol import FileInterfaceProtocol
from table_modifier.file_status import FileStatus


class SignalEmitter(QObject):
    """
    Emitter of application-wide signals.  Just a plain QObject subclass.
    """
    # Signals for job management
    jobStarted            = pyqtSignal(str)
    jobFinished           = pyqtSignal(str)
    jobResult             = pyqtSignal(str, str)
    jobProgress           = pyqtSignal(str, int)
    jobError              = pyqtSignal(str, tuple)

    # Application signals
    appInitialized        = pyqtSignal()
    appShutdown           = pyqtSignal()
    appError              = pyqtSignal(str, tuple)

    # Application control signals
    stateReset            = pyqtSignal()
    controlUpdated        = pyqtSignal(str, str)
    folderUpdated         = pyqtSignal(str)


# the one and only global instance:
signal_emitter = SignalEmitter()
