from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QPlainTextEdit,
    QVBoxLayout,
    QLabel,
    QPushButton,
)
from PyQt5.QtGui import QFont
from components.ErrorDialog import ErrorDialog
from utils import set_id3_tag
from logging import debug


class QuestionBoxDetails(QDialog):
    def __init__(self, title: str, description: str, details):
        super(QuestionBoxDetails, self).__init__()
        self.title: str = title
        self.description: str = description
        self.details: str = details
        self.reply: bool = False
        self.setWindowTitle(title)
        self.setMinimumSize(400, 400)
        layout = QVBoxLayout()
        h_layout = QHBoxLayout()

        # Labels & input fields
        label = QLabel(description)
        layout.addWidget(label)
        self.text_field = QPlainTextEdit(self.details)
        layout.addWidget(self.text_field)
        # ok
        ok_button = QPushButton("ok")
        ok_button.clicked.connect(self.ok)
        h_layout.addWidget(ok_button)
        # cancel
        cancel_button = QPushButton("cancel")
        cancel_button.clicked.connect(self.cancel)
        h_layout.addWidget(cancel_button)

        layout.addLayout(h_layout)
        self.setLayout(layout)

        ok_button.setFocus()

    def execute(self):
        self.exec_()
        return self.reply

    def cancel(self):
        self.reply = False
        self.close()

    def ok(self):
        self.reply = True
        self.close()
