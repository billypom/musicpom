from PyQt5.QtWidgets import (
    QDialog,
    QPlainTextEdit,
    QVBoxLayout,
    QLabel,
    QPushButton,
)
from PyQt5.QtGui import QFont
from components.ErrorDialog import ErrorDialog
from utils import set_id3_tag


class DebugWindow(QDialog):
    def __init__(self, song_filepath: str, text: str):
        super(DebugWindow, self).__init__()
        self.setWindowTitle("debug")
        self.setMinimumSize(400, 400)
        self.text: str = text
        self.song_filepath: str = song_filepath
        layout = QVBoxLayout()

        # Labels & input fields
        self.input_field = QPlainTextEdit(self.text)
        layout.addWidget(self.input_field)

        self.setLayout(layout)
