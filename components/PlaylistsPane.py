from PyQt5.QtWidgets import QAction, QListWidget, QMenu, QTreeWidget, QTreeWidgetItem
from PyQt5.QtCore import pyqtSignal, Qt, QPoint
import DBA
from logging import debug


class PlaylistWidgetItem(QTreeWidgetItem):
    def __init__(self, parent, id, name):
        super().__init__([name], 0)
        self.id = id

# NOTE: ideas:
# auto sort list (alphabetical?)
# reorder list
# duplicate playlist

class PlaylistsPane(QTreeWidget):
    playlistChoiceSignal = pyqtSignal(int)
    allSongsSignal = pyqtSignal()

    def __init__(self: QTreeWidget, parent=None):
        super().__init__(parent)
        self._library_root = QTreeWidgetItem(["Library"])
        self.addTopLevelItem(self._library_root)
        # all_songs_branch = QTreeWidgetItem(["All Songs"])
        # library_root.addChild(all_songs_branch)

        self._playlists_root = QTreeWidgetItem(["Playlists"])
        self.addTopLevelItem(self._playlists_root)
        with DBA.DBAccess() as db:
            playlists = db.query("SELECT id, name FROM playlist;", ())
        for playlist in playlists:
            branch = PlaylistWidgetItem(self, playlist[0], playlist[1])
            self._playlists_root.addChild(branch)

        # library_root.setExpanded(True)
        self._playlists_root.setExpanded(True)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.showContextMenu)
        self.currentItemChanged.connect(self.playlist_clicked)
        self.playlist_db_id_choice: int | None = None

    def showContextMenu(self, position: QPoint):
        """Right-click context menu"""
        if self.playlist_db_id_choice is None:
            return
            # dont delete or rename the root nodes
        menu = QMenu(self)
        rename_action = QAction("Rename", self)
        delete_action = QAction("Delete", self)
        rename_action.triggered.connect(self.rename_playlist)
        delete_action.triggered.connect(self.delete_playlist)
        menu.addAction(rename_action)
        menu.addAction(delete_action)
        menu.exec_(self.mapToGlobal(position))  # Show the menu

    def rename_playlist(self, *args):
        # TODO: implement this
        pass

    def delete_playlist(self, *args):
        # TODO: implement this
        pass

    def playlist_clicked(self, item):
        """Specific playlist index was clicked"""
        if item == self._playlists_root or item == self._library_root:
            self.playlist_db_id_choice = None
            self.all_songs_selected()
        elif isinstance(item, PlaylistWidgetItem):
            debug(f"ID: {item.id}, name: {item.text(0)}")
            self.playlist_db_id_choice = item.id
            self.playlistChoiceSignal.emit(int(item.id))

    def all_songs_selected(self):
        """Emits a signal to display all songs in the library"""
        # I have no idea why this has to be in its own function, but it does
        # or else it doesn't work
        self.allSongsSignal.emit()

    def add_latest_playlist_to_tree(self):
        """Adds the most recently created playlist to the pane"""
        with DBA.DBAccess() as db:
            playlist = db.query(
                "SELECT id, name FROM playlist ORDER BY date_created DESC LIMIT 1;", ()
            )[0]
        branch = PlaylistWidgetItem(self, playlist[0], playlist[1])
        self.playlists_root.addChild(branch)
