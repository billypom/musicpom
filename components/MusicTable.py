import DBA
from PyQt5.QtGui import QStandardItem, QStandardItemModel
from PyQt5.QtWidgets import QTableView
from PyQt5.QtCore import QTimer, Qt, pyqtSignal
from tinytag import TinyTag
from utils import add_files_to_library
from utils import get_id3_tags
from utils import get_album_art
import logging


class MusicTable(QTableView):
    playPauseSignal = pyqtSignal()
    enterKey = pyqtSignal()
    def __init__(self, parent=None, qapp=None):
        QTableView.__init__(self, parent)
        self.headers = ['title', 'artist', 'album', 'genre', 'codec', 'year', 'path']
        self.songChanged = None
        self.selected_song_filepath = None
        self.current_song_filepath = None
        self.qapp = None
        # self.tableView.resizeColumnsToContents()
        self.clicked.connect(self.set_selected_song_filepath)
        self.doubleClicked.connect(self.set_current_song_filepath) # listens for emitted signal, runs set_current_song_filepath
        self.enterKey.connect(self.set_current_song_filepath)
        self.fetch_library()

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
            self.enterKey.emit() # Enter key detected
        else: # Default behavior
            super().keyPressEvent(event)

    def mousePressEvent(self, event):
        """Press mouse button. Do thing"""
        self.last = "Click"
        QTableView.mousePressEvent(self, event) # Keep original functionality
    
    def mouseReleaseEvent(self, event):
        """Release mouse button. Do thing"""
        if self.last == "Click":
            QTimer.singleShot(self.qapp.instance().doubleClickInterval(),
                              self.performSingleClickAction)
        else:
            # Perform double click action.
            self.set_current_song_filepath
            self.message = "Double Click"
            self.update()
        QTableView.mouseReleaseEvent(self, event) # Keep original functionality
    
    def mouseDoubleClickEvent(self, event):
        self.last = "Double Click"
        self.doubleClicked.emit(self.selectionModel().currentIndex()) # emits the current index of the double clicked song
        QTableView.mouseDoubleClickEvent(self, event) # Keep original functionality
    
    def performSingleClickAction(self):
        if self.last == "Click":
            self.message = "Click"
            self.update()

    def toggle_play_pause(self):
        """Toggles the currently playing song by emitting a signal"""
        if not self.current_song_filepath:
            self.set_current_song_filepath()
        self.playPauseSignal.emit()

    def choose_new_song(self):
        """Starts the playback of a new song by emitting a signal"""
        
        
    def get_selected_rows(self):
        """Returns a list of indexes for every selected row"""
        rows = []
        for idx in self.selectionModel().siblingAtColumn():
            rows.append(idx.row())
        return rows
    
    def set_selected_song_filepath(self):
        """Sets the filepath of the currently selected song"""
        self.selected_song_filepath = self.currentIndex().siblingAtColumn(self.headers.index('path')).data()
        print(f'Selected song: {self.selected_song_filepath}')
    
    def set_current_song_filepath(self):
        """Sets the filepath of the currently playing/chosen song"""
        # Setting the current song filepath automatically plays that song
        # self.tableView listens to this function and plays the audio file located at self.current_song_filepath
        self.current_song_filepath = self.currentIndex().siblingAtColumn(self.headers.index('path')).data()
        print(f'Current song: {self.current_song_filepath}')
        
    def get_selected_song_filepath(self):
        """Returns the selected song filepath"""
        return self.selected_song_filepath
    
    def get_selected_song_metadata(self):
        """Returns the current/chosen song's ID3 tags"""
        return get_id3_tags(self.selected_song_filepath)
    
    def get_current_song_filepath(self):
        """Returns the current/chosen song filepath"""
        return self.current_song_filepath

    def get_current_song_metadata(self):
        """Returns the current/chosen song's ID3 tags"""
        return get_id3_tags(self.current_song_filepath)
    
    def get_current_song_album_art(self):
        """Returns the APIC data for the currently playing song"""
        return get_album_art(self.current_song_filepath)
        
    
    def fetch_library(self):
        """Initialize the tableview model"""
        self.model = QStandardItemModel()
        self.model.setHorizontalHeaderLabels(self.headers)
        # Fetch library data
        with DBA.DBAccess() as db:
            data = db.query('SELECT title, artist, album, genre, codec, album_date, filepath FROM library;', ())
        # Populate the model
        for row_data in data:
            items = [QStandardItem(str(item)) for item in row_data]
            self.model.appendRow(items)
        # Set the model to the tableView (we are the tableview)
        self.setModel(self.model)
        # self.update()
        self.viewport().update()
    
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
        self.qapp = qapp


        
