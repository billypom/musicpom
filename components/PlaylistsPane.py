from PyQt5.QtWidgets import (
    QAction,
    QInputDialog,
    QListWidget,
    QMenu,
    QMessageBox,
    QTreeWidget,
    QTreeWidgetItem,
)
from PyQt5.QtCore import pyqtSignal, Qt, QPoint
import DBA
from logging import debug

from components import CreatePlaylistWindow


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
    playlistCreatedSignal = pyqtSignal()
    allSongsSignal = pyqtSignal()

    def __init__(self: QTreeWidget, parent=None):
        super().__init__(parent)
        self._library_root = QTreeWidgetItem(["Library"])
        self._playlists_root: QTreeWidgetItem = QTreeWidgetItem(["Playlists"])
        self.addTopLevelItem(self._library_root)
        self.addTopLevelItem(self._playlists_root)
        self.reload_playlists()
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.showContextMenu)
        self.currentItemChanged.connect(self.playlist_clicked)
        self.playlist_db_id_choice: int | None = None

    def reload_playlists(self):
        """
        Clears and reinitializes the playlists tree
        each playlist is a branch/child of root node `Playlists`
        """
        # take all children away
        self._playlists_root.takeChildren()
        # NOTE: implement user sorting by adding a column to playlist db table for 'rank' or something
        with DBA.DBAccess() as db:
            playlists = db.query(
                "SELECT id, name FROM playlist ORDER BY date_created DESC LIMIT 1;", ()
            )
        for playlist in playlists:
            branch = PlaylistWidgetItem(self, playlist[0], playlist[1])
            self._playlists_root.addChild(branch)

        self._playlists_root.setExpanded(True)

    def showContextMenu(self, position: QPoint):
        """Right-click context menu"""
        menu = QMenu(self)
        if self.playlist_db_id_choice is not None:
            # only allow delete/rename non-root nodes
            rename_action = QAction("Rename", self)
            delete_action = QAction("Delete", self)
            rename_action.triggered.connect(self.rename_playlist)
            delete_action.triggered.connect(self.delete_playlist)
            menu.addAction(rename_action)
            menu.addAction(delete_action)
        create_action = QAction("New playlist", self)
        create_action.triggered.connect(self.create_playlist)
        menu.addAction(create_action)
        menu.exec_(self.mapToGlobal(position))  # Show the menu

    def create_playlist(self):
        """Creates a database record for a playlist, given a name"""
        window = CreatePlaylistWindow(self.playlistCreatedSignal)
        window.playlistCreatedSignal.connect(self.reload_playlists)  # type: ignore
        window.exec_()

    def rename_playlist(self, *args):
        """
        Asks user for input
        Renames selected playlist based on user input
        """
        text, ok = QInputDialog.getText(
            self, "Rename playlist", "New name:                                 "
        )

        if len(text) > 64:
            QMessageBox.warning(self, "WARNING", "Name must not exceed 64 characters")
            return
        if ok:
            with DBA.DBAccess() as db:
                db.execute(
                    "UPDATE playlist SET name = ? WHERE id = ?;",
                    (text, self.playlist_db_id_choice),
                )
            self.reload_playlists()

    def delete_playlist(self, *args):
        """Deletes a playlist"""
        reply = QMessageBox.question(
            self,
            "Confirmation",
            "Really delete this playlist??",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes,
        )
        if reply == QMessageBox.Yes:
            with DBA.DBAccess() as db:
                db.execute(
                    "DELETE FROM playlist WHERE id = ?;", (self.playlist_db_id_choice,)
                )
            # reload
            self.reload_playlists()

    def playlist_clicked(self, item):
        """Specific playlist pane index was clicked"""
        if item == self._playlists_root or item == self._library_root:
            self.playlist_db_id_choice = None
            # self.all_songs_selected()
            self.allSongsSignal.emit()
        elif isinstance(item, PlaylistWidgetItem):
            debug(f"ID: {item.id}, name: {item.text(0)}")
            self.playlist_db_id_choice = item.id
            self.playlistChoiceSignal.emit(int(item.id))

    # def all_songs_selected(self):
    #     """Emits a signal to display all songs in the library"""
    #     # I have no idea why this has to be in its own function, but it does
    #     # or else it doesn't work
    #     self.allSongsSignal.emit()
