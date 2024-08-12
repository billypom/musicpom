from PyQt5.QtWidgets import (
    QDialog,
    QFrame,
    QVBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
)
from PyQt5.QtGui import QFont
from mutagen.id3 import ID3
from utils.get_id3_tags import get_id3_tags


class MetadataWindow(QDialog):
    def __init__(self, songs: list):
        """
        Takes in a list of songs (absolute paths)
        """
        super(MetadataWindow, self).__init__()
        self.id3_tag_mapping = {
            "TIT2": "title",
            "TPE1": "artist",
            "TALB": "album",
            "TPE2": "album_artist",
            "TCON": "genre",
            "TRCK": "track_number",
            "APIC": "album_cover",
            "TCOP": "copyright",
        }
        self.setWindowTitle("Edit metadata")
        self.setMinimumSize(600, 800)
        layout = QVBoxLayout()
        h_separator = QFrame()
        h_separator.setFrameShape(QFrame.HLine)

        # Labels and categories and stuff
        # category_label = QLabel("Edit metadata")
        # category_label.setFont(QFont("Sans", weight=QFont.Bold))  # bold category
        # category_label.setStyleSheet("text-transform:uppercase;")  # uppercase category
        layout.addWidget(h_separator)

        # FIXME: dynamically load fields and stuf
        # Dict of sets
        # {
        #   "TIT2": ["song_title1", "song_title2"],
        #   ...
        # }
        tag_sets: dict = {}
        # List of dictionaries of ID3 tags for each song
        # songs_id3_data: list = []
        for song in songs:
            # songs_id3_data.append(get_id3_tags(song))
            song_data = get_id3_tags(song)
            for tag in self.id3_tag_mapping:
                try:
                    tag_sets[tag] = song_data[tag]
                except KeyError:
                    tag_sets[tag] = ""

        for tag, value in tag_sets.items():
            if value == set(value):
                # Normal field
                label = QLabel(str(self.id3_tag_mapping[tag]))
                input_field = QLineEdit(str(value))
            else:
                # Danger field
                label = QLabel(str(self.id3_tag_mapping[tag]))
                input_field = QLineEdit(str(value))
            layout.addWidget(label)
            layout.addWidget(input_field)

        # Editable fields
        # label = QLabel("Title")
        # input_field = QLineEdit({songs["TPE1"]})
        # layout.addWidget(label)
        # layout.addWidget(input_field)

        # Save button
        save_button = QPushButton("Save")
        save_button.clicked.connect(self.save)
        layout.addWidget(save_button)
        self.setLayout(layout)

    def save(self):
        """Save changes made to metadata for each song in dict"""
        pass
        self.close()
