from mutagen.easyid3 import EasyID3
import DBA
from PyQt5.QtGui import QStandardItem, QStandardItemModel, QKeySequence
from PyQt5.QtWidgets import QTableView, QShortcut, QMessageBox, QAbstractItemView
from PyQt5.QtCore import QModelIndex, Qt, pyqtSignal, QTimer
from utils import add_files_to_library
from utils import get_id3_tags
from utils import get_album_art
from utils import set_id3_tag
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
        self.model = QStandardItemModel(self) # Necessary for actions related to cell values
        self.setModel(self.model) # Same as above
        self.config = configparser.ConfigParser()
        self.config.read('config.ini')
        self.table_headers = ['title', 'artist', 'album', 'genre', 'codec', 'year', 'path'] # gui names of headers
        self.id3_headers = ['title', 'artist', 'album', 'content_type', ]
        self.database_columns = str(self.config['table']['columns']).split(',') # db names of headers
        self.vertical_scroll_position = 0
        self.songChanged = None
        self.selected_song_filepath = None
        self.current_song_filepath = None
        # self.tableView.resizeColumnsToContents()
        self.clicked.connect(self.set_selected_song_filepath)
        # doubleClicked is a built in event for QTableView - we listen for this event and run set_current_song_filepath
        self.doubleClicked.connect(self.set_current_song_filepath)
        self.enterKey.connect(self.set_current_song_filepath)
        self.fetch_library()
        self.setup_keyboard_shortcuts()
        self.model.dataChanged.connect(self.on_cell_data_changed) # editing cells
        self.model.layoutChanged.connect(self.restore_scroll_position)


    def setup_keyboard_shortcuts(self):
        """Setup shortcuts here"""
        shortcut = QShortcut(QKeySequence("Ctrl+Shift+R"), self)
        shortcut.activated.connect(self.reorganize_selected_files)


    def on_cell_data_changed(self, topLeft: QModelIndex, bottomRight: QModelIndex):
        """Handles updating ID3 tags when data changes in a cell"""
        print('on_cell_data_changed')
        filepath_column_idx = self.model.columnCount() - 1 # always the last column
        filepath_index = self.model.index(topLeft.row(), filepath_column_idx) # exact index of the edited cell
        filepath = self.model.data(filepath_index) # filepath
        # update the ID3 information
        user_input_data = topLeft.data()
        edited_column_name = self.database_columns[topLeft.column()]
        response = set_id3_tag(filepath, edited_column_name, user_input_data)
        if response:
            update_song_in_library(filepath, edited_column_name, user_input_data)


    def reorganize_selected_files(self):
        """Ctrl+Shift+R = Reorganize"""
        filepaths = self.get_selected_songs_filepaths()
        print(f'yay: {filepaths}')
        # Confirmation screen (yes, no)
        reply = QMessageBox.question(self, 'Confirmation', 'Are you sure you want to reorganize these files?', QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
        if reply:
            # Get target directory
            target_dir = str(self.config['directories']['reorganize_destination'])
            for filepath in filepaths:
                try:
                    # Read file metadata
                    audio = EasyID3(filepath)
                    artist = audio.get('artist', ['Unknown Artist'])[0]
                    album = audio.get('album', ['Unknown Album'])[0]
                    # Determine the new path that needs to be made
                    new_path = os.path.join(target_dir, artist, album, os.path.basename(filepath))
                    # Create the directories if they dont exist
                    os.makedirs(os.path.dirname(new_path), exist_ok=True)
                    # Move the file to the new directory
                    shutil.move(filepath, new_path)
                    # Update the db?
                    with DBA.DBAccess() as db:
                        db.query('UPDATE library SET filepath = ? WHERE filepath = ?', (new_path, filepath))
                    print(f'Moved: {filepath} -> {new_path}')
                except Exception as e:
                    print(f'Error moving file: {filepath} | {e}')

            self.fetch_library()
            QMessageBox.information(self, 'Reorganization complete', 'Files successfully reorganized')
            # add new files to library


    def keyPressEvent(self, event):
        """Press a key. Do a thing"""
        key = event.key()
        if key == Qt.Key_Space: # Spacebar to play/pause
            self.toggle_play_pause()
        elif key == Qt.Key_Up: # Arrow key navigation
            current_index = self.currentIndex()
            new_index = self.model.index(current_index.row() - 1, current_index.column())
            if new_index.isValid():
                self.setCurrentIndex(new_index)
        elif key == Qt.Key_Down: # Arrow key navigation
            current_index = self.currentIndex()
            new_index = self.model.index(current_index.row() + 1, current_index.column())
            if new_index.isValid():
                self.setCurrentIndex(new_index)
        elif key in (Qt.Key_Return, Qt.Key_Enter):
            if self.state() != QAbstractItemView.EditingState:
                self.enterKey.emit() # Enter key detected
            else:
                super().keyPressEvent(event)
        else: # Default behavior
            super().keyPressEvent(event)


    def toggle_play_pause(self):
        """Toggles the currently playing song by emitting a signal"""
        if not self.current_song_filepath:
            self.set_current_song_filepath()
        self.playPauseSignal.emit()


    def set_selected_song_filepath(self):
        """Sets the filepath of the currently selected song"""
        self.selected_song_filepath = self.currentIndex().siblingAtColumn(self.table_headers.index('path')).data()
        print(f'Selected song: {self.selected_song_filepath}')
        # print(get_id3_tags(self.selected_song_filepath))


    def set_current_song_filepath(self):
        """Sets the filepath of the currently playing song"""
        # Setting the current song filepath automatically plays that song
        # self.tableView listens to this function and plays the audio file located at self.current_song_filepath
        self.current_song_filepath = self.currentIndex().siblingAtColumn(self.table_headers.index('path')).data()
        # print(f'Current song: {self.current_song_filepath}')


    def get_selected_rows(self):
        """Returns a list of indexes for every selected row"""
        selection_model = self.selectionModel()
        return [index.row() for index in selection_model.selectedRows()]
        # rows = []
        # for idx in self.selectionModel().siblingAtColumn():
        #     rows.append(idx.row())
        # return rows


    def get_selected_songs_filepaths(self):
        """Returns a list of the filepaths for the currently selected songs"""
        selected_rows = self.get_selected_rows()
        filepaths = []
        for row in selected_rows:
            idx = self.model.index(row, self.table_headers.index('path'))
            filepaths.append(idx.data())
        return filepaths


    def get_selected_song_filepath(self):
        """Returns the selected songs filepath"""
        return self.selected_song_filepath


    def get_selected_song_metadata(self):
        """Returns the selected song's ID3 tags"""
        return get_id3_tags(self.selected_song_filepath)


    def get_current_song_filepath(self):
        """Returns the currently playing song filepath"""
        return self.current_song_filepath


    def get_current_song_metadata(self):
        """Returns the currently playing song's ID3 tags"""
        return get_id3_tags(self.current_song_filepath)


    def get_current_song_album_art(self):
        """Returns the APIC data (album art lol) for the currently playing song"""
        return get_album_art(self.current_song_filepath)


    def fetch_library(self):
        """Initialize the tableview model"""
        self.vertical_scroll_position = self.verticalScrollBar().value() # Get my scroll position before clearing
        self.model.clear()
        self.model.setHorizontalHeaderLabels(self.table_headers)
        # Fetch library data
        with DBA.DBAccess() as db:
            data = db.query('SELECT title, artist, album, genre, codec, album_date, filepath FROM library;', ())
        # Populate the model
        for row_data in data:
            items = [QStandardItem(str(item)) for item in row_data]
            self.model.appendRow(items)
        # Update the viewport/model
        # self.viewport().update()
        self.model.layoutChanged.emit()

    def restore_scroll_position(self):
        """Restores the scroll position"""
        print(f'Returning to {self.vertical_scroll_position}')
        QTimer.singleShot(100, lambda: self.verticalScrollBar().setValue(self.vertical_scroll_position))


    def add_files(self, files):
        """When song(s) added to the library, update the tableview model
        - Drag & Drop song(s) on tableView
        - File > Open > List of song(s)
        """
        print(f'tableView - adding files: {files}')
        number_of_files_added = add_files_to_library(files)
        if number_of_files_added:
            self.fetch_library()


    def load_qapp(self, qapp):
        # why was this necessary again? :thinking:
        self.qapp = qapp


