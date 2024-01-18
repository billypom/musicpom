import DBA
from PyQt5.QtGui import QStandardItem, QStandardItemModel
from PyQt5.QtWidgets import QTableView


class MusicTable(QTableView):
    def __init__(self):
        super().__init__()
        # Fetch library data
        with DBA.DBAccess() as db: # returns a tuple, 1 row just for metadata purposes
            data = db.query('SELECT title, artist, album, genre, codec, album_date, filepath FROM library;', ())
        headers = ['title', 'artist', 'album', 'genre', 'codec', 'year', 'path']
        # Create a model
        model = QStandardItemModel()
        model.setHorizontalHeaderLabels(headers)
        # Populate the model
        for row_data in data:
            items = [QStandardItem(str(item)) for item in row_data]
            model.appendRow(items)
        # Set the model to the tableView
        self.tableView.setModel(model)
        # self.tableView.resizeColumnsToContents()
        self.music_table.clicked.connect(self.set_clicked_cell_filepath)
        