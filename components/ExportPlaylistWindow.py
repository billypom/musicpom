import logging
from PyQt5.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLineEdit,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QListWidget,
    QListWidgetItem,
)
from PyQt5.QtGui import QFont
import DBA


class ExportPlaylistWindow(QDialog):
    def __init__(self):
        super(ExportPlaylistWindow, self).__init__()
        self.setWindowTitle("Export playlist")
        layout = QVBoxLayout()
        # button_layout = QHBoxLayout()

        playlist_dict = {}
        with DBA.DBAccess() as db:
            data = db.query("SELECT id, name from playlist;", ())
        for row in data:
            playlist_dict[row[0]] = row[1]

        self.item_dict = {}
        self.listWidget = QListWidget(self)
        for i, (k, v) in enumerate(playlist_dict.items()):
            item_text = f"{i} | {v}"
            item = QListWidgetItem(item_text)
            self.listWidget.addItem(item)
            self.item_dict[item_text] = k

        # add ui elements to window
        label = QLabel("Playlists")
        label.setFont(QFont("Sans", weight=QFont.Bold))
        layout.addWidget(label)
        layout.addWidget(self.listWidget)

        # Save button
        save_button = QPushButton("Export")
        save_button.clicked.connect(self.save)
        layout.addWidget(save_button)
        self.setLayout(layout)
        self.show()

    def save(self) -> None:
        """Exports the chosen database playlist to a .m3u file"""
        value = self.input.text()
        if value == "" or value is None:
            self.close()
            return
        else:
            try:
                with DBA.DBAccess() as db:
                    db.execute("INSERT INTO playlist (name) VALUES (?);", (value,))
            except Exception as e:
                logging.error(
                    f"CreatePlaylistWindow.py save() | Could not create playlist: {e}"
                )
            self.close()

    def cancel(self) -> None:
        self.close()
        return
