import DBA
from PyQt5.QtWidgets import (
    QDialog,
    QLineEdit,
    QLabel,
    QPushButton,
    QVBoxLayout,
)
from PyQt5.QtGui import QFont


class EditPlaylistOptionsWindow(QDialog):
    def __init__(self, playlist_id):
        super(EditPlaylistOptionsWindow, self).__init__()
        self.setWindowTitle("Playlist options")
        self.setMinimumSize(600, 400)
        self.playlist_id = playlist_id
        # self.playlist_path_prefix: str = self.config.get(
        #     "settings", "playlist_path_prefix"
        # )
        # self.export_path: str = self.config.get("settings", "playlist_export_path")
        # self.selected_playlist_name: str = "my-playlist.m3u"
        # self.chosen_list_widget_item: QListWidgetItem | None = None
        layout = self.setup_ui()
        self.setLayout(layout)
        self.show()

    def setup_ui(self):
        layout = QVBoxLayout()

        # Header label
        label = QLabel("Options")
        label.setFont(QFont("Sans", weight=QFont.Bold))
        layout.addWidget(label)

        # Get options from db
        with DBA.DBAccess() as db:
            data = db.query("SELECT auto_export_path, path_prefix from playlist WHERE id = ?;", (self.playlist_id,))
            auto_export_path = data[0][0]
            path_prefix = data[0][1]

        # Relative export path label
        label = QLabel("Auto export path (../music/playlists/my_playlist.m3u)")
        label.setFont(QFont("Sans", weight=QFont.Bold))  # bold category
        label.setStyleSheet("text-transform:lowercase;")  # uppercase category
        layout.addWidget(label)

        # Relative export path line edit widget
        self.auto_export_path = QLineEdit(auto_export_path)
        layout.addWidget(self.auto_export_path)

        # Playlist file save path label
        label = QLabel("Path prefix (/prefix/song.mp3, /prefix/song2.mp3)")
        label.setFont(QFont("Sans", weight=QFont.Bold))
        label.setStyleSheet("text-transform:lowercase;")
        layout.addWidget(label)

        # Playlist file save path line edit widget
        self.path_prefix = QLineEdit(path_prefix)
        layout.addWidget(self.path_prefix)

        # Save button
        self.save_button = QPushButton("Save")
        layout.addWidget(self.save_button)

        # Signals
        self.save_button.clicked.connect(self.save)
        return layout

    def save(self) -> None:
        """
        Updates the options in the db
        """
        with DBA.DBAccess() as db:
            db.execute('''
                       UPDATE playlist SET auto_export_path = ?, path_prefix = ? WHERE id = ?
                       ''', (self.auto_export_path.text(), self.path_prefix.text(), self.playlist_id)
                       )

        self.close()
        return

    def cancel(self) -> None:
        self.close()
        return
