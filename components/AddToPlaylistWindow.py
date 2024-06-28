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
        #
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
        # Upcate the config fields
        for key in self.input_fields:
            for category in self.config.sections():
                if key in self.config[category]:
                    self.config[category][key] = self.input_fields[key].text()

        # Write the config file
        with open("config.ini", "w") as configfile:
            self.config.write(configfile)

        self.close()
