from PyQt5.QtWidgets import (
    QDialog,
    QWidget,
    QListWidget,
    QFrame,
    QVBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
)
from PyQt5.QtGui import QFont


class AddToPlaylistWindow(QDialog):
    def __init__(self, list_options: dict):
        super(AddToPlaylistWindow, self).__init__()
        self.setWindowTitle("Choose")
        self.setMinimumSize(400, 400)
        layout = QVBoxLayout()
        listWidget = QListWidget(self)
        for k, v in list_options:
            listWidget.addItem(f"{k} | {v}")

        # add ui elements to window
        label = QLabel("Playlists")
        label.setFont(QFont("Sans", weight=QFont.Bold))
        layout.addWidget(label)
        layout.addWidget(listWidget)

        # Save button
        save_button = QPushButton("Add")
        save_button.clicked.connect(self.save)
        layout.addWidget(save_button)
        self.setLayout(layout)
        self.show()

    def save(self):
        print(self.listWidget.selectedItems())
        self.close()
