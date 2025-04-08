from PyQt5.QtWidgets import (
    QDialog,
    QPlainTextEdit,
    QVBoxLayout,
)
from pprint import pformat
from logging import debug


class DebugWindow(QDialog):
    def __init__(self, text: str):
        super(DebugWindow, self).__init__()
        self.setWindowTitle("debug")
        self.setMinimumSize(400, 400)
        self.text: str = text
        layout = QVBoxLayout()

        # Labels & input fields
        # debug(pformat(self.text))
        self.input_field = QPlainTextEdit(pformat(self.text))
        layout.addWidget(self.input_field)

        self.setLayout(layout)
