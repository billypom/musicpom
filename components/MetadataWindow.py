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


class MetadataWindow(QDialog):
    def __init__(self, songs: ID3 | dict):
        super(MetadataWindow, self).__init__()
        self.setWindowTitle("Edit metadata")
        self.setMinimumSize(400, 400)
        layout = QVBoxLayout()

        label = QLabel("Edit metadata")
        label.setFont(QFont("Sans", weight=QFont.Bold))
        layout.addWidget(label)

        # Labels and categories and stuff
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        layout.addWidget(separator)
        category_label = QLabel("Edit metadata")
        category_label.setFont(QFont("Sans", weight=QFont.Bold))  # bold category
        category_label.setStyleSheet("text-transform:uppercase;")  # uppercase category

        # Editable fields
        label = QLabel("Title")
        input_field = QLineEdit({songs["TPE1"]})
        layout.addWidget(label)
        layout.addWidget(input_field)

        # Save button
        save_button = QPushButton("Save")
        save_button.clicked.connect(self.save)
        layout.addWidget(save_button)
        self.setLayout(layout)

    def save(self):
        """Save changes made to metadata for each song in dict"""
        pass
        self.close()
