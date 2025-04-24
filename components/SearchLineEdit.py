from PyQt5.QtWidgets import QLineEdit

"""
MusicTable.py holds a variable called self.search_string
MusicTable.py had a function called load_music_table(), which loads data 
    from the SQLite database to the QTableView. load_music_table()
    checks for the self.search_string

in main.py, on self.lineEditSearch.textChanged(),
this updates the self.search_string in MusicTable.py

in MusicTable.py, when Ctrl+F is pressed, the line edit gets hidden or visible
"""


class SearchLineEdit(QLineEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setVisible(False)

    def toggle_visibility(self):
        if self.isHidden():
            self.setHidden(False)
        else:
            self.setHidden(True)
            self.setText(None)

    # def toggle_visibility(self):
    # if self.is_hidden:
    #     self.button.setVisible(True)
    #     self.is_hidden = False
    # else:
    #     self.button.setVisible(False)
    #     self.is_hidden = True
