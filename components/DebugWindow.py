from PyQt5.QtWidgets import (
    QDialog,
    QPlainTextEdit,
    QVBoxLayout,
)
from pprint import pformat


class DebugWindow(QDialog):
    def __init__(self, song_filepath: str, text: str):
        super(DebugWindow, self).__init__()
        self.setWindowTitle("debug")
        self.setMinimumSize(400, 400)
        self.text: str = text
        self.song_filepath: str = song_filepath
        layout = QVBoxLayout()

        # Labels & input fields
        self.input_field = QPlainTextEdit(pformat(self.text))
        layout.addWidget(self.input_field)

        self.setLayout(layout)
