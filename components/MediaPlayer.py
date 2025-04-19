from PyQt5.QtCore import QObject, QUrl
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent, QMediaPlaylist
from PyQt5.QtWidgets import QApplication
import sys

class MediaPlayer(QMediaPlayer):
    def __init__(self):
        super().__init__()

        # Connect mediaStatusChanged signal to our custom function
        self.mediaStatusChanged.connect(self.on_media_status_changed)

    # def play(self, file_path):
    #     media_content = QMediaContent(QUrl.fromLocalFile(file_path))
    #     self.player.setMedia(media_content)
    #     self.player.play()

    def on_media_status_changed(self, status):
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            print("Song ended, triggering custom function!")
            self.on_song_ended()

    def on_song_ended(self):
        # Your custom logic when the song ends
        print("Custom function executed after song ended!")

