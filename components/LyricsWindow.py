from PyQt5.QtWidgets import (
    QDialog,
    QPlainTextEdit,
    QVBoxLayout,
    QLabel,
    QPushButton,
)
from PyQt5.QtGui import QFont
from components.ErrorDialog import ErrorDialog
from utils import set_id3_tag
from logging import debug


class LyricsWindow(QDialog):
    def __init__(self, song_filepath: str, lyrics: str):
        super(LyricsWindow, self).__init__()
        self.setWindowTitle("Lyrics")
        self.setMinimumSize(400, 400)
        self.lyrics: str = lyrics
        self.song_filepath: str = song_filepath
        layout = QVBoxLayout()

        # Labels & input fields
        self.input_field = QPlainTextEdit(self.lyrics)
        layout.addWidget(self.input_field)

        # Save button
        save_button = QPushButton("Save")
        save_button.clicked.connect(self.save)
        layout.addWidget(save_button)
        self.setLayout(layout)

    def save(self):
        """Saves the current lyrics text to the USLT/lyrics ID3 tag"""
        success = set_id3_tag(
            filepath=self.song_filepath,
            tag_name="lyrics",
            value=self.input_field.toPlainText(),
        )
        if success:
            debug("lyrical success! yay")
        else:
            error_dialog = ErrorDialog("Could not save lyrics :( sad")
            error_dialog.exec()
        self.close()
