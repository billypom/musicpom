from mutagen.id3 import ID3
import DBA
from PyQt5.QtGui import (
    QDragMoveEvent,
    QStandardItem,
    QStandardItemModel,
    QKeySequence,
    QDragEnterEvent,
    QDropEvent,
    QResizeEvent,
)
from PyQt5.QtWidgets import (
    QAction,
    QHeaderView,
    QMenu,
    QSizePolicy,
    QTableView,
    QShortcut,
    QMessageBox,
    QAbstractItemView,
)
from PyQt5.QtCore import (
    Qt,
    QAbstractItemModel,
    QModelIndex,
    QThreadPool,
    pyqtSignal,
    QTimer,
)
from components.DebugWindow import DebugWindow
from components.ErrorDialog import ErrorDialog
from components.LyricsWindow import LyricsWindow
from components.AddToPlaylistWindow import AddToPlaylistWindow
from components.MetadataWindow import MetadataWindow

from components.ResizableHeaderView import ResizableHeaderView
from main import Worker
from utils.batch_delete_filepaths_from_database import (
    batch_delete_filepaths_from_database,
)
from utils.delete_song_id_from_database import delete_song_id_from_database
from utils.add_files_to_library import add_files_to_library
from utils.get_reorganize_vars import get_reorganize_vars
from utils.update_song_in_database import update_song_in_database
from utils.get_id3_tags import get_id3_tags
from utils.get_album_art import get_album_art
from utils import set_id3_tag
from subprocess import Popen
import logging
import configparser
import os
import shutil
import typing


class MusicTable(QTableView):
    playPauseSignal = pyqtSignal()
    enterKey = pyqtSignal()
    deleteKey = pyqtSignal()
    refreshMusicTable = pyqtSignal()
    handleProgressSignal = pyqtSignal(str)
    getThreadPoolSignal = pyqtSignal()

    def __init__(self, parent=None, application_window=None):
        super().__init__(parent)
        self.application_window = application_window

        # FIXME: why does this give me pyright errors
        self.model = QStandardItemModel()
        self.setModel(self.model)

        # Config
        self.config = configparser.ConfigParser()
        self.config.read("config.ini")
        self.threadpool = QThreadPool
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
        # Header stuff...
        header = ResizableHeaderView(Qt.Horizontal, self)
        self.setHorizontalHeader(header)
        # hide the id column
        self.hideColumn(0)
        # db names of headers
        self.database_columns = str(self.config["table"]["columns"]).split(",")
        self.vertical_scroll_position = 0
        self.songChanged = None
        self.selected_song_filepath = ""
        self.current_song_filepath = ""
        # table_view_column_widths = str(self.config["table"]["column_widths"]).split(",")
        # for i in range(self.model.columnCount() - 1):
        #     self.setColumnWidth(i, int(table_view_column_widths[i]))
        # self.horizontalHeader().setStretchLastSection(True)
        # self.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        # self.horizontalHeader().setCascadingSectionResizes(True)
        # CONNECTIONS
        self.clicked.connect(self.set_selected_song_filepath)
        self.doubleClicked.connect(self.set_current_song_filepath)
        self.enterKey.connect(self.set_current_song_filepath)
        self.deleteKey.connect(self.delete_songs)
        self.model.dataChanged.connect(self.on_cell_data_changed)  # editing cells
        self.model.layoutChanged.connect(self.restore_scroll_position)
        # self.horizontalHeader().sectionResized.connect(self.header_was_resized)
        # Final actions
        self.load_music_table()
        self.setup_keyboard_shortcuts()

    def resizeEvent(self, e: typing.Optional[QResizeEvent]) -> None:
        print(f"QTableView width: {self.size().width()}")
        if e is None:
            raise Exception
        super().resizeEvent(e)

    def header_was_resized(self, logicalIndex, oldSize, newSize):
        self.adjust_section_sizes(logicalIndex, oldSize, newSize)

    def adjust_section_sizes(self, logicalIndex, oldSize, newSize):
        header_width = 0
        current_width = self.size().width()

        for i in range(self.model.columnCount()):
            header_width += self.columnWidth(i)
        if header_width > current_width:
            # we pushing headers too far
            newSize = oldSize
            print("NOOO")
        print(f"total_width = {header_width}")
        print(f"logical index = {logicalIndex}")
        print(f"old size = {oldSize}")
        print(f"new size = {newSize}")
        # super().sectionResized(logicalIndex, oldSize, newSize)

    def contextMenuEvent(self, a0):
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
        if a0 is not None:
            menu.exec_(a0.globalPos())

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
            selected_filepaths = self.get_selected_songs_filepaths()
            worker = Worker(batch_delete_filepaths_from_database, selected_filepaths)
            worker.signals.signal_progress.connect(self.qapp.handle_progress)
            worker.signals.signal_finished.connect(self.remove_selected_row_indices)
            worker.signals.signal_finished.connect(self.load_music_table)
            if self.qapp:
                threadpool = self.qapp.threadpool
                threadpool.start(worker)

    def remove_selected_row_indices(self):
        """Removes rows from the QTableView based on a list of indices"""
        selected_indices = self.get_selected_rows()
        try:
            self.model.dataChanged.disconnect(self.on_cell_data_changed)
        except Exception:
            pass
        for index in selected_indices:
            try:
                self.model.removeRow(index)
            except Exception as e:
                logging.info(f" delete_songs() failed | {e}")
        try:
            self.model.dataChanged.connect(self.on_cell_data_changed)
        except Exception:
            pass

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
            logging.error(f"show_lyrics_menu() | could not retrieve lyrics | {e}")
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
        logging.info(f"dropEvent data: {data}")
        if data and data.hasUrls():
            directories = []
            files = []
            for url in data.urls():
                if url.isLocalFile():
                    path = url.toLocalFile()
                    if os.path.isdir(path):
                        # append 1 directory
                        directories.append(path)
                    else:
                        # append 1 file
                        files.append(path)
            e.accept()
            print(f"directories: {directories}")
            print(f"files: {files}")
            if directories:
                worker = Worker(self.get_audio_files_recursively, directories)
                # worker.signals.signal_progress.connect(self.handle_progress)
                worker.signals.signal_progress.connect(self.qapp.handle_progress)
                worker.signals.signal_result.connect(self.on_recursive_search_finished)
                worker.signals.signal_finished.connect(self.load_music_table)
                if self.qapp:
                    threadpool = self.qapp.threadpool
                    threadpool.start(worker)
            if files:
                self.add_files(files)
        else:
            e.ignore()

    def on_recursive_search_finished(self, result):
        """file search completion handler"""
        if result:
            self.add_files(result)

    # def handle_progress(self, data):
    #     """Emits data to main"""
    #     self.handleProgressSignal.emit(data)

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
        shortcut.activated.connect(self.handle_reorganize_selected_files)

    def on_cell_data_changed(self, topLeft: QModelIndex, bottomRight: QModelIndex):
        """Handles updating ID3 tags when data changes in a cell"""
        logging.info("on_cell_data_changed")
        if isinstance(self.model, QStandardItemModel):
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
            logging.info(f"edited column name: {edited_column_name}")
            response = set_id3_tag(filepath, edited_column_name, user_input_data)
            if response:
                # Update the library with new metadata
                update_song_in_database(song_id, edited_column_name, user_input_data)

    def handle_reorganize_selected_files(self):
        """"""
        worker = Worker(self.reorganize_selected_files)
        worker.signals.signal_progress.connect(self.qapp.handle_progress)
        self.qapp.threadpool.start(worker)

    def reorganize_selected_files(self, progress_callback=None):
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
                if str(filepath).startswith((target_dir)):
                    continue
                try:
                    if progress_callback:
                        progress_callback.emit(f"Organizing: {filepath}")
                    # Read file metadata
                    artist, album = get_reorganize_vars(filepath)
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
                    logging.info(
                        f"reorganize_selected_files() | Moved: {filepath} -> {new_path}"
                    )
                except Exception as e:
                    logging.warning(
                        f"reorganize_selected_files() |  Error moving file: {filepath} | {e}"
                    )
            # Draw the rest of the owl
            self.load_music_table()
            QMessageBox.information(
                self, "Reorganization complete", "Files successfully reorganized"
            )

    def toggle_play_pause(self):
        """Toggles the currently playing song by emitting a Signal"""
        if not self.current_song_filepath:
            self.set_current_song_filepath()
        self.playPauseSignal.emit()

    def add_files(self, files) -> None:
        """Thread handles adding songs to library
        - Drag & Drop song(s) on tableView
        - File > Open > List of song(s)
        """
        logging.info(f"add files, files: {files}")
        worker = Worker(add_files_to_library, files)
        worker.signals.signal_progress.connect(self.qapp.handle_progress)
        worker.signals.signal_finished.connect(self.load_music_table)
        if self.qapp:
            threadpool = self.qapp.threadpool
            threadpool.start(worker)
        else:
            logging.warning("Application window could not be found")
        # add_files_to_library(files, progress_callback)
        return

    def load_music_table(self, *playlist_id):
        """
        Loads data into self (QTableView)
        Default to loading all songs.
        If playlist_id is given, load songs in a particular playlist
        playlist_id is emitted from PlaylistsPane as a tuple (1,)
        """
        try:
            # Loading the table also causes cell data to change, technically
            # so we must disconnect the dataChanged trigger before loading
            # then re-enable after we are done loading
            self.model.dataChanged.disconnect(self.on_cell_data_changed)
        except Exception as e:
            logging.info(
                f"load_music_table() | could not disconnect on_cell_data_changed trigger: {e}"
            )
            pass
        self.vertical_scroll_position = (
            self.verticalScrollBar().value()
        )  # Get my scroll position before clearing
        self.model.clear()
        self.model.setHorizontalHeaderLabels(self.table_headers)
        if playlist_id:
            selected_playlist_id = playlist_id[0]
            logging.info(
                f"load_music_table() | selected_playlist_id: {selected_playlist_id}"
            )
            # Fetch playlist data
            try:
                with DBA.DBAccess() as db:
                    data = db.query(
                        "SELECT s.id, s.title, s.artist, s.album, s.track_number, s.genre, s.codec, s.album_date, s.filepath FROM song s JOIN song_playlist sp ON s.id = sp.song_id WHERE sp.playlist_id = ?",
                        (selected_playlist_id,),
                    )
            except Exception as e:
                logging.warning(f"load_music_table() | Unhandled exception: {e}")
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
                logging.warning(f"load_music_table() | Unhandled exception: {e}")
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
            self.restore_scroll_position()
        except Exception:
            pass
        try:
            self.model.dataChanged.connect(self.on_cell_data_changed)
        except Exception:
            pass

    def restore_scroll_position(self) -> None:
        """Restores the scroll position"""
        logging.info("restore_scroll_position")
        QTimer.singleShot(
            100,
            lambda: self.verticalScrollBar().setValue(self.vertical_scroll_position),
        )

    def get_audio_files_recursively(self, directories, progress_callback=None):
        """Scans a directories for files"""
        extensions = self.config.get("settings", "extensions").split(",")
        audio_files = []
        for directory in directories:
            for root, _, files in os.walk(directory):
                for file in files:
                    if any(file.lower().endswith(ext) for ext in extensions):
                        audio_files.append(os.path.join(root, file))
                        if progress_callback:
                            progress_callback.emit(f"Scanning {file}")
        return audio_files

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
        logging.info(self.selected_song_filepath)

    def set_current_song_filepath(self) -> None:
        """Sets the filepath of the currently playing song"""
        # Setting the current song filepath automatically plays that song
        # self.tableView listens to this function and plays the audio file located at self.current_song_filepath
        self.current_song_filepath = (
            self.currentIndex().siblingAtColumn(self.table_headers.index("path")).data()
        )

    def load_qapp(self, qapp) -> None:
        """Necessary for using members and methods of main application window"""
        self.qapp = qapp
