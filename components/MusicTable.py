import DBA
from PyQt5.QtGui import QStandardItem, QStandardItemModel
from PyQt5.QtWidgets import QTableView
from PyQt5.QtCore import QTimer
from tinytag import TinyTag
from utils import add_files_to_library
import logging


class MusicTable(QTableView):
    def __init__(self, parent=None, qapp=None):
        QTableView.__init__(self, parent)
        self.headers = ['title', 'artist', 'album', 'genre', 'codec', 'year', 'path']
        self.songChanged = None
        self.selected_song_filepath = None
        self.current_song_filepath = None
        self.qapp = None
        # self.tableView.resizeColumnsToContents()
        self.clicked.connect(self.set_selected_song_filepath) # These are faster than the click/double determination
        self.doubleClicked.connect(self.set_current_song_filepath) # These are faster than the click/double determination
        self.fetch_library()
        
    def mousePressEvent(self, event):
        self.last = "Click"
        QTableView.mousePressEvent(self, event) # Keep original functionality
    
    def mouseReleaseEvent(self, event):
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
        self.doubleClicked.emit(self.selectionModel().currentIndex())
        QTableView.mouseDoubleClickEvent(self, event) # Keep original functionality
    
    def performSingleClickAction(self):
        if self.last == "Click":
            self.message = "Click"
            self.update()
        
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
        self.current_song_filepath = self.currentIndex().siblingAtColumn(self.headers.index('path')).data()
        print(f'Current song: {self.current_song_filepath}')
        
    def get_selected_song_filepath(self):
        """Returns the selected song filepath"""
        return self.selected_song_filepath
    
    def get_selected_song_metadata(self):
        """Returns the current/chosen song's ID3 tags"""
        return TinyTag.get(self.selected_song_filepath)
    
    def get_current_song_filepath(self):
        """Returns the current/chosen song filepath"""
        return self.current_song_filepath

    def get_current_song_metadata(self):
        """Returns the current/chosen song's ID3 tags"""
        return TinyTag.get(self.current_song_filepath)
        
    
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
        self.update()
    
    def add_files(self, files):
        """When song(s) added to the library, update the tableview model
        - Drag & Drop song(s) on tableView
        - File > Open > List of song(s)
        """
        print(f'tableView - adding files: {files}')
        response = add_files_to_library(files)
        if response:
            self.fetch_library()
        else:
            logging.warning('MusicTable.add_files | failed to add files to library')
        
        
    def load_qapp(self, qapp):
        self.qapp = qapp


        