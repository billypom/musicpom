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
        # self.setMinimumSize(600, 800)
        layout = QVBoxLayout()
        # h_separator = QFrame()
        # h_separator.setFrameShape(QFrame.HLine)

        # Labels and categories and stuff
        # category_label = QLabel("Edit metadata")
        # category_label.setFont(QFont("Sans", weight=QFont.Bold))  # bold category
        # category_label.setStyleSheet("text-transform:uppercase;")  # uppercase category
        # layout.addWidget(category_label)
        # layout.addWidget(h_separator)

        # Editable fields
        tag_sets: dict = {}
        #  { "TIT2": ["song_title1", "song_title2"], ... }
        for song in songs:
            song_data = get_id3_tags(song)
            print("song_data")
            print(song_data)

            for tag in self.id3_tag_mapping:
                # See if the tag exists in the dict
                # else, create it
                try:
                    _ = tag_sets[tag]
                except KeyError:
                    tag_sets[tag] = []
                try:
                    tag_sets[tag].append(song_data[tag].text[0])
                except KeyError:
                    pass

        print(f"tag sets: {tag_sets}")

        current_layout = QHBoxLayout()
        for idx, (tag, value) in enumerate(tag_sets.items()):
            # Layout creation
            if idx == 0:
                pass
            elif idx % 2 == 0:
                # Make a new horizontal layout for every 2 items
                layout.addLayout(current_layout)
                current_layout = QHBoxLayout()

            print(f"type: {type(value)} | value: {value}")

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
                field_text = str(value[0]) if value else ""
                label = QLabel(str(self.id3_tag_mapping[tag]))
                input_field = QLineEdit(field_text)
                input_field.setStyleSheet("border: 1px solid red")
            current_layout.addWidget(label)
            current_layout.addWidget(input_field)

        # Save button
        save_button = QPushButton("Save")
        save_button.clicked.connect(self.save)
        layout.addWidget(save_button)
        self.setLayout(layout)

    def save(self):
        """Save changes made to metadata for each song in dict"""
        self.close()
