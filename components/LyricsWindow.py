from PyQt5.QtWidgets import (
    QDialog,
    QPlainTextEdit,
    QVBoxLayout,
    QLabel,
    QPushButton,
)
from PyQt5.QtGui import QFont
from utils import set_id3_tag


class LyricsWindow(QDialog):
    def __init__(self, song_filepath, lyrics):
        super(LyricsWindow, self).__init__()
        self.setWindowTitle("Lyrics")
        self.lyrics = lyrics
        self.song_filepath = song_filepath
        self.input_field = ""
        layout = QVBoxLayout()
        # label = QLabel("Lyrics")
        # layout.addWidget(label)

        # Labels & input fields
        self.input_fields = {}
        lyrics_label = QLabel("Lyrics")
        lyrics_label.setFont(QFont("Sans", weight=QFont.Bold))  # bold category
        lyrics_label.setStyleSheet("text-transform:uppercase;")  # uppercase category
        layout.addWidget(lyrics_label)
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
            print("success! yay")
        else:
            print("NNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNN")
        self.close()
