from PyQt5.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
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
        Window that allows batch editing of metadata for multiple files

        Input: songs
        - list of strings, absolute paths to mp3 files
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
        # Keep a dictionary of the input fields for save function
        self.input_fields = {}
        self.setWindowTitle("Edit metadata")
        # self.setMinimumSize(600, 800)
        layout = QVBoxLayout()
        h_separator = QFrame()
        h_separator.setFrameShape(QFrame.HLine)

        # Labels and categories and stuff
        category_label = QLabel("Edit metadata")
        category_label.setFont(QFont("Sans", weight=QFont.Bold))  # bold category
        category_label.setStyleSheet("text-transform:uppercase;")  # uppercase category
        layout.addWidget(category_label)
        layout.addWidget(h_separator)

        tag_sets: dict = {}
        # Get a dict of all tags for all songs
        # e.g.,  { "TIT2": ["song_title1", "song_title2"], ... }
        for song in songs:
            song_data = get_id3_tags(song)
            for tag in self.id3_tag_mapping:
                try:
                    _ = tag_sets[tag]
                except KeyError:
                    # If a tag doesn't exist in our dict, create an empty list
                    tag_sets[tag] = []
                try:
                    tag_sets[tag].append(song_data[tag].text[0])
                except KeyError:
                    pass

        # UI Creation
        current_layout = QHBoxLayout()
        for idx, (tag, value) in enumerate(tag_sets.items()):
            # Layout creation
            if idx == 0:
                pass
            elif idx % 2 == 0:
                # Make a new horizontal layout for every 2 items
                layout.addLayout(current_layout)
                current_layout = QHBoxLayout()

            # print(f"type: {type(value)} | value: {value}")

            # Field Creation
            if value == list(set(value)):
                field_text = str(value[0]) if value else ""
                # Normal field
                label = QLabel(str(self.id3_tag_mapping[tag]))
                input_field = QLineEdit(field_text)
                input_field.setStyleSheet(None)
            else:
                # Danger field
                # this means the metadata differs between the selected items for this tag
                # so be careful...dangerous
                field_text = str(value[0]) if value else ""
                label = QLabel(str(self.id3_tag_mapping[tag]))
                input_field = QLineEdit(field_text)
                input_field.setStyleSheet("border: 1px solid red")
            # Save each input field to our dict for saving
            self.input_fields[tag] = input_field
            current_layout.addWidget(label)
            current_layout.addWidget(input_field)

        # Save button
        save_button = QPushButton("Save")
        save_button.clicked.connect(self.save)
        layout.addWidget(save_button)
        self.setLayout(layout)

    def save(self):
        """Save changes made to metadata for each song in dict"""
        for tag, field in self.input_fields.items():
            print(tag, field)
        self.close()
