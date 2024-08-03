from PyQt5.QtWidgets import (
    QDialog,
    QWidget,
    QListWidget,
    QFrame,
    QVBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QListWidgetItem,
)
from PyQt5.QtGui import QFont
import DBA
import logging


class AddToPlaylistWindow(QDialog):
    def __init__(self, list_options: dict, song_db_ids: list):
        super(AddToPlaylistWindow, self).__init__()
        self.song_db_ids = song_db_ids
        self.setWindowTitle("Add songs to playlist:")
        self.setMinimumSize(400, 400)
        layout = QVBoxLayout()

        self.item_dict = {}
        self.listWidget = QListWidget(self)
        for i, (k, v) in enumerate(list_options.items()):
            item_text = f"{i} | {v}"
            item = QListWidgetItem(item_text)
            self.listWidget.addItem(item)
            self.item_dict[item_text] = k

        # add ui elements to window
        label = QLabel("Playlists")
        label.setFont(QFont("Sans", weight=QFont.Bold))
        layout.addWidget(label)
        layout.addWidget(self.listWidget)

        # Save button
        save_button = QPushButton("Add")
        save_button.clicked.connect(self.save)
        layout.addWidget(save_button)
        self.setLayout(layout)
        self.show()

    def save(self):
        selected_items = [item.text() for item in self.listWidget.selectedItems()]
        selected_db_ids = [self.item_dict[item] for item in selected_items]
        for song in self.song_db_ids:
            for playlist in selected_db_ids:
                try:
                    with DBA.DBAccess() as db:
                        db.execute(
                            "INSERT INTO song_playlist (playlist_id, song_id) VALUES (?, ?);",
                            (playlist, song),
                        )
                except Exception as e:
                    logging.error(
                        "AddToPlaylistWindow.py save() | could not insert song into playlist: {e}"
                    )

        self.close()
