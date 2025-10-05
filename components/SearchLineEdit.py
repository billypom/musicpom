from PyQt5.QtCore import QTimer, pyqtSignal
from PyQt5.QtWidgets import QLineEdit

"""
MusicTable.py holds a variable called self.search_string
MusicTable.py had a function called load_music_table(), which loads data 
    from the SQLite database to the QTableView. load_music_table()
    checks for the self.search_string

in main.py, on self.searchLineEdit.textChanged(),
this updates the self.search_string in MusicTable.py

in MusicTable.py, when Ctrl+F is pressed, the line edit gets hidden or visible
"""


class SearchLineEdit(QLineEdit):
    textTypedSignal = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setVisible(False)
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.on_typing_stopped)
        self.textChanged.connect(self.on_text_changed)

    def toggle_visibility(self) -> bool:
        """
        Returns true if visible
        false if hidden

        This is used to bring focus back to the music table after toggling visibility
        """
        if self.isHidden():
            self.setHidden(False)
            return True
        else:
            self.setHidden(True)
            self.setText(None)
            return False

    def on_text_changed(self):
        """Reset a timer each time text is changed"""
        self.timer.start(1500)

    def on_typing_stopped(self):
        """When timer reaches end, emit the text that is currently entered"""
        self.textTypedSignal.emit(self.text())
