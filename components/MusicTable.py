from mutagen.id3 import ID3
import DBA
from PyQt5.QtGui import (
    QDragMoveEvent,
    QStandardItem,
    QStandardItemModel,
    QKeySequence,
    QDragEnterEvent,
    QDropEvent,
)
from PyQt5.QtWidgets import (
    QAction,
    QMenu,
    QTableView,
    QShortcut,
    QMessageBox,
    QAbstractItemView,
)
from PyQt5.QtCore import QAbstractItemModel, QModelIndex, Qt, pyqtSignal, QTimer
from components.DebugWindow import DebugWindow
from components.ErrorDialog import ErrorDialog
from components.LyricsWindow import LyricsWindow
from components.AddToPlaylistWindow import AddToPlaylistWindow
from components.MetadataWindow import MetadataWindow
from utils.delete_song_id_from_database import delete_song_id_from_database
from utils.add_files_to_library import add_files_to_library
from utils.update_song_in_database import update_song_in_database
from utils.get_id3_tags import get_id3_tags
from utils.get_album_art import get_album_art
from utils import set_id3_tag
from subprocess import Popen
import logging
import configparser
import os
import shutil


class MusicTable(QTableView):
    playPauseSignal = pyqtSignal()
    enterKey = pyqtSignal()
    deleteKey = pyqtSignal()
    refreshMusicTable = pyqtSignal()

    def __init__(self: QTableView, parent=None):
        # QTableView.__init__(self, parent)
        super().__init__(parent)
        # Necessary for actions related to cell values
        # FIXME: why does this give me pyright errors
        self.model = QStandardItemModel(self)
        # self.model = QAbstractItemModel(self)
        self.setModel(self.model)

        # Config
        self.config = configparser.ConfigParser()
        self.config.read("config.ini")
        # gui names of headers
        self.table_headers = [
            "title",
            "artist",
            "album",
            "track_number",
            "genre",
            "codec",
            "year",
            "path",
        ]
        # id3 names of headers
        self.id3_headers = [
            "TIT2",
            "TPE1",
            "TALB",
            "TRCK",
            "content_type",
            None,
            "TDRC",
            None,
        ]
        # hide the id column
        self.hideColumn(0)
        # db names of headers
        self.database_columns = str(self.config["table"]["columns"]).split(",")
        self.vertical_scroll_position = 0
        self.songChanged = None
        self.selected_song_filepath = ""
        self.current_song_filepath = ""
        # self.tableView.resizeColumnsToContents()
        self.clicked.connect(self.set_selected_song_filepath)
        # doubleClicked is a built in event for QTableView - we listen for this event and run set_current_song_filepath
        self.doubleClicked.connect(self.set_current_song_filepath)
        self.enterKey.connect(self.set_current_song_filepath)
        self.deleteKey.connect(self.delete_songs)
        self.model.dataChanged.connect(self.on_cell_data_changed)  # editing cells
        self.model.layoutChanged.connect(self.restore_scroll_position)

        self.load_music_table()
        self.setup_keyboard_shortcuts()

    def contextMenuEvent(self, event):
        """Right-click context menu for rows in Music Table"""
        menu = QMenu(self)
        add_to_playlist_action = QAction("Add to playlist", self)
        add_to_playlist_action.triggered.connect(self.add_selected_files_to_playlist)
        menu.addAction(add_to_playlist_action)
        # edit metadata
        edit_metadata_action = QAction("Edit metadata", self)
        edit_metadata_action.triggered.connect(self.edit_selected_files_metadata)
        menu.addAction(edit_metadata_action)
        # edit lyrics
        lyrics_menu = QAction("Lyrics (View/Edit)", self)
        lyrics_menu.triggered.connect(self.show_lyrics_menu)
        menu.addAction(lyrics_menu)
        # open in file explorer
        open_containing_folder_action = QAction("Open in system file manager", self)
        open_containing_folder_action.triggered.connect(self.open_directory)
        menu.addAction(open_containing_folder_action)
        # view id3 tags (debug)
        view_id3_tags_debug = QAction("View ID3 tags (debug)", self)
        view_id3_tags_debug.triggered.connect(self.show_id3_tags_debug_menu)
        menu.addAction(view_id3_tags_debug)
        # delete song
        delete_action = QAction("Delete", self)
        delete_action.triggered.connect(self.delete_songs)
        menu.addAction(delete_action)
        # show
        self.set_selected_song_filepath()
        menu.exec_(event.globalPos())

    def show_id3_tags_debug_menu(self):
        """Shows ID3 tags for a specific .mp3 file"""
        selected_song_filepath = self.get_selected_song_filepath()
        if selected_song_filepath is None:
            return
        current_song = self.get_selected_song_metadata()
        lyrics_window = DebugWindow(selected_song_filepath, str(current_song))
        lyrics_window.exec_()

    def delete_songs(self):
        """Deletes the currently selected songs from the db and music table (not the filesystem)"""
        reply = QMessageBox.question(
            self,
            "Confirmation",
            "Remove these songs from the library? (Files stay on your computer)",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes,
        )
        if reply:
            model = self.model
            selected_filepaths = self.get_selected_songs_filepaths()
            selected_indices = self.get_selected_rows()
            for file in selected_filepaths:
                with DBA.DBAccess() as db:
                    song_id = db.query(
                        "SELECT id FROM song WHERE filepath = ?", (file,)
                    )[0][0]
                delete_song_id_from_database(song_id)
            self.model.dataChanged.disconnect(self.on_cell_data_changed)
            for index in selected_indices:
                try:
                    model.removeRow(index)
                except Exception as e:
                    logging.info(f"MusicTable.py delete_songs() failed | {e}")
            self.load_music_table()
            self.model.dataChanged.connect(self.on_cell_data_changed)

    def open_directory(self):
        """Opens the currently selected song in the system file manager"""
        if self.get_selected_song_filepath() is None:
            QMessageBox.warning(
                self,
                "File does not exist",
                "No file is selected, or the file does not exist",
                QMessageBox.Ok,
                QMessageBox.Ok,
            )
            return
        filepath = self.get_selected_song_filepath().split("/")
        filepath.pop()
        path = "/".join(filepath)
        Popen(["xdg-open", path])

    def edit_selected_files_metadata(self):
        # FIXME:
        """Opens a form with metadata from the selected audio files"""
        files = self.get_selected_songs_filepaths()
        song_ids = self.get_selected_songs_db_ids()
        window = MetadataWindow(self.refreshMusicTable, files, song_ids)
        window.refreshMusicTableSignal.connect(self.load_music_table)
        window.exec_()  # Display the preferences window modally

    def add_selected_files_to_playlist(self):
        """Opens a playlist choice menu and adds the currently selected files to the chosen playlist"""
        playlist_choice_window = AddToPlaylistWindow(self.get_selected_songs_db_ids())
        playlist_choice_window.exec_()

    def show_lyrics_menu(self):
        """Shows the lyrics for the currently selected song"""
        selected_song_filepath = self.get_selected_song_filepath()
        if selected_song_filepath is None:
            return
        current_song = self.get_selected_song_metadata()
        try:
            uslt_tags = [tag for tag in current_song.keys() if tag.startswith("USLT::")]
            if uslt_tags:
                lyrics = next((current_song[tag].text for tag in uslt_tags), "")
            else:
                raise RuntimeError("No USLT tags found in song metadata")
        except Exception as e:
            print(f"MusicTable.py | show_lyrics_menu | could not retrieve lyrics | {e}")
            lyrics = ""
        lyrics_window = LyricsWindow(selected_song_filepath, lyrics)
        lyrics_window.exec_()

    def dragEnterEvent(self, e: QDragEnterEvent | None):
        if e is None:
            return
        data = e.mimeData()
        if data and data.hasUrls():
            e.accept()
        else:
            e.ignore()

    def dragMoveEvent(self, e: QDragMoveEvent | None):
        if e is None:
            return
        data = e.mimeData()
        if data and data.hasUrls():
            e.accept()
        else:
            e.ignore()

    def dropEvent(self, e: QDropEvent | None):
        if e is None:
            return
        data = e.mimeData()
        if data and data.hasUrls():
            files = []
            for url in data.urls():
                if url.isLocalFile():
                    files.append(url.path())
            self.add_files(files)
            e.accept()
        else:
            e.ignore()

    def keyPressEvent(self, e):
        """Press a key. Do a thing"""
        if not e:
            return
        key = e.key()
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
                super().keyPressEvent(e)
        else:  # Default behavior
            super().keyPressEvent(e)

    def setup_keyboard_shortcuts(self):
        """Setup shortcuts here"""
        shortcut = QShortcut(QKeySequence("Ctrl+Shift+R"), self)
        shortcut.activated.connect(self.reorganize_selected_files)

    def on_cell_data_changed(self, topLeft: QModelIndex, bottomRight: QModelIndex):
        """Handles updating ID3 tags when data changes in a cell"""
        print("on_cell_data_changed")
        id_index = self.model.index(topLeft.row(), 0)  # ID is column 0, always
        song_id = self.model.data(id_index, Qt.UserRole)
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
            update_song_in_database(song_id, edited_column_name, user_input_data)

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
                    audio = ID3(filepath)
                    try:
                        artist = audio["TPE1"].text[0]
                        if artist == "":
                            artist = "Unknown Artist"
                    except KeyError:
                        artist = "Unknown Artist"

                    try:
                        album = audio["TALB"].text[0]
                        if album == "":
                            album = "Unknown Album"
                    except KeyError:
                        album = "Unknown Album"

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
                            "UPDATE song SET filepath = ? WHERE filepath = ?",
                            (new_path, filepath),
                        )
                    print(f"Moved: {filepath} -> {new_path}")
                except Exception as e:
                    logging.warning(
                        f"MusicTable.py reorganize_selected_files() |  Error moving file: {filepath} | {e}"
                    )
                    print(
                        f"MusicTable.py reorganize_selected_files() |  Error moving file: {filepath} | {e}"
                    )
            # Draw the rest of the owl
            # self.model.dataChanged.disconnect(self.on_cell_data_changed)
            self.load_music_table()
            # self.model.dataChanged.connect(self.on_cell_data_changed)
            QMessageBox.information(
                self, "Reorganization complete", "Files successfully reorganized"
            )

    def toggle_play_pause(self):
        """Toggles the currently playing song by emitting a signal"""
        if not self.current_song_filepath:
            self.set_current_song_filepath()
        self.playPauseSignal.emit()

    def load_music_table(self, *playlist_id):
        """
        Loads data into self (QTableView)
        Default to loading all songs.
        If playlist_id is given, load songs in a particular playlist
        """
        try:
            # Loading the table also causes cell data to change, technically
            # so we must disconnect the dataChanged trigger before loading
            # then re-enable after we are done loading
            self.model.dataChanged.disconnect(self.on_cell_data_changed)
        except Exception as e:
            print(
                f"MusicTable.py load_music_table() | could not disconnect on_cell_data_changed trigger: {e}"
            )
            pass
        self.vertical_scroll_position = (
            self.verticalScrollBar().value()
        )  # Get my scroll position before clearing
        # temporarily disconnect the datachanged signal to avoid EVERY SONG getting triggered
        self.model.clear()
        self.model.setHorizontalHeaderLabels(self.table_headers)
        if playlist_id:
            playlist_id = playlist_id[0]
            # Fetch playlist data
            try:
                with DBA.DBAccess() as db:
                    data = db.query(
                        "SELECT s.id, s.title, s.artist, s.album, s.track_number, s.genre, s.codec, s.album_date, s.filepath FROM song s JOIN song_playlist sp ON s.id = sp.id WHERE sp.id = ?",
                        (playlist_id,),
                    )
            except Exception as e:
                logging.warning(
                    f"MusicTable.py | load_music_table | Unhandled exception: {e}"
                )
                return
        else:
            # Fetch library data
            try:
                with DBA.DBAccess() as db:
                    data = db.query(
                        "SELECT id, title, artist, album, track_number, genre, codec, album_date, filepath FROM song;",
                        (),
                    )
            except Exception as e:
                logging.warning(
                    f"MusicTable.py | load_music_table | Unhandled exception: {e}"
                )
                return
        # Populate the model
        for row_data in data:
            id, *rest_of_data = row_data
            items = [QStandardItem(str(item) if item else "") for item in rest_of_data]
            self.model.appendRow(items)
            # store id using setData - useful for later faster db fetching
            # row = self.model.rowCount() - 1
            for item in items:
                item.setData(id, Qt.UserRole)
        self.model.layoutChanged.emit()  # emits a signal that the view should be updated
        try:
            self.model.dataChanged.connect(self.on_cell_data_changed)
            self.restore_scroll_position()
        except Exception:
            pass

    def restore_scroll_position(self) -> None:
        """Restores the scroll position"""
        print("restore_scroll_position")
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
            self.load_music_table()
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

    def get_selected_song_metadata(self) -> ID3 | dict:
        """Returns the selected song's ID3 tags"""
        return get_id3_tags(self.selected_song_filepath)

    def get_selected_songs_db_ids(self) -> list:
        """Returns a list of id's for the selected songs"""
        indexes = self.selectedIndexes()
        if not indexes:
            return []
        selected_rows = set(index.row() for index in indexes)
        id_list = [
            self.model.data(self.model.index(row, 0), Qt.UserRole)
            for row in selected_rows
        ]
        # selected_ids = []
        # for index in indexes:
        #     model_item = self.model.item(index.row())
        #     id_data = model_item.data(Qt.UserRole)
        #     selected_ids.append(id_data)
        return id_list

    def get_current_song_filepath(self) -> str:
        """Returns the currently playing song filepath"""
        return self.current_song_filepath

    def get_current_song_metadata(self) -> ID3 | dict:
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
