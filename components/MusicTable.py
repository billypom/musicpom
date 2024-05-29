from mutagen.easyid3 import EasyID3
import DBA
from PyQt5.QtGui import (
    QStandardItem,
    QStandardItemModel,
    QKeySequence,
    QDragEnterEvent,
    QDropEvent,
)
from PyQt5.QtWidgets import QAction, QMenu, QTableView, QShortcut, QMessageBox, QAbstractItemView
from PyQt5.QtCore import QModelIndex, Qt, pyqtSignal, QTimer
from utils import add_files_to_library
from utils import update_song_in_library
from utils import get_id3_tags
from utils import get_album_art
from utils import set_id3_tag
from subprocess import Popen
import logging
import configparser
import os
import shutil


class MusicTable(QTableView):
    playPauseSignal = pyqtSignal()
    enterKey = pyqtSignal()

    def __init__(self, parent=None):
        # QTableView.__init__(self, parent)
        super().__init__(parent)
        self.model = QStandardItemModel(self)
        # Necessary for actions related to cell values
        self.setModel(self.model)  # Same as above
        self.config = configparser.ConfigParser()
        self.config.read("config.ini")
        # gui names of headers
        self.table_headers = [
            "title",
            "artist",
            "album",
            "genre",
            "codec",
            "year",
            "path",
        ]
        # id3 names of headers
        self.id3_headers = [
            "title",
            "artist",
            "album",
            "content_type",
            None,
            None,
            None,
        ]
        # db names of headers
        self.database_columns = str(self.config["table"]["columns"]).split(",")
        self.vertical_scroll_position = 0
        self.songChanged = None
        self.selected_song_filepath = ''
        self.current_song_filepath = ''
        # self.tableView.resizeColumnsToContents()
        self.clicked.connect(self.set_selected_song_filepath)
        # doubleClicked is a built in event for QTableView - we listen for this event and run set_current_song_filepath
        self.doubleClicked.connect(self.set_current_song_filepath)
        self.enterKey.connect(self.set_current_song_filepath)
        self.fetch_library()
        self.setup_keyboard_shortcuts()
        self.model.dataChanged.connect(self.on_cell_data_changed)  # editing cells
        self.model.layoutChanged.connect(self.restore_scroll_position)

    def contextMenuEvent(self, event):
        """Show a context menu when you right-click a row"""
        menu = QMenu(self)
        # delete song
        delete_action = QAction("Delete", self)
        delete_action.triggered.connect(self.delete_songs)
        menu.addAction(delete_action)
        # lyrics
        lyrics_menu = QAction("Lyrics (View/Edit)", self)
        lyrics_menu.triggered.connect(self.show_lyrics_menu)
        menu.addAction(lyrics_menu)
        # open in file explorer
        open_containing_folder_action = QAction("Open in system file manager", self)
        open_containing_folder_action.triggered.connect(self.open_directory)
        menu.addAction(open_containing_folder_action)
        # show
        self.set_selected_song_filepath()
        menu.exec_(event.globalPos())

    def delete_songs(self):
        """Deletes the currently selected songs from the db and table (not the filesystem)"""
        reply = QMessageBox.question(
            self,
            "Confirmation",
            "Are you sure you want to delete these songs?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes,
        )
        if reply:
            # selected_rows = self.get_selected_rows()
            selected_filepaths = self.get_selected_songs_filepaths()
            # for index in selected_rows:
            #     self.model().removeRow(index)
            for file in selected_filepaths:
                with DBA.DBAccess() as db:
                    db.execute('DELETE FROM library WHERE filepath = ?', (file,))

    def open_directory(self):
        filepath = self.get_selected_song_filepath().split('/')
        filepath.pop()
        path = '/'.join(filepath)
        Popen(["xdg-open", path])

    def show_lyrics_menu(self):
        pass

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dragMoveEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent):
        if event.mimeData().hasUrls():
            files = []
            for url in event.mimeData().urls():
                if url.isLocalFile():
                    files.append(url.path())
            self.add_files(files)
            event.accept()
        else:
            event.ignore()

    def setup_keyboard_shortcuts(self):
        """Setup shortcuts here"""
        shortcut = QShortcut(QKeySequence("Ctrl+Shift+R"), self)
        shortcut.activated.connect(self.reorganize_selected_files)

    def on_cell_data_changed(self, topLeft: QModelIndex, bottomRight: QModelIndex):
        """Handles updating ID3 tags when data changes in a cell"""
        print("on_cell_data_changed")
        id_index = self.model.index(topLeft.row(), 0)  # ID is column 0, always
        library_id = self.model.data(id_index, Qt.UserRole)
        # filepath is always the last column
        filepath_column_idx = self.model.columnCount() - 1
        filepath_index = self.model.index(topLeft.row(), filepath_column_idx)
        # exact index of the edited cell in 2d space
        filepath = self.model.data(filepath_index)  # filepath
        # update the ID3 information
        user_input_data = topLeft.data()
        edited_column_name = self.database_columns[topLeft.column()]
        print(f"edited column name: {edited_column_name}")
        response = set_id3_tag(filepath, edited_column_name, user_input_data)
        if response:
            # Update the library with new metadata
            update_song_in_library(library_id, edited_column_name, user_input_data)

    def reorganize_selected_files(self):
        """Ctrl+Shift+R = Reorganize"""
        filepaths = self.get_selected_songs_filepaths()
        # Confirmation screen (yes, no)
        reply = QMessageBox.question(
            self,
            "Confirmation",
            "Are you sure you want to reorganize these files?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes,
        )
        if reply:
            # Get target directory
            target_dir = str(self.config["directories"]["reorganize_destination"])
            for filepath in filepaths:
                try:
                    # Read file metadata
                    audio = EasyID3(filepath)
                    artist = audio.get("artist", ["Unknown Artist"])[0]
                    album = audio.get("album", ["Unknown Album"])[0]
                    # Determine the new path that needs to be made
                    new_path = os.path.join(
                        target_dir, artist, album, os.path.basename(filepath)
                    )
                    # Create the directories if they dont exist
                    os.makedirs(os.path.dirname(new_path), exist_ok=True)
                    # Move the file to the new directory
                    shutil.move(filepath, new_path)
                    # Update the db
                    with DBA.DBAccess() as db:
                        db.query(
                            "UPDATE library SET filepath = ? WHERE filepath = ?",
                            (new_path, filepath),
                        )
                    print(f"Moved: {filepath} -> {new_path}")
                except Exception as e:
                    print(f"Error moving file: {filepath} | {e}")
            # Draw the rest of the owl
            self.model.dataChanged.disconnect(self.on_cell_data_changed)
            self.fetch_library()
            self.model.dataChanged.connect(self.on_cell_data_changed)
            QMessageBox.information(
                self, "Reorganization complete", "Files successfully reorganized"
            )

    def keyPressEvent(self, event):
        """Press a key. Do a thing"""
        key = event.key()
        if key == Qt.Key_Space:  # Spacebar to play/pause
            self.toggle_play_pause()
        elif key == Qt.Key_Up:  # Arrow key navigation
            current_index = self.currentIndex()
            new_index = self.model.index(
                current_index.row() - 1, current_index.column()
            )
            if new_index.isValid():
                self.setCurrentIndex(new_index)
        elif key == Qt.Key_Down:  # Arrow key navigation
            current_index = self.currentIndex()
            new_index = self.model.index(
                current_index.row() + 1, current_index.column()
            )
            if new_index.isValid():
                self.setCurrentIndex(new_index)
        elif key in (Qt.Key_Return, Qt.Key_Enter):
            if self.state() != QAbstractItemView.EditingState:
                self.enterKey.emit()  # Enter key detected
            else:
                super().keyPressEvent(event)
        else:  # Default behavior
            super().keyPressEvent(event)

    def toggle_play_pause(self):
        """Toggles the currently playing song by emitting a signal"""
        if not self.current_song_filepath:
            self.set_current_song_filepath()
        self.playPauseSignal.emit()

    def fetch_library(self):
        """Initialize the tableview model"""
        self.vertical_scroll_position = (
            self.verticalScrollBar().value()
        )  # Get my scroll position before clearing
        # temporarily disconnect the datachanged signal to avoid EVERY SONG getting triggered
        self.model.clear()
        self.model.setHorizontalHeaderLabels(self.table_headers)
        # Fetch library data
        with DBA.DBAccess() as db:
            data = db.query(
                "SELECT id, title, artist, album, genre, codec, album_date, filepath FROM library;",
                (),
            )
        # Populate the model
        for row_data in data:
            id, *rest_of_data = row_data
            items = [QStandardItem(str(item)) for item in rest_of_data]
            self.model.appendRow(items)
            # store id using setData - useful for later faster db fetching
            row = self.model.rowCount() - 1
            for item in items:
                item.setData(id, Qt.UserRole)
        # Update the viewport/model
        self.model.layoutChanged.emit()  # emits a signal that the view should be updated

    def restore_scroll_position(self) -> None:
        """Restores the scroll position"""
        QTimer.singleShot(
            100,
            lambda: self.verticalScrollBar().setValue(self.vertical_scroll_position),
        )

    def add_files(self, files) -> None:
        """When song(s) added to the library, update the tableview model
        - Drag & Drop song(s) on tableView
        - File > Open > List of song(s)
        """
        number_of_files_added = add_files_to_library(files)
        if number_of_files_added:
            self.model.dataChanged.disconnect(self.on_cell_data_changed)
            self.fetch_library()
            self.model.dataChanged.connect(self.on_cell_data_changed)

    def get_selected_rows(self) -> list[int]:
        """Returns a list of indexes for every selected row"""
        selection_model = self.selectionModel()
        return [index.row() for index in selection_model.selectedRows()]

    def get_selected_songs_filepaths(self) -> list[str]:
        """Returns a list of the filepaths for the currently selected songs"""
        selected_rows = self.get_selected_rows()
        filepaths = []
        for row in selected_rows:
            idx = self.model.index(row, self.table_headers.index("path"))
            filepaths.append(idx.data())
        return filepaths

    def get_selected_song_filepath(self) -> str:
        """Returns the selected songs filepath"""
        return self.selected_song_filepath

    def get_selected_song_metadata(self) -> EasyID3 | dict:
        """Returns the selected song's ID3 tags"""
        return get_id3_tags(self.selected_song_filepath)

    def get_current_song_filepath(self) -> str:
        """Returns the currently playing song filepath"""
        return self.current_song_filepath

    def get_current_song_metadata(self) -> EasyID3 | dict:
        """Returns the currently playing song's ID3 tags"""
        return get_id3_tags(self.current_song_filepath)

    def get_current_song_album_art(self) -> bytes:
        """Returns the APIC data (album art lol) for the currently playing song"""
        return get_album_art(self.current_song_filepath)

    def set_selected_song_filepath(self) -> None:
        """Sets the filepath of the currently selected song"""
        self.selected_song_filepath = (
            self.currentIndex().siblingAtColumn(self.table_headers.index("path")).data()
        )
        print(self.selected_song_filepath)

    def set_current_song_filepath(self) -> None:
        """Sets the filepath of the currently playing song"""
        # Setting the current song filepath automatically plays that song
        # self.tableView listens to this function and plays the audio file located at self.current_song_filepath
        self.current_song_filepath = (
            self.currentIndex().siblingAtColumn(self.table_headers.index("path")).data()
        )

    def load_qapp(self, qapp) -> None:
        """Necessary for talking between components..."""
        self.qapp = qapp
