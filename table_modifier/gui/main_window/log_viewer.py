from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTextEdit


class LogViewerWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.log_text_edit = QTextEdit(self)
        self.log_text_edit.setReadOnly(True)

        self.layout.addWidget(self.log_text_edit)
        self.setLayout(self.layout)

    def append_log(self, message):
        """Append a log message to the text edit."""
        self.log_text_edit.append(message)
