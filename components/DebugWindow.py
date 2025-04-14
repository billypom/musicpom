from collections.abc import Iterable
from PyQt5.QtWidgets import (
    QDialog,
    QPlainTextEdit,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)
from pprint import pformat
from logging import debug


class DebugWindow(QDialog):
    def __init__(self, data):
        """
        Shows a dialog window
        data can be str, list or dict
        """
        super(DebugWindow, self).__init__()
        self.setWindowTitle("debug")
        self.setMinimumSize(400, 400)
        self.data = data
        layout = QVBoxLayout()

        # Labels & input fields
        # debug(pformat(self.text))
        if isinstance(self.data, str):
            self.input_field = QPlainTextEdit(pformat(self.data))
            layout.addWidget(self.input_field)
        elif isinstance(self.data, list):
            table = QTableWidget()
            table.setRowCount(len(data))
            table.setColumnCount(len(data[0]))
            for ri, row_data in enumerate(data):
                for ci, item in enumerate(row_data):
                    table.setItem(ri, ci, QTableWidgetItem(str(item)))
            layout.addWidget(table)
        elif isinstance(self.data, dict):
            # FIXME: i wanna grow....woah
            try:
                table = QTableWidget()
                rows = max(len(value) for value in data.keys())
                table.setRowCount(rows)
                table.setColumnCount(len(data))
                table.setHorizontalHeaderLabels(data.keys())
                for ci, (key, values) in enumerate(data.items()):
                    for ri, value in enumerate(values):
                        table.setItem(ri, ci, QTableWidgetItem(str(value)))
                layout.addWidget(table)
            except Exception as e:
                data = str(self.data)
                self.input_field = QPlainTextEdit(pformat(data + "\n\n" + str(e)))
                layout.addWidget(self.input_field)

        self.setLayout(layout)
