from mutagen.id3 import ID3
from json import load as jsonload
import DBA
from pprint import pprint
from PyQt5.QtGui import (
    QColor,
    QDragMoveEvent,
    QPainter,
    QPen,
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
    QTableView,
    QShortcut,
    QMessageBox,
    QAbstractItemView,
)
from PyQt5.QtCore import (
    QItemSelectionModel,
    QSortFilterProxyModel,
    Qt,
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

from main import Worker
from utils.batch_delete_filepaths_from_database import (
    batch_delete_filepaths_from_database,
)
from utils.delete_song_id_from_database import delete_song_id_from_database
from utils.add_files_to_database import add_files_to_database
from utils.get_reorganize_vars import get_reorganize_vars
from utils.update_song_in_database import update_song_in_database
from utils.get_id3_tags import get_id3_tags
from utils.get_album_art import get_album_art
from utils import set_id3_tag
from subprocess import Popen
from logging import debug, error
import os
import shutil
import typing
from pathlib import Path
from appdirs import user_config_dir
from configparser import ConfigParser


class MusicTable(QTableView):
    playPauseSignal = pyqtSignal()
    playSignal = pyqtSignal(str)
    enterKey = pyqtSignal()
    deleteKey = pyqtSignal()
    refreshMusicTableSignal = pyqtSignal()
    handleProgressSignal = pyqtSignal(str)
    getThreadPoolSignal = pyqtSignal()

    def __init__(self, parent=None, application_window=None):
        super().__init__(parent)
        # why do i need this?
        self.application_window = application_window

        # NOTE: wtf is actually going on here with the models?
        # Create QStandardItemModel
        # Create QSortFilterProxyModel
        # Set QSortFilterProxyModel source to QStandardItemModel
        # Set QTableView model to the Proxy model
        # so it looks like this, i guess:
        # QTableView model2 = QSortFilterProxyModel(QStandardItemModel)

        # need a standard item model to do actions on cells
        self.model2: QStandardItemModel = QStandardItemModel()
        # proxy model for sorting i guess?
        self.proxymodel = QSortFilterProxyModel()
        self.proxymodel.setSourceModel(self.model2)
        self.setModel(self.proxymodel)
        self.setSortingEnabled(True)

        # Config
        cfg_file = (
            Path(user_config_dir(appname="musicpom", appauthor="billypom"))
            / "config.ini"
        )
        self.config = ConfigParser()
        self.config.read(cfg_file)

        # Threads
        self.threadpool = QThreadPool
        # gui names of headers
        self.table_headers = [
            "title",
            "artist",
            "album",
            "track",
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
        # db names of headers
        self.database_columns = str(self.config["table"]["columns"]).split(",")
        self.vertical_scroll_position = 0
        self.selected_song_filepath = ""
        self.current_song_filepath = ""
        self.current_song_db_id = None
        self.current_song_qmodel_index: QModelIndex

        # Properties
        self.setAcceptDrops(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setEditTriggers(QAbstractItemView.EditTrigger.EditKeyPressed)
        self.setAlternatingRowColors(True)
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        # header
        # FIXME: table headers being resized and going out window bounds
        # causing some recursion errors...
        self.horizontal_header: QHeaderView = self.horizontalHeader()
        assert self.horizontal_header is not None  # i hate look at linting errors
        self.horizontal_header.setStretchLastSection(True)
        self.horizontal_header.setSectionResizeMode(QHeaderView.Interactive)
        self.horizontal_header.sortIndicatorChanged.connect(self.on_sort)
        # dumb vertical estupido
        self.vertical_header: QHeaderView = self.verticalHeader()
        assert self.vertical_header is not None
        self.vertical_header.setVisible(False)

        # CONNECTIONS
        self.clicked.connect(self.on_cell_clicked)
        self.deleteKey.connect(self.delete_songs)
        self.doubleClicked.connect(self.play_audio_file)
        self.enterKey.connect(self.play_audio_file)
        self.model2.dataChanged.connect(self.on_cell_data_changed)  # editing cells
        self.model2.layoutChanged.connect(self.restore_scroll_position)
        self.horizontal_header.sectionResized.connect(self.on_header_resized)
        # Final actions
        self.load_music_table()
        self.setup_keyboard_shortcuts()
        self.load_header_widths()

    #  _________________
    # |                 |
    # |                 |
    # | Built-in Events |
    # |                 |
    # |_________________|

    def resizeEvent(self, e: typing.Optional[QResizeEvent]) -> None:
        """Do something when the QTableView is resized"""
        if e is None:
            raise Exception
        super().resizeEvent(e)

    def paintEvent(self, e):
        """Override paint event to highlight the current cell"""
        # First do the default painting
        super().paintEvent(e)

        # Check if we have a current cell
        current_index = self.currentIndex()
        if current_index and current_index.isValid():
            # Get the visual rect for the current cell
            rect = self.visualRect(current_index)

            # Create a painter for custom drawing
            with QPainter(self.viewport()) as painter:
                # Draw a border around the current cell
                pen = QPen(QColor("#4a90e2"), 2)  # Blue, 2px width
                painter.setPen(pen)
                painter.drawRect(rect.adjusted(1, 1, -1, -1))

    def contextMenuEvent(self, a0):
        """Right-click context menu"""
        menu = QMenu(self)
        add_to_playlist_action = QAction("Add to playlist", self)
        add_to_playlist_action.triggered.connect(self.add_selected_files_to_playlist)
        menu.addAction(add_to_playlist_action)
        # edit metadata
        edit_metadata_action = QAction("Edit metadata", self)
        edit_metadata_action.triggered.connect(self.edit_selected_files_metadata)
        menu.addAction(edit_metadata_action)
        # edit lyrics
        edit_lyrics_action = QAction("Lyrics (View/Edit)", self)
        edit_lyrics_action.triggered.connect(self.show_lyrics_menu)
        menu.addAction(edit_lyrics_action)
        # jump to current song in table
        jump_to_current_song_action = QAction("Jump to current song", self)
        jump_to_current_song_action.triggered.connect(self.jump_to_current_song)
        menu.addAction(jump_to_current_song_action)
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
        debug("dropEvent")
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
            if directories:
                worker = Worker(self.get_audio_files_recursively, directories)
                worker.signals.signal_progress.connect(self.handle_progress)
                worker.signals.signal_result.connect(
                    self.on_get_audio_files_recursively_finished
                )
                worker.signals.signal_finished.connect(self.load_music_table)
                if self.qapp:
                    threadpool = self.qapp.threadpool
                    threadpool.start(worker)
            if files:
                self.add_files_to_library(files)
        else:
            e.ignore()

    def keyPressEvent(self, e):
        """Press a key. Do a thing"""
        if not e:
            return

        key = e.key()
        if key == Qt.Key.Key_Space:
            self.toggle_play_pause()

        elif key == Qt.Key.Key_Right:
            index = self.currentIndex()
            new_index = self.model2.index(index.row(), index.column() + 1)
            if new_index.isValid():
                # print(f"right -> ({new_index.row()},{new_index.column()})")
                self.setCurrentIndex(new_index)
                self.viewport().update()  # type: ignore
            super().keyPressEvent(e)
            return

        elif key == Qt.Key.Key_Left:
            index = self.currentIndex()
            new_index = self.model2.index(index.row(), index.column() - 1)
            if new_index.isValid():
                # print(f"left -> ({new_index.row()},{new_index.column()})")
                self.setCurrentIndex(new_index)
                self.viewport().update()  # type: ignore
            super().keyPressEvent(e)
            return

        elif key == Qt.Key.Key_Up:
            index = self.currentIndex()
            new_index = self.model2.index(index.row() - 1, index.column())
            if new_index.isValid():
                # print(f"up -> ({new_index.row()},{new_index.column()})")
                self.setCurrentIndex(new_index)
                self.viewport().update()  # type: ignore
            super().keyPressEvent(e)
            return

        elif key == Qt.Key.Key_Down:
            index = self.currentIndex()
            new_index = self.model2.index(index.row() + 1, index.column())
            if new_index.isValid():
                # print(f"down -> ({new_index.row()},{new_index.column()})")
                self.setCurrentIndex(new_index)
                self.viewport().update()  # type: ignore
            super().keyPressEvent(e)
            return

        elif key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            if self.state() != QAbstractItemView.EditingState:
                self.enterKey.emit()  # Enter key detected
            else:
                super().keyPressEvent(e)
        else:  # Default behavior
            super().keyPressEvent(e)

    #  ____________________
    # |                    |
    # |                    |
    # | On action handlers |
    # |                    |
    # |____________________|

    def find_qmodel_index_by_value(self, model, column: int, value) -> QModelIndex:
        for row in range(model.rowCount()):
            index = model.index(row, column)
            if index.data() == value:
                return index
        return QModelIndex()  # Invalid index if not found

    def on_sort(self):
        debug("on_sort")
        search_col_num = self.table_headers.index("path")
        qmodel_index = self.find_qmodel_index_by_value(
            self.model2, search_col_num, self.current_song_filepath
        )
        self.set_qmodel_index(qmodel_index)
        self.jump_to_current_song()

        # ```python
        # (method) def match(
        #     start: QModelIndex,
        #     role: int,
        #     value: Any,
        #     hits: int = ...,
        #     flags: MatchFlags | MatchFlag = ...
        # ) -> List[QModelIndex]
        # ```

    def on_cell_clicked(self, index):
        """
        When a cell is clicked, do some stuff :)
        - this func also runs when double click happens, fyi
        """
        debug("on_cell_clicked")
        self.set_selected_song_filepath()
        self.viewport().update()  # type: ignore

    def on_header_resized(self, logicalIndex, oldSize, newSize):
        """Handles keeping headers inside the viewport"""
        # https://stackoverflow.com/questions/46775438/how-to-limit-qheaderview-size-when-resizing-sections
        col_count = self.model2.columnCount()
        qtableview_width = self.size().width()
        sum_of_cols = self.horizontal_header.length()
        # debug(f'qtable_width: {qtableview_width}')
        # debug(f'sum of cols: {sum_of_cols}')

        # check for discrepancy
        if sum_of_cols != qtableview_width:
            # if not the last header
            if logicalIndex < col_count:
                next_header_size = self.horizontal_header.sectionSize(logicalIndex + 1)
                # If it should shrink
                if next_header_size > (sum_of_cols - qtableview_width):
                    # shrink it
                    self.horizontal_header.resizeSection(
                        logicalIndex + 1,
                        next_header_size - (sum_of_cols - qtableview_width),
                    )
                else:
                    # block the resize
                    self.horizontal_header.resizeSection(logicalIndex, oldSize)

    def on_cell_data_changed(self, topLeft: QModelIndex, bottomRight: QModelIndex):
        """Handles updating ID3 tags when data changes in a cell"""
        if isinstance(self.model2, QStandardItemModel):
            debug("on_cell_data_changed | doing the normal stuff")
            # get the ID of the row that was edited
            id_index = self.model2.index(topLeft.row(), 0)  # ID is column 0, always
            # get the db song_id from the row
            song_id = self.model2.data(id_index, Qt.ItemDataRole.UserRole)
            # get the filepath through a series of steps...
            # NOTE: filepath is always the last column
            filepath_column_idx = self.model2.columnCount() - 1
            filepath_index = self.model2.index(topLeft.row(), filepath_column_idx)
            filepath = self.model2.data(filepath_index)
            # update the ID3 information
            user_input_data = topLeft.data()
            edited_column_name = self.database_columns[topLeft.column()]
            debug(f"on_cell_data_changed | edited column name: {edited_column_name}")
            response = set_id3_tag(filepath, edited_column_name, user_input_data)
            if response:
                # Update the library with new metadata
                update_song_in_database(song_id, edited_column_name, user_input_data)
            return

    def handle_progress(self, data):
        """Emits data to main"""
        self.handleProgressSignal.emit(data)

    def on_get_audio_files_recursively_finished(self, result):
        """file search completion handler"""
        if result:
            self.add_files_to_library(result)

    def on_add_files_to_database_finished(self, *args):
        """
        Shows failed to import files and reasons
        Runs after worker process signal_finished for add_files_to_database()

        Args:
            - args: ((return_data),)
            - data returned from the original worker process function are returned here
              as the first item in a tuple
        """
        # FIXME:
        # TODO: make this prettier, show a table in a window instead of raw text probably
        _, details = args[0][:2]
        if details:
            window = DebugWindow(details)
            window.exec_()

    #  ____________________
    # |                    |
    # |                    |
    # |       Verbs        |
    # |                    |
    # |____________________|

    def set_qmodel_index(self, index: QModelIndex):
        self.current_song_qmodel_index = index

    def play_audio_file(self):
        """
        Sets the current song filepath
        Emits a signal that the current song should start playback
        """
        self.set_current_song_filepath()
        self.playSignal.emit(self.current_song_filepath)

    def add_files_to_library(self, files: list[str]) -> None:
        """
        Spawns a worker thread - adds a list of filepaths to the library
        - Drag & Drop song(s) on tableView
        - File > Open > List of song(s)
        """
        worker = Worker(add_files_to_database, files)
        worker.signals.signal_progress.connect(self.qapp.handle_progress)
        worker.signals.signal_result.connect(self.on_add_files_to_database_finished)
        worker.signals.signal_finished.connect(self.load_music_table)
        if self.qapp:
            threadpool = self.qapp.threadpool
            threadpool.start(worker)
        else:
            error("Application window could not be found")

    def add_selected_files_to_playlist(self):
        """Opens a playlist choice menu and adds the currently selected files to the chosen playlist"""
        playlist_choice_window = AddToPlaylistWindow(self.get_selected_songs_db_ids())
        playlist_choice_window.exec_()

    def delete_songs(self):
        """Asks to delete the currently selected songs from the db and music table (not the filesystem)"""
        # FIXME: need to get indexes based on the proxy model
        selected_filepaths = self.get_selected_songs_filepaths()
        formatted_selected_filepaths = "\n".join(selected_filepaths)
        reply = QMessageBox.question(
            self,
            "Confirmation",
            f"Remove these songs from the library? (Files stay on your computer)\n{formatted_selected_filepaths}",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes,
        )
        if reply == QMessageBox.Yes:
            pprint(selected_filepaths)
            worker = Worker(batch_delete_filepaths_from_database, selected_filepaths)
            worker.signals.signal_progress.connect(self.qapp.handle_progress)
            worker.signals.signal_finished.connect(self.delete_selected_row_indices)
            if self.qapp:
                threadpool = self.qapp.threadpool
                threadpool.start(worker)

    def delete_selected_row_indices(self):
        """
        Removes rows from the QTableView based on a list of indices
        and then reload the table
        """
        selected_indices = self.get_selected_rows()
        self.disconnect_data_changed()
        for index in selected_indices:
            try:
                self.model2.removeRow(index)
            except Exception as e:
                debug(f"delete_selected_row_indices() failed | {e}")
        self.connect_data_changed()
        self.load_music_table()

    def edit_selected_files_metadata(self):
        """Opens a form with metadata from the selected audio files"""
        files = self.get_selected_songs_filepaths()
        song_ids = self.get_selected_songs_db_ids()
        window = MetadataWindow(self.refreshMusicTable, files, song_ids)
        window.refreshMusicTableSignal.connect(self.load_music_table)
        window.exec_()  # Display the preferences window modally

    def jump_to_current_song(self):
        """Moves screen to the currently playing song, and selects the row"""
        debug("jump_to_current_song")
        # get the proxy model index
        proxy_index = self.proxymodel.mapFromSource(self.current_song_qmodel_index)
        self.scrollTo(proxy_index)
        self.selectRow(proxy_index.row())

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

    def show_id3_tags_debug_menu(self):
        """Shows ID3 tags for a specific .mp3 file"""
        if self.get_selected_song_filepath() is not None:
            window = DebugWindow(str(self.get_selected_song_metadata()))
            window.exec_()

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
            error(f"show_lyrics_menu() | could not retrieve lyrics | {e}")
            lyrics = ""
        lyrics_window = LyricsWindow(selected_song_filepath, lyrics)
        lyrics_window.exec_()

    def setup_keyboard_shortcuts(self):
        """Setup shortcuts here"""
        shortcut = QShortcut(QKeySequence("Ctrl+Shift+R"), self)
        shortcut.activated.connect(self.confirm_reorganize_files)
        # Delete key?
        shortcut = QShortcut(QKeySequence("Delete"), self)
        shortcut.activated.connect(self.delete_songs)

    def confirm_reorganize_files(self) -> None:
        """
        Ctrl+Shift+R = Reorganize
        Asks user to confirm reorganizing files,
        then starts a new thread to do the work
        """
        filepaths = self.get_selected_songs_filepaths()
        # Confirmation screen (yes, no)
        reply = QMessageBox.question(
            self,
            "Confirmation",
            "Are you sure you want to reorganize these files?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes,
        )
        if reply == QMessageBox.Yes:
            worker = Worker(self.reorganize_files, filepaths)
            worker.signals.signal_progress.connect(self.handle_progress)
            worker.signals.signal_finished.connect(self.load_music_table)
            self.qapp.threadpool.start(worker)

    def reorganize_files(self, filepaths, progress_callback=None):
        """
        Reorganizes files into Artist/Album/Song,
        based on self.config['directories'][reorganize_destination']
        """
        debug("reorganizing files")
        # FIXME: batch update, instead of doing 1 file at a time
        # DBAccess is being instantiated for every file, boo
        # NOTE:
        # is that even possible with move file function?

        # Get target directory
        target_dir = str(self.config["directories"]["reorganize_destination"])
        for filepath in filepaths:
            # Read file metadata
            artist, album = get_reorganize_vars(filepath)
            # Determine the new path that needs to be made
            new_path = os.path.join(
                target_dir, artist, album, os.path.basename(filepath)
            )
            # Need to determine if filepath is equal
            if new_path == filepath:
                continue
            try:
                if progress_callback:
                    progress_callback.emit(f"Organizing: {filepath}")
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
                # debug(f"reorganize_files() | Moved: {filepath} -> {new_path}")
            except Exception as e:
                error(f"reorganize_files() | Error moving file: {filepath} | {e}")
        # Draw the rest of the owl
        # QMessageBox.information(
        #     self, "Reorganization complete", "Files successfully reorganized"
        # )

    def toggle_play_pause(self):
        """Toggles the currently playing song by emitting a Signal"""
        if not self.current_song_filepath:
            self.set_current_song_filepath()
        self.playPauseSignal.emit()

    def load_music_table(self, *playlist_id):
        """
        Loads data into self (QTableView)
        Loads all songs in library, by default
        Loads songs from a playlist, if `playlist_id` is given

        hint: You get a `playlist_id` from the signal emitted from PlaylistsPane as a tuple (1,)
        """
        self.disconnect_data_changed()
        self.disconnect_layout_changed()
        self.vertical_scroll_position = self.verticalScrollBar().value()  # type: ignore
        self.model2.clear()
        self.model2.setHorizontalHeaderLabels(self.table_headers)
        if playlist_id:  # Load a playlist
            # Fetch playlist data
            selected_playlist_id = playlist_id[0]
            try:
                debug(
                    f"load_music_table() | selected_playlist_id: {selected_playlist_id}"
                )
                with DBA.DBAccess() as db:
                    data = db.query(
                        "SELECT s.id, s.title, s.artist, s.album, s.track_number, s.genre, s.codec, s.album_date, s.filepath FROM song s JOIN song_playlist sp ON s.id = sp.song_id WHERE sp.playlist_id = ?",
                        (selected_playlist_id,),
                    )
            except Exception as e:
                error(f"load_music_table() | Unhandled exception: {e}")
                return
        else:  # Load the library
            try:
                with DBA.DBAccess() as db:
                    data = db.query(
                        "SELECT id, title, artist, album, track_number, genre, codec, album_date, filepath FROM song;",
                        (),
                    )
            except Exception as e:
                error(f"load_music_table() | Unhandled exception: {e}")
                return
        # Populate the model
        for row_data in data:
            id, *rest_of_data = row_data
            # handle different datatypes
            items = []
            for item in rest_of_data:
                if isinstance(item, int):
                    std_item = QStandardItem()
                    std_item.setData(item, Qt.ItemDataRole.DisplayRole)
                    std_item.setData(item, Qt.ItemDataRole.EditRole)
                else:
                    std_item = QStandardItem(str(item) if item else "")
                items.append(std_item)

            self.model2.appendRow(items)
            # store database id in the row object using setData
            # - useful for fast db fetching and other model operations
            for item in items:
                item.setData(id, Qt.ItemDataRole.UserRole)
        self.model2.layoutChanged.emit()  # emits a signal that the view should be updated
        self.connect_data_changed()
        self.connect_layout_changed()

    def load_header_widths(self):
        """
        Loads the header widths from the last application close.
        """
        table_view_column_widths = str(self.config["table"]["column_widths"]).split(",")
        if not isinstance(table_view_column_widths[0], int):
            return
        if not isinstance(table_view_column_widths, list):
            for i in range(self.model2.columnCount() - 1):
                self.setColumnWidth(i, int(table_view_column_widths[i]))

    def sort_table_by_multiple_columns(self):
        """
        Sorts the data in QTableView (self) by multiple columns
        as defined in config.ini
        """
        # TODO: Rewrite this function to use self.load_music_table() with dynamic SQL queries
        # in order to sort the data more effectively & have more control over UI refreshes.

        # Disconnect these signals to prevent unnecessary loads
        debug("sort_table_by_multiple_columns()")
        self.disconnect_data_changed()
        self.disconnect_layout_changed()
        sort_orders = []
        config_sort_orders: list[int] = [
            int(x) for x in self.config["table"]["sort_orders"].split(",")
        ]
        for order in config_sort_orders:
            if order == 0:
                sort_orders.append(None)
            elif order == 1:
                sort_orders.append(Qt.SortOrder.AscendingOrder)
            elif order == 2:
                sort_orders.append(Qt.SortOrder.DescendingOrder)

        # QTableView sorts need to happen in reverse order
        # The primary sort column is the last column sorted.
        for i in reversed(range(len(sort_orders))):
            if sort_orders[i] is not None:
                debug(f"sorting column {i} by {sort_orders[i]}")
                self.sortByColumn(i, sort_orders[i])
                # WARNING:
                # sortByColumn calls a SELECT statement,
                # and will do this for as many sorts that are needed
                # maybe not a huge deal for a small music application...?
                # `len(config_sort_orders)` number of SELECTs

        self.connect_data_changed()
        self.connect_layout_changed()
        # self.model2.layoutChanged.emit()

    def restore_scroll_position(self) -> None:
        """Restores the scroll position"""
        debug("restore_scroll_position (inactive)")
        # QTimer.singleShot(
        #     100,
        #     lambda: self.verticalScrollBar().setValue(self.vertical_scroll_position),
        # )

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
        """
        Returns a list of indexes for every selected row, agnostic of proxy model
        This gets the actual index in the root table
        """
        selection_model: QItemSelectionModel | None = self.selectionModel()
        assert selection_model is not None  # begone linter error
        return [index.row() for index in selection_model.selectedRows()]

    def get_selected_songs_filepaths(self) -> list[str]:
        """
        Returns a list of the filepaths for the currently selected songs, based on the proxy model
        (things could be sorted differently)
        """
        selected_rows = self.get_selected_rows()
        filepaths = []
        for row in selected_rows:
            idx = self.proxymodel.index(row, self.table_headers.index("path"))
            filepaths.append(idx.data())
        return filepaths

    def get_selected_song_filepath(self) -> str:
        """Returns the selected songs filepath"""
        return self.selected_song_filepath

    def get_selected_song_metadata(self) -> ID3 | dict:
        """Returns the selected song's ID3 tags"""
        return get_id3_tags(self.selected_song_filepath)[0]

    def get_selected_songs_db_ids(self) -> list:
        """Returns a list of id's for the selected songs"""
        indexes = self.selectedIndexes()
        if not indexes:
            return []
        selected_rows = set(index.row() for index in indexes)
        id_list = [
            self.model2.data(self.model2.index(row, 0), Qt.ItemDataRole.UserRole)
            for row in selected_rows
        ]
        return id_list

    def get_current_song_filepath(self) -> str:
        """Returns the currently playing song filepath"""
        return self.current_song_filepath

    def get_current_song_metadata(self) -> ID3 | dict:
        """Returns the currently playing song's ID3 tags"""
        return get_id3_tags(self.current_song_filepath)[0]

    def get_current_song_album_art(self) -> bytes:
        """Returns the APIC data (album art lol) for the currently playing song"""
        return get_album_art(self.current_song_filepath)

    def set_selected_song_filepath(self) -> None:
        """Sets the filepath of the currently selected song"""
        self.selected_song_filepath = (
            self.currentIndex().siblingAtColumn(self.table_headers.index("path")).data()
        )

    def set_current_song_filepath(self) -> None:
        """
        Sets the current song filepath to the value in column 'path' with current selected row index
        also stores the QModelIndex for some useful navigation stuff
        """
        # map proxy (sortable) model to the original model (used for interactions)
        source_index = self.proxymodel.mapToSource(self.currentIndex())
        # set the proxy model index
        self.set_current_song_qmodel_index(source_index)
        # update the filepath
        self.current_song_filepath: str = (
            self.current_song_qmodel_index.siblingAtColumn(
                self.table_headers.index("path")
            ).data()
        )

    def set_current_song_qmodel_index(self, index: QModelIndex):
        self.current_song_qmodel_index: QModelIndex = index

    def load_qapp(self, qapp) -> None:
        """Necessary for using members and methods of main application window"""
        self.qapp = qapp

    #  ____________________
    # |                    |
    # |                    |
    # | Connection  Mgmt   |
    # |                    |
    # |____________________|

    def disconnect_data_changed(self):
        """Disconnects the dataChanged signal from QTableView.model"""
        try:
            self.model2.dataChanged.disconnect()
        except Exception:
            pass

    def connect_data_changed(self):
        """Connects the dataChanged signal from QTableView.model"""
        try:
            self.model2.dataChanged.connect(self.on_cell_data_changed)
        except Exception:
            pass

    def disconnect_layout_changed(self):
        """Disconnects the layoutChanged signal from QTableView.model"""
        try:
            self.model2.layoutChanged.disconnect()
        except Exception:
            pass

    def connect_layout_changed(self):
        """Connects the layoutChanged signal from QTableView.model"""
        try:
            self.model2.layoutChanged.connect(self.restore_scroll_position)
        except Exception:
            pass


# QT Roles

# In Qt, roles are used to specify different aspects or types of data associated with each item in a model. The roles are defined in the Qt.ItemDataRole enum. The three roles you asked about - DisplayRole, EditRole, and UserRole - are particularly important. Let's break them down:
#
# Qt.ItemDataRole.DisplayRole:
# This is the default role for displaying data in views. It determines how the data appears visually in the view.
#
# Purpose: To provide the text or image that will be shown in the view.
# Example: In a table view, this is typically the text you see in each cell.
#
#
# Qt.ItemDataRole.EditRole:
# This role is used when the item's data is being edited.
#
# Purpose: To provide the data in a format suitable for editing.
# Example: For a date field, DisplayRole might show "Jan 1, 2023", but EditRole could contain a QDate object or an ISO format string "2023-01-01".
#
#
# Qt.ItemDataRole.UserRole:
# This is a special role that serves as a starting point for custom roles defined by the user.
#
# Purpose: To store additional, custom data associated with an item that doesn't fit into the predefined roles.
# Example: Storing a unique identifier, additional metadata, or any other custom data you want to associate with the item.
