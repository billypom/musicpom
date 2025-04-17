from collections.abc import Iterable
from PyQt5.QtWidgets import (
    QAbstractScrollArea,
    QDialog,
    QHeaderView,
    QPlainTextEdit,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)
from pprint import pformat
from logging import debug, error


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

        self.setLayout(layout)
