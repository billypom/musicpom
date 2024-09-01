import logging
from PyQt5.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLineEdit,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QListWidget,
    QListWidgetItem,
)
from PyQt5.QtGui import QFont
from configparser import ConfigParser
import DBA


class ExportPlaylistWindow(QDialog):
    def __init__(self):
        super(ExportPlaylistWindow, self).__init__()
        self.setWindowTitle("Export playlist")
        config = ConfigParser()
        config.read("config.ini")
        self.export_path = config.get("directories", "playlist_export_path")
        layout = QVBoxLayout()
        # button_layout = QHBoxLayout()

        playlist_dict = {}
        with DBA.DBAccess() as db:
            data = db.query("SELECT id, name from playlist;", ())
        for row in data:
            playlist_dict[row[0]] = row[1]

        self.item_dict = {}
        self.listWidget = QListWidget(self)
        for i, (k, v) in enumerate(playlist_dict.items()):
            item_text = f"{i} | {v}"
            item = QListWidgetItem(item_text)
            self.listWidget.addItem(item)
            self.item_dict[item_text] = k

        # add ui elements to window
        label = QLabel("Playlists")
        label.setFont(QFont("Sans", weight=QFont.Bold))
        layout.addWidget(label)
        layout.addWidget(self.listWidget)

        # Export path label
        label = QLabel("Export path")
        label.setFont(QFont("Sans", weight=QFont.Bold))  # bold category
        label.setStyleSheet("text-transform:lowercase;")  # uppercase category

        # Export path
        self.input = QLineEdit(self.export_path)
        layout.addWidget(self.input)

        # Save button
        save_button = QPushButton("Export")
        save_button.clicked.connect(self.save)
        layout.addWidget(save_button)
        self.setLayout(layout)
        self.show()

    def save(self) -> None:
        """Exports the chosen database playlist to a .m3u file"""
        selected_items = [item.text() for item in self.listWidget.selectedItems()]
        selected_db_ids = [self.item_dict[item] for item in selected_items]
        value = self.input.text()
        if value == "" or value is None:
            self.close()
            return
        for playlist in selected_db_ids:
            print(type(playlist))
            print(playlist)
            try:
                with DBA.DBAccess() as db:
                    selected_song_paths = db.query(
                        "SELECT s.filepath FROM song_playlist as sp JOIN song as s ON s.id = sp.song_id WHERE sp.playlist_id = ?;",
                        (playlist,),
                    )
            except Exception as e:
                logging.error(
                    f"ExportPlaylistWindow.py save() | could not retrieve playlist songs: {e}"
                )
        # FIXME: make this write to a .m3u file, also
        # need to consider relative paths + config for that
        self.close()

    def cancel(self) -> None:
        self.close()
        return
