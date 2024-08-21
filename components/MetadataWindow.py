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
from PyQt5.QtCore import pyqtSignal
from mutagen.id3 import ID3
from components.ErrorDialog import ErrorDialog
from utils.get_id3_tags import get_id3_tags
from utils.set_id3_tag import set_id3_tag
from utils.update_song_in_database import update_song_in_database
from utils.id3_tag_mapping import id3_tag_mapping
# import re


class ID3LineEdit(QLineEdit):
    def __init__(self, text: str, tag: str):
        """ """
        super(ID3LineEdit, self).__init__()
        self.setText(text)
        self._original_text = text
        self.tag = tag

    def has_changed(self) -> bool:
        return self.text() != self._original_text


class MetadataWindow(QDialog):
    def __init__(self, refreshMusicTableSignal, songs: list, ids: list):
        """
        Window that allows batch editing of metadata for multiple files

        Input: songs, ids
        - list of strings, absolute paths to mp3 files
        - list of database song ids

        """
        super(MetadataWindow, self).__init__()
        self.refreshMusicTableSignal = refreshMusicTableSignal
        self.songs = list(zip(songs, ids))
        self.id3_tag_mapping = id3_tag_mapping
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
        for song in self.songs:
            song_data = get_id3_tags(song[0])
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
                print(value)
                # If the ID3 tag is the same for every item we're editing
                field_text = str(value[0]) if value else ""
                # Normal field
                label = QLabel(str(self.id3_tag_mapping[tag]))
                input_field = ID3LineEdit(field_text, tag)
                input_field.setStyleSheet(None)
            else:
                print(value)
                # Danger field
                # this means the metadata differs between the selected items for this tag
                # so be careful...dangerous
                field_text = str(value[0]) if value else ""
                label = QLabel(str(self.id3_tag_mapping[tag]))
                input_field = ID3LineEdit(field_text, tag)
                input_field.setStyleSheet("border: 1px solid red")
            # Save each input field to our dict for saving
            self.input_fields[tag] = input_field
            current_layout.addWidget(label)
            current_layout.addWidget(input_field)
        layout.addLayout(current_layout)

        # Save button
        save_button = QPushButton("Save")
        save_button.clicked.connect(self.save)
        layout.addWidget(save_button)
        self.setLayout(layout)

    def save(self):
        """Save changes made to metadata for each song in dict"""
        for song in self.songs:
            for tag, field in self.input_fields.items():
                if field.text() is not None and field.text() != "":
                    if field.has_changed():
                        # date crap...
                        # if tag == "TYER":
                        #     continue
                        # if tag == "TDAT":
                        #     match = re.match(
                        #         r"(\d{4})[-/](\d{2})[-/](\d{2})", field.text()
                        #     )
                        #     if not match:
                        #         continue
                        #     year, _, _ = match.groups()
                        #     _ = set_id3_tag(
                        #         filepath=song[0], tag_name="TYER", value=str(year)
                        #     )
                        # BUSINESS AS USUAL
                        # Update the ID3 tag if the tag is not blank,
                        #   and has been edited
                        success = set_id3_tag(
                            filepath=song[0], tag_name=tag, value=field.text()
                        )
                        if success:
                            update_song_in_database(
                                song[1],
                                edited_column_name=self.id3_tag_mapping[tag],
                                user_input_data=field.text(),
                            )
                        else:
                            error_dialog = ErrorDialog(
                                f"Could not update metadata for {song}. Exiting early"
                            )
                            error_dialog.exec()
                            self.close()
        self.refreshMusicTableSignal.emit()
        self.close()
