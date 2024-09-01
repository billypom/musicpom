from PyQt5.QtWidgets import QListWidget, QTreeWidget, QTreeWidgetItem
from PyQt5.QtCore import pyqtSignal
import DBA


class PlaylistWidgetItem(QTreeWidgetItem):
    def __init__(self, parent, id, name):
        super().__init__([name], 0)
        self.id = id


class PlaylistsPane(QTreeWidget):
    playlistChoiceSignal = pyqtSignal(int)
    allSongsSignal = pyqtSignal()

    def __init__(self: QTreeWidget, parent=None):
        super().__init__(parent)
        library_root = QTreeWidgetItem(["Library"])
        self.addTopLevelItem(library_root)
        all_songs_branch = QTreeWidgetItem(["All Songs"])
        library_root.addChild(all_songs_branch)

        self.playlists_root = QTreeWidgetItem(["Playlists"])
        self.addTopLevelItem(self.playlists_root)
        with DBA.DBAccess() as db:
            playlists = db.query("SELECT id, name FROM playlist;", ())
        for playlist in playlists:
            branch = PlaylistWidgetItem(self, playlist[0], playlist[1])
            self.playlists_root.addChild(branch)

        library_root.setExpanded(True)
        self.playlists_root.setExpanded(True)

        self.currentItemChanged.connect(self.playlist_clicked)
        self.playlist_db_id_choice: int | None = None

    def playlist_clicked(self, item):
        if isinstance(item, PlaylistWidgetItem):
            print(f"ID: {item.id}, name: {item.text(0)}")
            self.playlist_db_id_choice = item.id
            self.playlistChoiceSignal.emit(item.id)
        elif item.text(0).lower() == "all songs":
            self.all_songs_selected()

    def all_songs_selected(self):
        self.allSongsSignal.emit()

    def add_latest_playlist_to_tree(self):
        with DBA.DBAccess() as db:
            playlist = db.query(
                "SELECT id, name FROM playlist ORDER BY date_created DESC LIMIT 1;", ()
            )[0]
        branch = PlaylistWidgetItem(self, playlist[0], playlist[1])
        self.playlists_root.addChild(branch)
