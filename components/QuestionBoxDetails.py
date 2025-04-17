from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import (
    QAbstractScrollArea,
    QDialog,
    QHBoxLayout,
    QHeaderView,
    QPlainTextEdit,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QLabel,
    QPushButton,
)
from PyQt5.QtGui import QFont
from components.ErrorDialog import ErrorDialog
from logging import debug, error
from pprint import pformat


class QuestionBoxDetails(QDialog):
    def __init__(self, title: str, description: str, data):
        super(QuestionBoxDetails, self).__init__()
        self.title: str = title
        self.description: str = description
        self.data: str = data
        self.reply: bool = False
        self.setWindowTitle(title)
        self.setMinimumSize(400, 400)
        self.setMaximumSize(600,1000)
        layout = QVBoxLayout()
        h_layout = QHBoxLayout()

        # Labels & input fields
        label = QLabel(description)
        layout.addWidget(label)

        if isinstance(self.data, str):
            self.input_field = QPlainTextEdit(pformat(self.data))
            layout.addWidget(self.input_field)
        else:
            table: QTableWidget = QTableWidget()
            table.setSizeAdjustPolicy(QAbstractScrollArea.SizeAdjustPolicy.AdjustToContents)
            table.horizontalHeader().setStretchLastSection(True)
            table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
            if isinstance(self.data, list):
                # big ol column
                table.setRowCount(len(data))
                table.setColumnCount(1)
                for i, item in enumerate(self.data):
                    table.setItem(i, 0, QTableWidgetItem(str(item)))
                layout.addWidget(table)
            elif isinstance(self.data, dict):
                try:
                    # | TIT2 | title goes here |
                    # | TDRC | 2025-05-05      |
                    table.setRowCount(len(data.keys()))
                    table.setColumnCount(2)
                    table.setHorizontalHeaderLabels(['Tag', 'Value'])
                    for i, (k, v) in enumerate(data.items()):
                        table.setItem(i, 0, QTableWidgetItem(str(k)))
                        table.setItem(i, 1, QTableWidgetItem(str(v)))
                    layout.addWidget(table)
                except Exception as e:
                    data = str(self.data)
                    self.input_field = QPlainTextEdit(pformat(data + "\n\n" + str(e)))
                    layout.addWidget(self.input_field)
                    error(f'Tried to load self.data as dict but could not. {e}')
        # ok
        ok_button = QPushButton("Confirm")
        ok_button.clicked.connect(self.ok)
        h_layout.addWidget(ok_button)
        # cancel
        cancel_button = QPushButton("no")
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
