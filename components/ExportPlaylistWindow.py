import logging
import DBA
import os
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
from utils import get_reorganize_vars
from components import ErrorDialog
from configparser import ConfigParser
from pathlib import Path
from appdirs import user_config_dir


class ExportPlaylistWindow(QDialog):
    def __init__(self):
        super(ExportPlaylistWindow, self).__init__()
        self.setWindowTitle("Export playlist")
        self.setMinimumSize(600, 400)
        self.load_config()
        self.relative_path: str = self.config.get(
            "settings", "playlist_content_relative_path"
        )
        self.export_path: str = self.config.get("settings", "playlist_export_path")
        self.selected_playlist_name: str = "my-playlist.m3u"
        self.chosen_list_widget_item: QListWidgetItem | None = None
        layout = self.setup_ui()
        self.setLayout(layout)
        self.show()

    def setup_ui(self):
        layout = QVBoxLayout()

        # Header label
        label = QLabel("Playlists")
        label.setFont(QFont("Sans", weight=QFont.Bold))
        layout.addWidget(label)

        # Get playlists from db
        playlist_dict = {}
        with DBA.DBAccess() as db:
            data = db.query("SELECT id, name from playlist ORDER BY id ASC;", ())
        for row in data:
            playlist_dict[row[0]] = row[1]

        # Playlist list widget
        self.playlist_listWidget = QListWidget(self)
        self.item_dict = {}
        for i, (k, v) in enumerate(playlist_dict.items()):
            # item_text = f"{i+1} | {v}"
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
        self.input_relative_path = QLineEdit(self.relative_path)  # not needed
        layout.addWidget(self.input_relative_path)

        # Playlist file save path label
        label = QLabel("Playlist file path")
        label.setFont(QFont("Sans", weight=QFont.Bold))
        label.setStyleSheet("text-transform:lowercase;")
        layout.addWidget(label)

        # Playlist file save path line edit widget
        self.export_m3u_path = QLineEdit(self.config.get("settings", "playlist_export_path"))
        layout.addWidget(self.export_m3u_path)

        # Save button
        self.save_button = QPushButton("Export")
        layout.addWidget(self.save_button)

        # Signals
        self.save_button.clicked.connect(self.save)
        self.checkbox.toggled.connect(self.input_relative_path.setEnabled)
        self.playlist_listWidget.currentRowChanged.connect(
            self.handle_playlist_selected
        )
        return layout

    def load_config(self):
        self.cfg_file = (
            Path(user_config_dir(appname="musicpom", appauthor="billypom"))
            / "config.ini"
        )
        self.config = ConfigParser()
        self.config.read(self.cfg_file)

    def handle_playlist_selected(self) -> None:
        """
        Sets the current playlist name, then edits the playlist export path
        """
        # Get the current chosen list item
        self.chosen_list_widget_item: QListWidgetItem | None = (
            self.playlist_listWidget.currentItem()
        )
        # We don't care if nothing is chosen
        if self.chosen_list_widget_item is None:
            return

        # Create the filename for the playlist to be exported
        self.selected_playlist_name = self.chosen_list_widget_item.text() + ".m3u"

        # get the db id
        self.selected_playlist_db_id = self.item_dict[
            self.chosen_list_widget_item.text()
        ]

        # alter line edit text for playlist path
        # Make the thing react and show the correct thing or whatever
        current_text: list = self.input_m3u_path.text().split("/")
        if "." in current_text[-1]:
            current_text = current_text[:-1]
        else:
            current_text = current_text
        m3u_text = os.path.join("/", *current_text, self.selected_playlist_name)
        self.input_m3u_path.setText(m3u_text)

    def save(self) -> None:
        """
        Exports the selected playlist to a .m3u file
        - handles writing relative paths, if needed
        """
        if self.chosen_list_widget_item is None:
            return
        relative_path = self.input_relative_path.text()
        output_filename = self.input_m3u_path.text()

        # If no output path is provided, just close the window...
        if output_filename == "" or output_filename is None:
            self.close()
            return

        # Get filepaths for selected playlist from the database
        try:
            with DBA.DBAccess() as db:
                data = db.query(
                    """SELECT s.filepath FROM song_playlist as sp
                    JOIN song as s ON s.id = sp.song_id
                    WHERE sp.playlist_id = ?;""",
                    (int(self.selected_playlist_db_id),),
                )
                db_paths = [path[0] for path in data]
        except Exception as e:
            logging.error(
                f"ExportPlaylistWindow.py save() | could not retrieve playlist songs: {e}"
            )
            error_dialog = ErrorDialog(
                f"Could not get songs from this playlist. noooooo: {e}"
            )
            error_dialog.exec()
            self.close()
            return

        # Gather playlist song paths
        write_paths = []
        if self.checkbox.isChecked:
            # Relative paths
            for song in db_paths:
                artist, album = get_reorganize_vars(song)
                write_path = os.path.join(
                    relative_path, artist, album, song.split("/")[-1] + "\n"
                )
                write_paths.append(str(write_path))
        else:
            # Normal paths
            for song in db_paths:
                write_paths.append(song + "\n")

        # Write playlist file TODO: add threading
        os.makedirs(os.path.dirname(output_filename), exist_ok=True)
        with open(output_filename, "w") as f:
            f.writelines(write_paths)

        self.close()
        return

    def cancel(self) -> None:
        self.close()
        return
