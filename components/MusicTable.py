import DBA
from PyQt5.QtGui import (
    QColor,
    QDragMoveEvent,
    QFont,
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
    QApplication,
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
    QTimer,
    Qt,
    QModelIndex,
    pyqtSignal,
)
from components.DebugWindow import DebugWindow
from components.LyricsWindow import LyricsWindow
from components.AddToPlaylistWindow import AddToPlaylistWindow
from components.MetadataWindow import MetadataWindow
from components.QuestionBoxDetails import QuestionBoxDetails
from components.HeaderTags import HeaderTags2

from utils import (
    batch_delete_filepaths_from_database,
    batch_delete_filepaths_from_playlist,
    add_files_to_database,
    get_reorganize_vars,
    update_song_in_database,
    id3_remap,
    get_tags,
    set_tag,
    Worker
)
from subprocess import Popen
from logging import debug, error
import os
import shutil
import typing
from pathlib import Path
from appdirs import user_config_dir
from configparser import ConfigParser

class MusicTable(QTableView):
    playlistStatsSignal: pyqtSignal = pyqtSignal(str)
    loadMusicTableSignal: pyqtSignal = pyqtSignal()
    sortSignal: pyqtSignal = pyqtSignal()
    playPauseSignal: pyqtSignal = pyqtSignal()
    playSignal: pyqtSignal = pyqtSignal(str)
    enterKey: pyqtSignal = pyqtSignal()
    deleteKey: pyqtSignal = pyqtSignal()
    refreshMusicTableSignal: pyqtSignal = pyqtSignal()
    handleProgressSignal: pyqtSignal = pyqtSignal(str)
    getThreadPoolSignal: pyqtSignal = pyqtSignal()
    searchBoxSignal: pyqtSignal = pyqtSignal()
    focusEnterSignal: pyqtSignal = pyqtSignal()
    focusLeaveSignal: pyqtSignal = pyqtSignal()

    def __init__(self, parent=None, application_window=None):
        super().__init__(parent)
        # why do i need this?
        self.application_window = application_window
        # Config
        self.config = ConfigParser()
        self.cfg_file = (
            Path(user_config_dir(appname="musicpom", appauthor="billypom"))
            / "config.ini"
        )
        _ = self.config.read(self.cfg_file)

        font: QFont = QFont()
        font.setPointSize(11)
        self.setFont(font)

        # NOTE:
        # QTableView model2 = QSortFilterProxyModel(QStandardItemModel)
        #
        # wtf is actually going on here with the models?
        # Create QStandardItemModel
        # Create QSortFilterProxyModel
        # Set QSortFilterProxyModel source to QStandardItemModel
        # Set QTableView model to the Proxy model
        # so it looks like the above note, i guess

        # need a QStandardItemModel to load data & do actions on cells
        self.model2: QStandardItemModel = QStandardItemModel()
        self.proxymodel: QSortFilterProxyModel = QSortFilterProxyModel()
        self.data_cache = {}
        self.playlist_scroll_positions: dict[int | None, int] = {}
        self.search_string: str | None = None
        self.headers = HeaderTags2()
        self.selected_song_filepath = ""
        self.selected_song_qmodel_index: QModelIndex
        self.current_song_filepath = ""
        self.current_song_db_id = None
        self.current_song_qmodel_index: QModelIndex
        self.selected_playlist_id: int | None = None
        self.current_playlist_id: int | None = None

        # proxy model for sorting i guess?
        self.proxymodel.setSourceModel(self.model2)
        self.proxymodel.setSortCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.setModel(self.proxymodel)
        self.setSortingEnabled(True)

        # Properties
        self.setAcceptDrops(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        # self.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerItem)
        self.setEditTriggers(QAbstractItemView.EditTrigger.EditKeyPressed)
        self.setAlternatingRowColors(True)
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        # header
        self.horizontal_header: QHeaderView = self.horizontalHeader()
        assert self.horizontal_header is not None  # i hate look at linting errors
        self.horizontal_header.setSectionResizeMode(QHeaderView.Interactive)
        self.horizontal_header.sortIndicatorChanged.connect(self.on_user_sort_change)
        self.horizontal_header.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.horizontal_header.customContextMenuRequested.connect(self.show_header_context_menu)
        # dumb vertical estupido
        self.vertical_header: QHeaderView = self.verticalHeader()
        assert self.vertical_header is not None
        self.vertical_header.setVisible(False)

        # CONNECTIONS
        self.clicked.connect(self.on_cell_clicked)
        self.deleteKey.connect(self.delete_songs)
        self.doubleClicked.connect(self.play_selected_audio_file)
        self.enterKey.connect(self.play_selected_audio_file)
        self.model2.dataChanged.connect(self.on_cell_data_changed)  # editing cells
        # Final actions
        # self.load_music_table()
        self.setup_keyboard_shortcuts()

    #  _________________
    # |                 |
    # |                 |
    # | Built-in Events |
    # |                 |
    # |_________________|

    def focusInEvent(self, e):
        """
        Event filter: when self is focused
        """
        self.focusEnterSignal.emit()
        # arrow keys act normal
        super().focusInEvent(e)

    def focusOutEvent(self, e):
        """
        Event filter: when self becomes unfocused
        """
        self.focusLeaveSignal.emit()


    def resizeEvent(self, e: typing.Optional[QResizeEvent]) -> None:
        """
        Do something when the QTableView is resized
        We will recalculate column widths based on the new table width,
        retaining the ratio of the original column widths.
        """
        super().resizeEvent(e)
        if e is None:
            raise Exception
        self.load_header_widths(self.saved_column_ratios)

    def showEvent(self, a0):
        """
        When the table is shown:
        - Set the widths very small, then set them to sizes relative to our stored ratios
        - This is to prevent issues with the widths on app startup
        """
        super().showEvent(a0)
        widths = []
        for _ in self.saved_column_ratios:
            widths.append('0.001')
        self.load_header_widths(widths)
        QTimer.singleShot(0, lambda: self.load_header_widths(self.saved_column_ratios))

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
        font: QFont = QFont()
        font.setPointSize(11)

        menu = QMenu(self)
        menu.setFont(font)

        add_to_playlist_action = QAction("Add to playlist", self)
        _ = add_to_playlist_action.triggered.connect(self.add_selected_files_to_playlist)
        menu.addAction(add_to_playlist_action)
        # edit metadata
        edit_metadata_action = QAction("Edit metadata", self)
        _ = edit_metadata_action.triggered.connect(self.edit_selected_files_metadata)
        menu.addAction(edit_metadata_action)
        # edit lyrics
        edit_lyrics_action = QAction("Lyrics (View/Edit)", self)
        _ = edit_lyrics_action.triggered.connect(self.show_lyrics_menu)
        menu.addAction(edit_lyrics_action)
        # jump to current song in table
        jump_to_current_song_action = QAction("Jump to current song", self)
        _ = jump_to_current_song_action.triggered.connect(self.jump_to_current_song)
        menu.addAction(jump_to_current_song_action)
        # open in file explorer
        open_containing_folder_action = QAction(
            "Open in system file manager", self)
        _ = open_containing_folder_action.triggered.connect(self.open_directory)
        menu.addAction(open_containing_folder_action)
        # view id3 tags (debug)
        view_id3_tags_debug = QAction("View ID3 tags (debug)", self)
        _ = view_id3_tags_debug.triggered.connect(self.view_id3_tags_debug_menu)
        menu.addAction(view_id3_tags_debug)
        # delete song
        delete_action = QAction("Delete", self)
        _ = delete_action.triggered.connect(self.delete_songs)
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
        if data and data.hasUrls():
            directories: list[str] = []
            files: list[str] = []
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
                _ = worker.signals.signal_progress.connect(self.handle_progress)
                _ = worker.signals.signal_result.connect(self.on_get_audio_files_recursively_finished)
                _ = worker.signals.signal_finished.connect(self.load_music_table)
                if self.qapp:
                    threadpool = self.qapp.threadpool # type: ignore
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

        if key == Qt.Key.Key_Right:
            index = self.currentIndex()
            new_index = self.model2.index(index.row(), index.column() + 1)
            if new_index.isValid():
                self.setCurrentIndex(new_index)
                self.viewport().update()
            super().keyPressEvent(e)
            return

        elif key == Qt.Key.Key_Left:
            index = self.currentIndex()
            new_index = self.model2.index(index.row(), index.column() - 1)
            if new_index.isValid():
                self.setCurrentIndex(new_index)
                self.viewport().update()
            super().keyPressEvent(e)
            return

        elif key == Qt.Key.Key_Up:
            index = self.currentIndex()
            new_index = self.model2.index(index.row() - 1, index.column())
            if new_index.isValid():
                self.setCurrentIndex(new_index)
                self.viewport().update()
            super().keyPressEvent(e)
            return

        elif key == Qt.Key.Key_Down:
            index = self.currentIndex()
            new_index = self.model2.index(index.row() + 1, index.column())
            if new_index.isValid():
                self.setCurrentIndex(new_index)
                self.viewport().update()
            super().keyPressEvent(e)
            return

        elif key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            if self.state() != QAbstractItemView.EditingState:
                self.enterKey.emit()
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



    def on_user_sort_change(self, column: int, order: Qt.SortOrder):
        """
        Called when user clicks a column header to sort.
        Updates the multi-sort config based on interaction.
        """
        try:
            db_field = self.headers.db_list[column]
        except IndexError:
            error(f"Invalid column index: {column}")
            return

        raw = self.config["table"].get("sort_order", "")
        sort_list = []

        # Parse current sort_order from config
        if raw:
            for item in raw.split(","):
                if ":" not in item:
                    continue
                field, dir_str = item.strip().split(":")
                direction = Qt.SortOrder.AscendingOrder if dir_str == "1" else Qt.SortOrder.DescendingOrder
                sort_list.append((field, direction))

        # Update or insert the new sort field at the end (highest priority)
        sort_list = [(f, d) for f, d in sort_list if f != db_field]  # remove if exists
        sort_list.append((db_field, order))  # add with latest order

        # Save back to config
        self.save_sort_config(sort_list)

        # Re-apply the updated sort order
        self.sort_by_logical_fields()

    def on_sort(self):
        self.find_current_and_selected_bits()
        self.jump_to_selected_song()
        self.sortSignal.emit()

    def on_cell_clicked(self, index):
        """
        When a cell is clicked, do some stuff :)
        - this func also runs when double click happens, fyi
        """
        # print(index.row(), index.column())
        self.set_selected_song_filepath()
        self.set_selected_song_qmodel_index()
        self.viewport().update()  # type: ignore

    def on_cell_data_changed(self, topLeft: QModelIndex, bottomRight: QModelIndex):
        """Handles updating ID3 tags when data changes in a cell"""
        # if isinstance(self.model2, QStandardItemModel):
        # debug("on_cell_data_changed")
        # get the ID of the row that was edited
        id_index = self.model2.index(topLeft.row(), 0)
        # get the db song_id from the row
        song_id: int = self.model2.data(id_index, Qt.ItemDataRole.UserRole)
        user_index = self.headers.db_list.index("filepath")
        filepath = self.currentIndex().siblingAtColumn(user_index).data()
        # update the ID3 information
        user_input_data: str = topLeft.data()
        edited_column_name: str = self.headers.db_list[topLeft.column()]
        # debug(f"on_cell_data_changed | edited column name: {edited_column_name}")
        response = set_tag(
            filepath=filepath, 
            db_column=edited_column_name, 
            value=user_input_data
        )
        if response:
            # Update the library with new metadata
            _ = update_song_in_database(song_id, edited_column_name, user_input_data)
        else:
            error('ERROR: response failed')
        return

    def handle_progress(self, data: object):
        """Emits data to main"""
        self.handleProgressSignal.emit(data)

    def on_get_audio_files_recursively_finished(self, result: list[str]):
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
        try:
            _, details = args[0][:2]
            details = dict(tuple(details)[0])
            if details:
                window = DebugWindow(details)
                window.exec_()
        except IndexError:
            pass
        except Exception as e:
            debug(
                f"on_add_files_to_database_finished() | Something went wrong: {e}")

    #  ____________________
    # |                    |
    # |                    |
    # |       Verbs        |
    # |                    |
    # |____________________|


    def show_header_context_menu(self, position):
        """
        Show context menu on right-click in the horizontal header.
        """
        menu = QMenu()
        clear_action = QAction("Clear all sorts", self)
        clear_action.triggered.connect(self.clear_all_sorts)
        menu.addAction(clear_action)
        # Show menu at global position
        global_pos = self.horizontal_header.mapToGlobal(position)
        menu.exec(global_pos)


    def clear_all_sorts(self):
        """
        Clears all stored sort orders and refreshes the table view.
        """
        self.config["table"]["sort_order"] = ""
        with open(self.config_path, "w") as f:
            self.config.write(f)
        # Clear sort visually
        self.horizontal_header.setSortIndicator(-1, Qt.SortOrder.AscendingOrder)
        # Reload data if necessary, or just reapply sorting
        self.sort_by_logical_fields()

    def find_qmodel_index_by_value(self, model, column: int, value) -> QModelIndex:
        for row in range(model.rowCount()):
            index = model.index(row, column)
            if index.data() == value:
                return index
        return QModelIndex()  # Invalid index if not found


    def get_current_header_width_ratios(self) -> list[str]:
        """
        Get the current header widths, as ratios
        """
        total_table_width = self.size().width()
        column_ratios = []
        for i in range(self.model2.columnCount()):
        # for i in range(self.model2.columnCount() - 1):
            column_width = self.columnWidth(i)
            ratio = column_width / total_table_width
            column_ratios.append(str(round(ratio, 4)))
        # debug(f'get_current_header_width_ratios = {column_ratios}')
        return column_ratios

    def save_header_ratios(self):
        """
        Saves the current header widths to memory and file, as ratios
        """
        # WARNING: DOES NOT WORK and is not used. 
        # the same functionality is implemented in main.py closeEvent()
        self.saved_column_ratios = self.get_current_header_width_ratios()
        column_ratios_as_string = ",".join(self.saved_column_ratios)
        self.config["table"]["column_ratios"] = column_ratios_as_string
        # Save the config
        try:
            with open(self.cfg_file, "w") as configfile:
                self.config.write(configfile)
        except Exception as e:
            debug(f"wtf man {e}")
        debug(f"Saved column ratios: {self.saved_column_ratios}")

    def load_header_widths(self, ratios: list[str] | None = None):
        """
        Loads the header widths, based on saved ratios
        or pass in a list of ratios to be loaded
        """
        self.horizontal_header.setStretchLastSection(True)
        if ratios is None:
            column_ratios = self.get_current_header_width_ratios()
        else:
            column_ratios = ratios
        total_table_width = self.size().width()
        column_widths = []
        for ratio in column_ratios:
            column_widths.append(float(ratio) * total_table_width)
        if isinstance(column_widths, list):
            # for i in range(self.model2.columnCount() - 1):
            for i in range(self.model2.columnCount()):
                self.setColumnWidth(i, int(column_widths[i]))


    def set_qmodel_index(self, index: QModelIndex):
        self.current_song_qmodel_index = index

    def play_selected_audio_file(self):
        """
        Sets the current song filepath
        Emits a signal that the current song should start playback
        """
        self.set_current_song_qmodel_index()
        self.set_current_song_filepath()
        self.playSignal.emit(self.current_song_filepath)

    def add_files_to_library(self, files: list[str]) -> None:
        """
        Spawns a worker thread - adds a list of filepaths to the library

        - Drag & Drop song(s) on tableView
        - File > Open > List of song(s)
        """
        # debug('add_files_to_library()')
        worker = Worker(add_files_to_database, files, None)
        _ = worker.signals.signal_progress.connect(self.qapp.handle_progress) # type: ignore
        _ = worker.signals.signal_result.connect(self.on_add_files_to_database_finished)
        _ = worker.signals.signal_finished.connect(self.load_music_table)
        if self.qapp:
            threadpool = self.qapp.threadpool # type: ignore
            threadpool.start(worker)
        else:
            error("Application window could not be found")

    def add_selected_files_to_playlist(self):
        """Opens a playlist choice menu and adds the currently selected files to the chosen playlist"""
        playlist_choice_window = AddToPlaylistWindow(
            self.get_selected_songs_db_ids())
        playlist_choice_window.exec_()

    def delete_songs(self):
        """Asks to delete the currently selected songs from the db and music table (not the filesystem)"""
        # NOTE: provide extra questionbox option?
        # | Delete from playlist & lib | Delete from playlist only | Cancel |
        # Currently, this just deletes from the playlist, or the main lib & any playlists
        selected_filepaths = self.get_selected_songs_filepaths()
        if self.selected_playlist_id:
            question_dialog = QuestionBoxDetails(
                title="Delete songs",
                description="Remove these songs from the playlist?",
                data=selected_filepaths,
            )
            reply = question_dialog.execute()
            if reply:
                worker = Worker(batch_delete_filepaths_from_playlist, selected_filepaths, self.selected_playlist_id)
                worker.signals.signal_progress.connect(self.qapp.handle_progress) # type: ignore
                worker.signals.signal_finished.connect(self.delete_selected_row_indices)
                if self.qapp:
                    threadpool = self.qapp.threadpool # type: ignore
                    threadpool.start(worker)
        else:
            question_dialog = QuestionBoxDetails(
                title="Delete songs",
                description="Remove these songs from the library?\n(This will remove the songs from all playlists)",
                data=selected_filepaths,
            )
            reply = question_dialog.execute()
            if reply:
                worker = Worker(batch_delete_filepaths_from_database, selected_filepaths)
                worker.signals.signal_progress.connect(self.qapp.handle_progress) # type: ignore
                worker.signals.signal_finished.connect(self.delete_selected_row_indices)
                if self.qapp:
                    threadpool = self.qapp.threadpool # type: ignore
                    threadpool.start(worker)

    # def delete_selected_row_indices(self):
    #     """
    #     Removes rows from the QTableView based on a list of indices
    #     and then reload the table
    #     """
    #     debug('delete_selected_row_indices')
    #     selected_indices = self.get_selected_rows()
    #     for index in selected_indices:
    #         try:
    #             self.model2.removeRow(index)
    #         except Exception as e:
    #             debug(f"delete_selected_row_indices() failed | {e}")
    #     self.model2.layoutChanged.emit()  # emits a signal that the view should be updated
    #     # self.viewport().update()

    def delete_selected_row_indices(self):
        """
        Removes rows from the QTableView (which uses a proxy model)
        by mapping selected proxy indices to the source model.
        """
        selected_proxy_indices = self.get_selected_rows()
        selected_source_rows = [
            self.proxymodel.mapToSource(self.proxymodel.index(row, 0)).row()
            for row in selected_proxy_indices
        ]
        # Delete in reverse to maintain correct indexes to delete
        for source_row in sorted(selected_source_rows, reverse=True):
            try:
                self.model2.removeRow(source_row)
            except Exception as e:
                debug(f"delete_selected_row_indices() failed | {e}")

    def edit_selected_files_metadata(self):
        """Opens a form with metadata from the selected audio files"""
        files = self.get_selected_songs_filepaths()
        song_ids = self.get_selected_songs_db_ids()
        window = MetadataWindow(self.refreshMusicTableSignal, self.headers, files, song_ids)
        window.refreshMusicTableSignal.connect(self.load_music_table)
        window.exec_()  # Display the preferences window modally

    def jump_to_selected_song(self):
        """Moves screen to the selected song, then selects the row"""
        debug("jump_to_selected_song")
        # get the proxy model index
        proxy_index = self.proxymodel.mapFromSource(self.selected_song_qmodel_index)
        self.scrollTo(proxy_index)
        self.selectRow(proxy_index.row())

    def jump_to_current_song(self):
        """Moves screen to the currently playing song, then selects the row"""
        # get the proxy model index
        try:
            proxy_index = self.proxymodel.mapFromSource(self.current_song_qmodel_index)
            self.scrollTo(proxy_index)
            self.selectRow(proxy_index.row())
        except Exception as e:
            debug(f'MusicTable.py | jump_to_current_song() | {self.current_song_filepath}')
            debug(f'MusicTable.py | jump_to_current_song() | {self.current_song_qmodel_index}')
            debug(f'MusicTable.py | jump_to_current_song() | Could not find current song in current table buffer - {e}')

    def open_directory(self):
        """Opens the containing directory of the currently selected song, in the system file manager"""
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

    def view_id3_tags_debug_menu(self):
        """Shows ID3 tags for a specific .mp3 file"""
        if self.get_selected_song_filepath() is not None:
            window = DebugWindow(dict(self.get_selected_song_metadata()))
            window.exec_()

    def show_lyrics_menu(self):
        """Shows the lyrics for the currently selected song"""
        selected_song_filepath = self.get_selected_song_filepath()
        if selected_song_filepath is None:
            return
        dic = id3_remap(get_tags(selected_song_filepath)[0])
        lyrics = str(dic["lyrics"])
        if not lyrics:
            lyrics = ""
        lyrics_window = LyricsWindow(selected_song_filepath, lyrics)
        lyrics_window.exec_()

    def setup_keyboard_shortcuts(self):
        """Setup shortcuts here"""
        shortcut = QShortcut(QKeySequence("Ctrl+Shift+R"), self)
        shortcut.activated.connect(self.confirm_reorganize_files)
        # Delete key?
        shortcut = QShortcut(QKeySequence("Del"), self)
        shortcut.activated.connect(self.delete_songs)
        # Search box
        shortcut = QShortcut(QKeySequence("Ctrl+F"), self)
        shortcut.activated.connect(self.emit_search_box)

    def emit_search_box(self):
        self.searchBoxSignal.emit()

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
            self.qapp.threadpool.start(worker) # type: ignore

    def reorganize_files(self, filepaths, progress_callback=None):
        """
        Reorganizes files into Artist/Album/Song,
        based on self.config['settings'][reorganize_destination']
        """
        debug("reorganizing files")
        # FIXME: batch update, instead of doing 1 file at a time
        # DBAccess is being instantiated for every file, boo
        # NOTE:
        # is that even possible with move file function?
        # FIXME: change reorganize location in config, try to reorganize, failed - old reference

        # Get target directory
        target_dir = str(self.config["settings"]["reorganize_destination"])
        for filepath in filepaths:
            # Read file metadata
            artist, album = get_reorganize_vars(filepath)
            # Determine the new path that needs to be made
            new_path = os.path.join(target_dir, artist, album, os.path.basename(filepath))
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
            self.set_current_song_qmodel_index()
            self.set_current_song_filepath()
        self.playPauseSignal.emit()

    def load_music_table(self, *playlist_id):
        """
        Loads data into self (QTableView)
        Loads all songs in library, by default
        Loads songs from a playlist, if `playlist_id` is given

        hint: You get a `playlist_id` from the signal emitted from PlaylistsPane as a tuple (1,)
        """
        if playlist_id:
            if self.selected_playlist_id == playlist_id[0]:
                # Don't reload if we clicked the same item
                return
        self.model2.clear()
        self.model2.setHorizontalHeaderLabels(self.headers.db_list)
        fields = ", ".join(self.headers.db_list)
        search_clause = (
            "title LIKE ? OR artist LIKE ? OR album LIKE ?"
            if self.search_string
            else ""
        )
        params = ""
        is_playlist = 0
        if len(playlist_id) > 0:
            if playlist_id[0] == 0:
                self.selected_playlist_id = 0
                is_playlist = 0
            else:
                self.selected_playlist_id = playlist_id[0]
                is_playlist = 1
        else:
            self.selected_playlist_id = 0
            is_playlist = 0

        # try:
        #     # Check cache for already loaded QTableView QStandardItemModel
        #     data = self.data_cache[self.selected_playlist_id]
        #     self.populate_model(data)
        #     debug('loaded table from cache')
        # except KeyError:
        #     # Query for a playlist
        if is_playlist:
            try:
                with DBA.DBAccess() as db:
                    query = f"SELECT id, {
                        fields} FROM song JOIN song_playlist sp ON id = sp.song_id WHERE sp.playlist_id = ?"
                    # fulltext search
                    if self.search_string:
                        # params = 3 * [self.search_string]
                        params = ["%" + self.search_string + "%"] * 3
                        if query.find("WHERE") == -1:
                            query = f"{query} WHERE {search_clause};"
                        else:
                            query = f"{query} AND {search_clause};"
                        data = db.query(
                            query, (self.selected_playlist_id, params))
                    else:
                        data = db.query(query, (self.selected_playlist_id,))

            except Exception as e:
                error(f"load_music_table() | Unhandled exception 1: {e}")
                return
        # Query for the entire library
        else:
            try:
                with DBA.DBAccess() as db:
                    query = f"SELECT id, {fields} FROM song"
                    # fulltext search
                    if self.search_string:
                        params = ["%" + self.search_string + "%"] * 3
                        if query.find("WHERE") == -1:
                            query = f"{query} WHERE {search_clause};"
                        else:
                            query = f"{query} AND {search_clause};"
                    data = db.query(
                        query,
                        (params),
                    )
            except Exception as e:
                error(f"load_music_table() | Unhandled exception 2: {e}")
                return
        # cache the data
        # self.data_cache[self.selected_playlist_id] = data
        self.populate_model(data)
        self.sort_table_by_multiple_columns()
        self.current_playlist_id = self.selected_playlist_id
        self.model2.layoutChanged.emit()  # emits a signal that the view should be updated
        db_name: str = self.config.get("settings", "db").split("/").pop()
        db_filename = self.config.get("settings", "db")
        self.playlistStatsSignal.emit(f"Songs: {self.model2.rowCount()} | {db_name} | {db_filename}")
        self.loadMusicTableSignal.emit()
        self.find_current_and_selected_bits()
        self.jump_to_current_song()

    def find_current_and_selected_bits(self):
        """
        When data changes in the model view, its nice to re-grab the current song index information
        might as well get the selected song too i guess? though nothing should be selected when reloading the table data
        """
        search_col_num = self.headers.db_list.index("filepath")
        selected_qmodel_index = self.find_qmodel_index_by_value(self.proxymodel, search_col_num, self.selected_song_filepath)
        current_qmodel_index = self.find_qmodel_index_by_value(self.proxymodel, search_col_num, self.current_song_filepath)
        # Update the 2 proxy QModelIndexes that we track
        self.set_selected_song_qmodel_index(selected_qmodel_index)
        self.set_current_song_qmodel_index(current_qmodel_index)

    def populate_model(self, data):
        """
        populate the model2 with data... or whatever
        """
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
            # store database id in the row object using setData
            # - useful for fast db fetching and other model operations
            for item in items:
                item.setData(id, Qt.ItemDataRole.UserRole)
            self.model2.appendRow(items)
        self.proxymodel.setSourceModel(self.model2)
        self.setModel(self.proxymodel)

    def sort_table_by_multiple_columns(self):
        """
        Sorts the data in QTableView (self) by multiple columns
        as defined in config.ini
        """
        self.horizontal_header.sortIndicatorChanged.disconnect()
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
        self.on_sort()
        self.model2.layoutChanged.emit()

    def save_sort_config(self, fields: list[tuple[str, Qt.SortOrder]]):
        """
        Save sort config to ini file.
        fields: List of tuples like [('artist', Qt.AscendingOrder), ('album', Qt.DescendingOrder)]
        """
        raw = ",".join(f"{field}:{1 if order == Qt.SortOrder.AscendingOrder else 2}" for field, order in fields)
        self.config["table"]["sort_order"] = raw
        with open(self.config_path, "w") as f:
            self.config.write(f)

    def get_sort_config(self) -> list[tuple[int, Qt.SortOrder]]:
        """
        Returns a list of (column_index, Qt.SortOrder) tuples based on config and headers
        """
        sort_config = []
        raw_sort = self.config["table"].get("sort_order", "")
        if not raw_sort:
            return []

        try:
            sort_fields = [x.strip() for x in raw_sort.split(",")]
            for entry in sort_fields:
                if ":" not in entry:
                    continue
                db_field, order_str = entry.split(":")
                db_field = db_field.strip()
                order = Qt.SortOrder.AscendingOrder if order_str.strip() == "1" else Qt.SortOrder.DescendingOrder

                # Get the index of the column using your headers class
                if db_field in self.headers.db:
                    col_index = self.headers.db_list.index(db_field)
                    sort_config.append((col_index, order))
        except Exception as e:
            error(f"Failed to parse sort config: {e}")
        return sort_config

    def sort_by_logical_fields(self):
        """
        Sorts the table using logical field names defined in config.
        """
        self.horizontal_header.sortIndicatorChanged.disconnect()  # Prevent feedback loop

        sort_config = self.get_sort_config()

        # Sort in reverse order (primary sort last)
        for col_index, order in reversed(sort_config):
            self.sortByColumn(col_index, order)

        self.model2.layoutChanged.emit()
        self.on_sort()

    def get_audio_files_recursively(self, directories: list[str], progress_callback=None) -> list[str]:
        """Scans a directories for files"""
        extensions = self.config.get("settings", "extensions").split(",")
        audio_files: list[str] = []
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
        (because things could be sorted differently)
        """
        selected_rows = self.get_selected_rows()
        filepaths = []
        for row in selected_rows:
            idx = self.proxymodel.index(row, self.headers.db_list.index("filepath"))
            filepaths.append(idx.data())
        return filepaths

    def get_selected_song_filepath(self) -> str:
        """Returns the selected songs filepath"""
        return self.selected_song_filepath

    def get_selected_songs_db_ids(self) -> list:
        """Returns a list of id's for the selected songs"""
        indexes = self.selectedIndexes()
        if not indexes:
            return []
        selected_rows = set(index.row() for index in indexes)
        id_list = [
            self.proxymodel.data(self.proxymodel.index(row, 0), Qt.ItemDataRole.UserRole) for row in selected_rows
        ]
        return id_list

    def get_current_song_filepath(self) -> str:
        """Returns the currently playing song filepath"""
        return self.current_song_filepath

    def get_current_song_metadata(self) -> dict:
        """Returns the currently playing song's ID3 tags"""
        return id3_remap(get_tags(self.current_song_filepath)[0])

    def get_selected_song_metadata(self) -> dict:
        """Returns the selected song's ID3 tags"""
        return id3_remap(get_tags(self.selected_song_filepath)[0])

    def set_selected_song_filepath(self) -> None:
        """Sets the filepath of the currently selected song"""
        try:
            user_index = self.headers.db_list.index("filepath")
            filepath = self.currentIndex().siblingAtColumn(user_index).data()
        except ValueError:
            # if the user doesnt have filepath selected as a header, retrieve the file from db
            row = self.currentIndex().row()
            id = self.proxymodel.data(self.proxymodel.index(row, 0), Qt.ItemDataRole.UserRole)
            with DBA.DBAccess() as db:
                filepath = db.query("SELECT filepath FROM song WHERE id = ?", (id,))[0][0]
        self.selected_song_filepath = filepath

    def set_current_song_filepath(self, filepath=None) -> None:
        """
        - Sets the current song filepath to the value in column 'path'
        from the current selected row index
        """
        # update the filepath
        if not filepath:
            path = self.current_song_qmodel_index.siblingAtColumn(
                self.headers.db_list.index("filepath")
            ).data()
            self.current_song_filepath: str = path
        else:
            self.current_song_filepath = filepath

    def set_current_song_qmodel_index(self, index: QModelIndex | None = None):
        """
        Takes in the proxy model index for current song - QModelIndex
        converts to model2 index
        stores it
        """
        if index is None:
            index = self.currentIndex()
        # map proxy (sortable) model to the original model (used for interactions)
        real_index: QModelIndex = self.proxymodel.mapToSource(index)
        self.current_song_qmodel_index = real_index

    def set_selected_song_qmodel_index(self, index: QModelIndex | None = None):
        """
        Takes in the proxy model index for current song - QModelIndex
        converts to model2 index
        stores it
        """
        if index is None:
            index = self.currentIndex()
        # map proxy (sortable) model to the original model (used for interactions)
        real_index: QModelIndex = self.proxymodel.mapToSource(index)
        self.selected_song_qmodel_index = real_index

    def set_search_string(self, text: str):
        """set the search string"""
        self.search_string = text

    def load_qapp(self, qapp: QApplication) -> None:
        """Necessary for using members and methods of main application window"""
        self.qapp: QApplication = qapp

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
            _ = self.model2.dataChanged.connect(self.on_cell_data_changed)
        except Exception:
            pass

    def disconnect_layout_changed(self):
        """Disconnects the layoutChanged signal from QTableView.model"""
        try:
            self.model2.layoutChanged.disconnect()
        except Exception:
            pass

    # def connect_layout_changed(self):
    #     """Connects the layoutChanged signal from QTableView.model"""
    #     try:
    #         pass
    #         _ = self.model2.layoutChanged.connect(self.restore_scroll_position)
    #     except Exception:
    #         pass


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
