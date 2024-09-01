import logging
from PyQt5.QtWidgets import QDialog, QHBoxLayout, QLineEdit, QPushButton, QVBoxLayout
from PyQt5.QtCore import pyqtSignal
import DBA


class CreatePlaylistWindow(QDialog):
    def __init__(self, playlistCreatedSignal):
        super(CreatePlaylistWindow, self).__init__()
        self.playlistCreatedSignal = playlistCreatedSignal
        self.setWindowTitle("Create new playlist")
        layout = QVBoxLayout()
        button_layout = QHBoxLayout()

        self.input = QLineEdit()
        layout.addWidget(self.input)

        ok_button = QPushButton("OK")
        ok_button.clicked.connect(self.save)
        button_layout.addWidget(ok_button)

        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.cancel)
        button_layout.addWidget(cancel_button)

        layout.addLayout(button_layout)
        self.setLayout(layout)

    def save(self) -> None:
        """Creates a playlist in the database with a specific name"""
        value = self.input.text()
        if value == "" or value is None:
            self.close()
            return
        else:
            try:
                with DBA.DBAccess() as db:
                    db.execute("INSERT INTO playlist (name) VALUES (?);", (value,))
            except Exception as e:
                logging.error(
                    f"CreatePlaylistWindow.py save() | Could not create playlist: {e}"
                )
            self.playlistCreatedSignal.emit()
            self.close()

    def cancel(self) -> None:
        self.close()
        return
