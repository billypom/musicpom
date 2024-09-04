import logging
from PyQt5.QtWidgets import (
    QCheckBox,
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
from utils import get_id3_tags, get_reorganize_vars
from components import ErrorDialog
import DBA
import os


class ExportPlaylistWindow(QDialog):
    def __init__(self):
        super(ExportPlaylistWindow, self).__init__()
        self.setWindowTitle("Export playlist")
        config = ConfigParser()
        config.read("config.ini")
        self.relative_path = config.get("directories", "playlist_relative_path")
        self.export_path = config.get("directories", "playlist_export_path")
        self.selected_playlist_name = "my-playlist.m3u"
        self.current_m3u_path = self.export_path
        self.current_relative_path = self.relative_path
        layout = QVBoxLayout()

        # Header label
        label = QLabel("Playlists")
        label.setFont(QFont("Sans", weight=QFont.Bold))
        layout.addWidget(label)

        # Get playlists from db
        playlist_dict = {}
        with DBA.DBAccess() as db:
            data = db.query("SELECT id, name from playlist;", ())
        for row in data:
            playlist_dict[row[0]] = row[1]

        # Playlist list widget
        self.item_dict = {}
        self.playlist_listWidget = QListWidget(self)
        for i, (k, v) in enumerate(playlist_dict.items()):
            # item_text = f"{i} | {v}"
            item_text = v
            item = QListWidgetItem(item_text)
            self.playlist_listWidget.addItem(item)
            self.item_dict[item_text] = k

        layout.addWidget(self.playlist_listWidget)

        # Relative path checkbox widget
        self.checkbox = QCheckBox(text="Use relative paths?")
        self.checkbox.setChecked(True)
        layout.addWidget(self.checkbox)

        # Relative export path label
        label = QLabel("Relative path")
        label.setFont(QFont("Sans", weight=QFont.Bold))  # bold category
        label.setStyleSheet("text-transform:lowercase;")  # uppercase category
        layout.addWidget(label)

        # Relative export path line edit widget
        self.relative_path_input = QLineEdit(self.relative_path)
        layout.addWidget(self.relative_path_input)

        # Playlist file save path label
        label = QLabel("Playlist file path")
        label.setFont(QFont("Sans", weight=QFont.Bold))
        label.setStyleSheet("text-transform:lowercase;")
        layout.addWidget(label)

        # Playlist file save path line edit widget
        self.m3u_path_input = QLineEdit(self.export_path)
        layout.addWidget(self.m3u_path_input)

        # Save button
        self.save_button = QPushButton("Export")
        layout.addWidget(self.save_button)

        # Signals
        self.save_button.clicked.connect(self.save)
        self.checkbox.toggled.connect(self.relative_path_input.setEnabled)
        self.playlist_listWidget.currentItemChanged.connect(
            self.set_current_selected_playlist
        )
        self.setLayout(layout)
        self.show()

    def set_current_selected_playlist(self) -> None:
        self.selected_playlist_name = (
            self.playlist_listWidget.selectedItems()[0].text() + ".m3u"
        )
        print(self.selected_playlist_name)

    def save(self) -> None:
        """Exports the chosen database playlist to a .m3u file"""
        selected_items = [
            item.text() for item in self.playlist_listWidget.selectedItems()
        ]
        selected_db_ids = [self.item_dict[item] for item in selected_items]
        relative_path = self.relative_path_input.text()
        m3u_path = self.m3u_path_input.text()
        if m3u_path == "" or m3u_path is None:
            self.close()
            return
        for playlist in selected_db_ids:
            try:
                with DBA.DBAccess() as db:
                    db_paths = db.query(
                        "SELECT s.filepath FROM song_playlist as sp JOIN song as s ON s.id = sp.song_id WHERE sp.playlist_id = ?;",
                        (playlist,),
                    )[0]
            except Exception as e:
                logging.error(
                    f"ExportPlaylistWindow.py save() | could not retrieve playlist songs: {e}"
                )
                error_dialog = ErrorDialog(
                    "Could not get songs from this playlist. noooooo"
                )
                error_dialog.exec()
                self.close()
        # Gather playlist song paths
        write_paths = []
        if self.checkbox.isChecked:
            # Relative paths
            for song in db_paths:
                artist, album = get_reorganize_vars(song)
                write_path = os.path.join(
                    relative_path, artist, album, song.split("/")[-1]
                )
                write_paths.append(write_path)
        else:
            # Normal paths
            for song in db_paths:
                write_paths.append(song)
        # Write playlist file
        for line in write_paths:
            pass
        self.close()

    def cancel(self) -> None:
        self.close()
        return
