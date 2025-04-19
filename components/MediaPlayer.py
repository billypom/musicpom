from PyQt5.QtCore import QObject, QUrl, pyqtSignal
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent, QMediaPlaylist
from PyQt5.QtWidgets import QApplication
import sys

class MediaPlayer(QMediaPlayer):
    playlistNextSignal = pyqtSignal()
    def __init__(self):
        super().__init__()

        # Connect mediaStatusChanged signal to our custom function
        self.mediaStatusChanged.connect(self.on_media_status_changed)

    def play(self):
        super().play()

    def on_media_status_changed(self, status):
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            print("Song ended, triggering custom function!")
            self.on_song_ended()

    def on_song_ended(self):
        self.playlistNextSignal.emit()
        print("Custom function executed after song ended!")

