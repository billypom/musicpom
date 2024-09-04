import os
import configparser
import sys
import logging
from subprocess import run
import qdarktheme

from pyqtgraph import mkBrush
from mutagen.id3 import ID3
from mutagen.id3._frames import APIC
from configparser import ConfigParser
import DBA
from ui import Ui_MainWindow
from PyQt5.QtWidgets import (
    QFileDialog,
    QMainWindow,
    QApplication,
    QGraphicsScene,
    QHeaderView,
    QGraphicsPixmapItem,
    QMessageBox,
)
from PyQt5.QtCore import QUrl, QTimer, Qt, pyqtSignal
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent, QAudioProbe
from PyQt5.QtGui import QCloseEvent, QPixmap
from utils import scan_for_music, delete_and_create_library_database, initialize_db
from components import (
    PreferencesWindow,
    AudioVisualizer,
    CreatePlaylistWindow,
    ExportPlaylistWindow,
)

# Create ui.py file from Qt Designer
# pyuic5 ui.ui -o ui.py


class ApplicationWindow(QMainWindow, Ui_MainWindow):
    playlistCreatedSignal = pyqtSignal()

    def __init__(self, qapp):
        super(ApplicationWindow, self).__init__()
        global stopped
        stopped = False
        self.setupUi(self)
        self.setWindowTitle("MusicPom")
        self.selected_song_filepath: str | None = None
        self.current_song_filepath: str | None = None
        self.current_song_metadata: ID3 | dict | None = None
        self.current_song_album_art: bytes | None = None
        self.album_art_scene: QGraphicsScene = QGraphicsScene()
        self.config: ConfigParser = configparser.ConfigParser()
        self.player: QMediaPlayer = QMediaPlayer()  # Audio player object
        self.probe: QAudioProbe = QAudioProbe()  # Gets audio data
        self.audio_visualizer: AudioVisualizer = AudioVisualizer(self.player)
        self.current_volume: int = 50
        self.qapp = qapp
        # print(f'ApplicationWindow self.qapp: {self.qapp}')
        self.tableView.load_qapp(self.qapp)
        self.albumGraphicsView.load_qapp(self.qapp)
        self.config.read("config.ini")
        # Initialization
        self.timer = QTimer(self)  # Audio timing things
        self.player.setVolume(self.current_volume)
        # Audio probe for processing audio signal in real time
        self.probe.setSource(self.player)
        self.probe.audioBufferProbed.connect(self.process_probe)

        # Slider Timer (realtime playback feedback horizontal bar)
        self.timer.start(100)
        self.timer.timeout.connect(self.move_slider)

        # Graphics plot
        self.PlotWidget.setXRange(0, 100, padding=0)  # x axis range
        self.PlotWidget.setYRange(0, 1, padding=0)  # y axis range
        self.PlotWidget.getAxis("bottom").setTicks([])  # Remove x-axis ticks
        self.PlotWidget.getAxis("bottom").setLabel("")  # Remove x-axis label
        self.PlotWidget.setLogMode(False, False)
        # Remove y-axis labels and decorations
        self.PlotWidget.getAxis("left").setTicks([])  # Remove y-axis ticks
        self.PlotWidget.getAxis("left").setLabel("")  # Remove y-axis label

        # Playlist left-pane
        # self.playlistTreeView

        # Connections
        self.playbackSlider.sliderReleased.connect(
            lambda: self.player.setPosition(self.playbackSlider.value())
        )  # maybe sliderReleased works better than sliderMoved
        self
        self.volumeSlider.sliderMoved[int].connect(
            lambda: self.volume_changed()
        )  # Move slider to adjust volume
        self.playButton.clicked.connect(self.on_play_clicked)  # Click to play/pause
        self.previousButton.clicked.connect(
            self.on_previous_clicked
        )  # Click to previous song
        self.nextButton.clicked.connect(self.on_next_clicked)  # Click to next song

        # FILE MENU
        self.actionOpenFiles.triggered.connect(self.open_files)  # Open files window
        self.actionNewPlaylist.triggered.connect(self.create_playlist)
        self.actionExportPlaylist.triggered.connect(self.export_playlist)
        # EDIT MENU
        # VIEW MENU
        self.actionPreferences.triggered.connect(
            self.open_preferences
        )  # Open preferences menu
        # QUICK ACTIONS MENU
        self.actionScanLibraries.triggered.connect(self.scan_libraries)
        self.actionDeleteLibrary.triggered.connect(self.clear_database)
        self.actionDeleteDatabase.triggered.connect(self.delete_database)

        ## tableView triggers
        self.tableView.doubleClicked.connect(
            self.play_audio_file
        )  # Listens for the double click event, then plays the song
        self.tableView.enterKey.connect(
            self.play_audio_file
        )  # Listens for the enter key event, then plays the song
        self.tableView.playPauseSignal.connect(
            self.on_play_clicked
        )  # Spacebar toggle play/pause signal

        ## Playlist triggers
        self.playlistTreeView.playlistChoiceSignal.connect(
            self.tableView.load_music_table
        )
        self.playlistTreeView.allSongsSignal.connect(self.tableView.load_music_table)

        # albumGraphicsView
        self.albumGraphicsView.albumArtDropped.connect(
            self.set_album_art_for_selected_songs
        )
        self.albumGraphicsView.albumArtDeleted.connect(
            self.delete_album_art_for_selected_songs
        )
        self.tableView.viewport().installEventFilter(
            self
        )  # for drag & drop functionality
        # set column widths
        table_view_column_widths = str(self.config["table"]["column_widths"]).split(",")
        for i in range(self.tableView.model.columnCount()):
            self.tableView.setColumnWidth(i, int(table_view_column_widths[i]))
            # dont extend last column past table view border
        self.tableView.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tableView.horizontalHeader().setStretchLastSection(False)

    def closeEvent(self, a0: QCloseEvent | None) -> None:
        """Save settings when closing the application"""
        # MusicTable/tableView column widths
        list_of_column_widths = []
        for i in range(self.tableView.model.columnCount()):
            list_of_column_widths.append(str(self.tableView.columnWidth(i)))
        column_widths_as_string = ",".join(list_of_column_widths)
        self.config["table"]["column_widths"] = column_widths_as_string

        # Save the config
        with open("config.ini", "w") as configfile:
            self.config.write(configfile)
        super().closeEvent(a0)

    def play_audio_file(self) -> None:
        """Start playback of tableView.current_song_filepath track & moves playback slider"""
        self.current_song_metadata = (
            self.tableView.get_current_song_metadata()
        )  # get metadata
        self.current_song_album_art = self.tableView.get_current_song_album_art()
        url = QUrl.fromLocalFile(
            self.tableView.get_current_song_filepath()
        )  # read the file
        content = QMediaContent(url)  # load the audio content
        self.player.setMedia(content)  # what content to play
        self.player.play()  # play
        self.move_slider()  # mover

        # assign metadata
        artist = (
            self.current_song_metadata["TPE1"][0]
            if "artist" in self.current_song_metadata
            else None
        )
        album = (
            self.current_song_metadata["TALB"][0]
            if "album" in self.current_song_metadata
            else None
        )
        title = self.current_song_metadata["TIT2"][0]
        # edit labels
        self.artistLabel.setText(artist)
        self.albumLabel.setText(album)
        self.titleLabel.setText(title)
        # set album artwork
        self.load_album_art(self.current_song_album_art)

    def load_album_art(self, album_art_data) -> None:
        """Displays the album art for the currently playing track in the GraphicsView"""
        if self.current_song_album_art:
            # Clear the scene
            try:
                self.album_art_scene.clear()
            except Exception:
                pass
            # Reset the scene
            self.albumGraphicsView.setScene(None)
            # Create pixmap for album art
            pixmap = QPixmap()
            pixmap.loadFromData(album_art_data)
            # Create a QGraphicsPixmapItem for more control over pic
            pixmapItem = QGraphicsPixmapItem(pixmap)
            pixmapItem.setTransformationMode(
                Qt.SmoothTransformation
            )  # For better quality scaling
            # Add pixmap item to the scene
            self.album_art_scene.addItem(pixmapItem)
            # Set the scene
            self.albumGraphicsView.setScene(self.album_art_scene)
            # Adjust the album art scaling
            self.adjustPixmapScaling(pixmapItem)

    def adjustPixmapScaling(self, pixmapItem) -> None:
        """Adjust the scaling of the pixmap item to fit the QGraphicsView, maintaining aspect ratio"""
        viewWidth = self.albumGraphicsView.width()
        viewHeight = self.albumGraphicsView.height()
        pixmapSize = pixmapItem.pixmap().size()
        # Calculate scaling factor while maintaining aspect ratio
        scaleX = viewWidth / pixmapSize.width()
        scaleY = viewHeight / pixmapSize.height()
        scaleFactor = min(scaleX, scaleY)
        # Apply scaling to the pixmap item
        pixmapItem.setScale(scaleFactor)

    def set_album_art_for_selected_songs(self, album_art_path: str) -> None:
        """Sets the ID3 tag APIC (album art) for all selected song filepaths"""
        selected_songs = self.tableView.get_selected_songs_filepaths()
        for song in selected_songs:
            print(f"updating album art for {song}")
            self.update_album_art_for_song(song, album_art_path)

    def update_album_art_for_song(
        self, song_file_path: str, album_art_path: str
    ) -> None:
        """Updates the ID3 tag APIC (album art) for 1 song"""
        # audio = MP3(song_file_path, ID3=ID3)
        audio = ID3(song_file_path)
        # Remove existing APIC Frames (album art)
        audio.delall("APIC")
        # Add the album art
        with open(album_art_path, "rb") as album_art_file:
            if album_art_path.endswith(".jpg") or album_art_path.endswith(".jpeg"):
                audio.add(
                    APIC(
                        encoding=3,  # 3 = utf-8
                        mime="image/jpeg",
                        type=3,  # 3 = cover image
                        desc="Cover",
                        data=album_art_file.read(),
                    )
                )
            elif album_art_path.endswith(".png"):
                audio.add(
                    APIC(
                        encoding=3,  # 3 = utf-8
                        mime="image/png",
                        type=3,  # 3 = cover image
                        desc="Cover",
                        data=album_art_file.read(),
                    )
                )
        audio.save()

    def delete_album_art_for_selected_songs(self) -> None:
        """Handles deleting the ID3 tag APIC (album art) for all selected songs"""
        filepaths = self.tableView.get_selected_songs_filepaths()
        for file in filepaths:
            # delete APIC data
            try:
                audio = ID3(file)
                if "APIC:" in audio:
                    del audio["APIC"]
                    audio.save()
            except Exception as e:
                print(f"Error processing {file}: {e}")

    def update_audio_visualization(self) -> None:
        """Handles upading points on the pyqtgraph visual"""
        self.clear_audio_visualization()
        y = self.audio_visualizer.get_amplitudes()
        x = [i for i in range(len(y))]
        self.PlotWidget.plot(x, y, fillLevel=0, fillBrush=mkBrush("b"))
        self.PlotWidget.show()

    def clear_audio_visualization(self) -> None:
        self.PlotWidget.clear()

    def move_slider(self) -> None:
        """Handles moving the playback slider"""
        if stopped:
            return
        else:
            if self.playbackSlider.isSliderDown():
                # Prevents slider from updating when dragging
                return
            # Update the slider
            if self.player.state() == QMediaPlayer.State.PlayingState:
                self.playbackSlider.setMinimum(0)
                self.playbackSlider.setMaximum(self.player.duration())
                slider_position = self.player.position()
                self.playbackSlider.setValue(slider_position)
                current_minutes, current_seconds = divmod(slider_position / 1000, 60)
                duration_minutes, duration_seconds = divmod(
                    self.player.duration() / 1000, 60
                )
                self.startTimeLabel.setText(
                    f"{int(current_minutes):02d}:{int(current_seconds):02d}"
                )
                self.endTimeLabel.setText(
                    f"{int(duration_minutes):02d}:{int(duration_seconds):02d}"
                )

    def volume_changed(self) -> None:
        """Handles volume changes"""
        try:
            self.current_volume = self.volumeSlider.value()
            self.player.setVolume(self.current_volume)
        except Exception as e:
            print(f"Changing volume error: {e}")

    def on_play_clicked(self) -> None:
        """Updates the Play & Pause buttons when clicked"""
        if self.player.state() == QMediaPlayer.State.PlayingState:
            self.player.pause()
            self.playButton.setText("▶️")
        else:
            if self.player.state() == QMediaPlayer.State.PausedState:
                self.player.play()
                self.playButton.setText("⏸️")
            else:
                self.play_audio_file()
                self.playButton.setText("⏸️")

    def on_previous_clicked(self) -> None:
        """"""
        print("previous")

    def on_next_clicked(self) -> None:
        print("next")

    def open_files(self) -> None:
        """Opens the open files window"""
        open_files_window = QFileDialog(
            self, "Open file(s)", ".", "Audio files (*.mp3)"
        )
        # QFileDialog.FileMode enum { AnyFile, ExistingFile, Directory, ExistingFiles }
        open_files_window.setFileMode(QFileDialog.ExistingFiles)
        open_files_window.exec_()
        filenames = open_files_window.selectedFiles()
        self.tableView.add_files(filenames)

    def create_playlist(self) -> None:
        """Creates a database record for a playlist, given a name"""
        window = CreatePlaylistWindow(self.playlistCreatedSignal)
        window.playlistCreatedSignal.connect(self.add_latest_playlist_to_tree)
        window.exec_()

    def add_latest_playlist_to_tree(self) -> None:
        """Refreshes the playlist tree"""
        self.playlistTreeView.add_latest_playlist_to_tree()

    def import_playlist(self) -> None:
        """
        Imports a .m3u file, given a base path attempts to match playlist files to
        database records that currently exist
        """
        pass

    def export_playlist(self) -> None:
        """
        Export playlist window
        Takes a certain database playlist and turns it into a .m3u file
        """
        export_playlist_window = ExportPlaylistWindow()
        export_playlist_window.exec_()

    def open_preferences(self) -> None:
        """Opens the preferences window"""
        preferences_window = PreferencesWindow(self.config)
        preferences_window.exec_()  # Display the preferences window modally

    def scan_libraries(self) -> None:
        """Scans for new files in the configured library folder
        Refreshes the datagridview"""
        scan_for_music()
        self.tableView.load_music_table()

    def clear_database(self) -> None:
        """Clears all songs from the database"""
        reply = QMessageBox.question(
            self,
            "Confirmation",
            "Clear all songs from database?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes,
        )
        if reply:
            delete_and_create_library_database()
            self.tableView.load_music_table()

    def delete_database(self) -> None:
        """Deletes the entire database"""
        reply = QMessageBox.question(
            self,
            "Confirmation",
            "Delete database?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes,
        )
        if reply:
            initialize_db()
            self.tableView.load_music_table()

    def reinitialize_database(self) -> None:
        """Clears all tables in database and recreates"""
        reply = QMessageBox.question(
            self,
            "Confirmation",
            "Recreate the database?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes,
        )
        if reply:
            initialize_db()
            self.tableView.load_music_table()

    def process_probe(self, buff) -> None:
        buff.startTime()
        self.update_audio_visualization()


if __name__ == "__main__":
    # First run initialization
    if not os.path.exists("config.ini"):
        # Create config file from sample
        run(["cp", "sample_config.ini", "config.ini"])
    config = ConfigParser()
    config.read("config.ini")
    db_name = config.get("db", "database")
    db_path = db_name.split("/")
    db_path.pop()
    db_path_as_string = "/".join(db_path)
    if not os.path.exists(db_path_as_string):
        os.makedirs(db_path_as_string)
        # Create database on first run
        with DBA.DBAccess() as db:
            with open("utils/init.sql", "r") as file:
                lines = file.read()
                for statement in lines.split(";"):
                    print(f"executing [{statement}]")
                    db.execute(statement, ())
    # logging setup
    logging.basicConfig(filename="musicpom.log", encoding="utf-8", level=logging.DEBUG)
    # Allow for dynamic imports of my custom classes and utilities
    project_root = os.path.abspath(os.path.dirname(__file__))
    sys.path.append(project_root)
    # Start the app
    app = QApplication(sys.argv)
    # print(f"main.py app: {app}")
    # Dark theme >:3
    qdarktheme.setup_theme()
    # Show the UI
    ui = ApplicationWindow(app)
    ui.show()
    sys.exit(app.exec_())
