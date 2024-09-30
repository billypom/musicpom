import os
import sys
import logging
from subprocess import run
import qdarktheme
import typing
from pyqtgraph import mkBrush
from mutagen.id3 import ID3
from mutagen.id3._frames import APIC
from configparser import ConfigParser
import traceback
import DBA
from ui import Ui_MainWindow
from PyQt5.QtWidgets import (
    QFileDialog,
    QLabel,
    QMainWindow,
    QApplication,
    QGraphicsScene,
    QGraphicsPixmapItem,
    QMessageBox,
    QStatusBar,
)
from PyQt5.QtCore import (
    QUrl,
    QTimer,
    Qt,
    pyqtSignal,
    QObject,
    pyqtSlot,
    QThreadPool,
    QRunnable,
)
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent, QAudioProbe
from PyQt5.QtGui import QCloseEvent, QPixmap, QResizeEvent
from utils import (
    scan_for_music,
    delete_and_create_library_database,
    initialize_db,
    add_files_to_library,
)
from components import (
    PreferencesWindow,
    AudioVisualizer,
    CreatePlaylistWindow,
    ExportPlaylistWindow,
)

# Create ui.py file from Qt Designer
# pyuic5 ui.ui -o ui.py


# good help with signals slots in threads
# https://stackoverflow.com/questions/52993677/how-do-i-setup-signals-and-slots-in-pyqt-with-qthreads-in-both-directions

# GOOD
# https://www.pythonguis.com/tutorials/multithreading-pyqt-applications-qthreadpool/


class WorkerSignals(QObject):
    """
    How to use signals for a QRunnable class;
    Unlike most cases where signals are defined as class attributes directly in the class,
    here we define a class that inherits from QObject
    and define the signals as class attributes in that class.
    Then we can instantiate that class and use it as a signal object.
    """

    # 1)
    # Use a naming convention for signals that makes it clear that they are signals
    # and a corresponding naming convention for the slots that handle them.
    # For example signal_* and handle_*.
    # 2)
    # And try to make the signal content as small as possible. DO NOT pass large objects through signals, like
    # pandas DataFrames or numpy arrays. Instead, pass the minimum amount of information needed
    # (i.e. lists of filepaths)

    signal_started = pyqtSignal()
    signal_result = pyqtSignal(object)
    signal_finished = pyqtSignal()
    signal_progress = pyqtSignal(str)


class Worker(QRunnable):
    """
    This is the thread that is going to do the work so that the
    application doesn't freeze

    Inherits from QRunnable to handle worker thread setup, signals, and tear down
    :param callback: the function callback to run on this worker thread. Supplied
                    arg and kwargs will be passed through to the runner
    :type callback: function
    :param args: Arguments to pass to the callback function
    :param kwargs: Keywords to pass to the callback function
    """

    def __init__(self, fn, *args, **kwargs):
        super(Worker, self).__init__()
        # Store constructor arguments (re-used for processing)
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals: WorkerSignals = WorkerSignals()

        # Add a callback to our kwargs
        self.kwargs["progress_callback"] = self.signals.signal_progress

    @pyqtSlot()
    def run(self) -> None:  # type: ignore
        """
        This is where the work is done.
        MUST be called run() in order for QRunnable to work

        Initialize the runner function with passed args & kwargs
        """
        self.signals.signal_started.emit()
        try:
            result = self.fn(*self.args, **self.kwargs)
        except Exception:
            traceback.print_exc()
            exctype, value = sys.exc_info()[:2]
            self.signals.signal_finished.emit((exctype, value, traceback.format_exc()))
            logging.error(
                f"Worker failed: {exctype} | {value} | {traceback.format_exc()}"
            )
        else:
            if result:
                self.signals.signal_finished.emit()
                self.signals.signal_result.emit(result)
            else:
                self.signals.signal_finished.emit()


class ApplicationWindow(QMainWindow, Ui_MainWindow):
    playlistCreatedSignal = pyqtSignal()

    def __init__(self):
        super(ApplicationWindow, self).__init__()
        global stopped
        stopped = False
        # Multithreading stuff...
        self.threadpool = QThreadPool()
        # UI
        self.setupUi(self)
        self.setWindowTitle("MusicPom")
        self.status_bar = QStatusBar()
        self.permanent_status_label = QLabel("Status...")
        self.status_bar.addPermanentWidget(self.permanent_status_label)
        self.setStatusBar(self.status_bar)
        self.selected_song_filepath: str | None = None
        self.current_song_filepath: str | None = None
        self.current_song_metadata: ID3 | dict | None = None
        self.current_song_album_art: bytes | None = None
        self.album_art_scene: QGraphicsScene = QGraphicsScene()
        self.config: ConfigParser = ConfigParser()
        self.player: QMediaPlayer = QMediaPlayer()  # Audio player object
        self.probe: QAudioProbe = QAudioProbe()  # Gets audio data
        self.audio_visualizer: AudioVisualizer = AudioVisualizer(self.player)
        self.current_volume: int = 50
        self.tableView.load_qapp(self)
        self.albumGraphicsView.load_qapp(self)
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

        # Connections
        self.playbackSlider.sliderReleased.connect(
            lambda: self.player.setPosition(self.playbackSlider.value())
        )  # sliderReleased works better than sliderMoved
        self.volumeSlider.sliderMoved[int].connect(lambda: self.volume_changed())
        self.playButton.clicked.connect(self.on_play_clicked)  # Click to play/pause
        self.previousButton.clicked.connect(self.on_previous_clicked)
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
        self.actionSortColumns.triggered.connect(
            self.tableView.sort_table_by_multiple_columns
        )

        # QTableView
        # for drag & drop functionality
        self.tableView.viewport().installEventFilter(self)

        ## CONNECTIONS
        # tableView
        self.tableView.doubleClicked.connect(
            self.play_audio_file
        )  # Listens for the double click event, then plays the song
        self.tableView.enterKey.connect(
            self.play_audio_file
        )  # Listens for the enter key event, then plays the song
        self.tableView.playPauseSignal.connect(
            self.on_play_clicked
        )  # Spacebar toggle play/pause signal
        self.tableView.handleProgressSignal.connect(self.handle_progress)

        # playlistTreeView
        self.playlistTreeView.playlistChoiceSignal.connect(
            self.tableView.load_music_table
        )
        self.playlistTreeView.allSongsSignal.connect(self.tableView.load_music_table)

        # albumGraphicsView
        self.albumGraphicsView.albumArtDropped.connect(
            self.set_album_art_for_selected_songs
        )
        self.albumGraphicsView.albumArtDeleted.connect(
            self.delete_album_art_for_current_song
        )

    def reload_config(self) -> None:
        """does what it says"""
        self.config.read("config.ini")

    def get_thread_pool(self) -> QThreadPool:
        """Returns the threadpool instance"""
        return self.threadpool

    def resizeEvent(self, a0: typing.Optional[QResizeEvent]) -> None:
        """Do something when the window resizes"""
        if a0 is not None:
            return super().resizeEvent(a0)

    def closeEvent(self, a0: QCloseEvent | None) -> None:
        """Save settings when closing the application"""
        # MusicTable/tableView column widths
        list_of_column_widths = []
        for i in range(self.tableView.model2.columnCount()):
            list_of_column_widths.append(str(self.tableView.columnWidth(i)))
        column_widths_as_string = ",".join(list_of_column_widths)
        self.config["table"]["column_widths"] = column_widths_as_string

        # Save the config
        with open("config.ini", "w") as configfile:
            self.config.write(configfile)
        if a0 is not None:
            super().closeEvent(a0)

    def show_status_bar_message(self, message: str, timeout: int | None = None) -> None:
        """
        Show a `message` in the status bar for a length of time - `timeout` in ms
        """
        if timeout:
            self.status_bar.showMessage(message, timeout)
        else:
            self.status_bar.showMessage(message)

    def set_permanent_status_bar_message(self, message: str) -> None:
        """
        Sets the permanent message label in the status bar
        """
        self.permanent_status_label.setText(message)

    def play_audio_file(self) -> None:
        """Start playback of tableView.current_song_filepath track & moves playback slider"""
        # get metadata
        self.current_song_metadata = self.tableView.get_current_song_metadata()
        logging.info("current song metadata: %s", self.current_song_metadata)
        self.current_song_album_art = self.tableView.get_current_song_album_art()
        # read the file
        url = QUrl.fromLocalFile(self.tableView.get_current_song_filepath())
        # load the audio content
        content = QMediaContent(url)
        # set the player to play the content
        self.player.setMedia(content)
        self.player.play()  # play
        self.move_slider()  # mover

        # assign metadata
        if self.current_song_metadata is not None:
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
            pixmap_item = QGraphicsPixmapItem(pixmap)
            pixmap_item.setTransformationMode(
                Qt.TransformationMode.SmoothTransformation
            )  # For better quality scaling
            # Add pixmap item to the scene
            self.album_art_scene.addItem(pixmap_item)
            # Set the scene
            self.albumGraphicsView.setScene(self.album_art_scene)
            # Adjust the album art scaling
            self.adjust_pixmap_scaling(pixmap_item)

    def adjust_pixmap_scaling(self, pixmap_item) -> None:
        """Adjust the scaling of the pixmap item to fit the QGraphicsView, maintaining aspect ratio"""
        viewWidth = self.albumGraphicsView.width()
        viewHeight = self.albumGraphicsView.height()
        pixmapSize = pixmap_item.pixmap().size()
        # Calculate scaling factor while maintaining aspect ratio
        scaleX = viewWidth / pixmapSize.width()
        scaleY = viewHeight / pixmapSize.height()
        scaleFactor = min(scaleX, scaleY)
        # Apply scaling to the pixmap item
        pixmap_item.setScale(scaleFactor)

    def set_album_art_for_selected_songs(self, album_art_path: str) -> None:
        """Sets the ID3 tag APIC (album art) for all selected song filepaths"""
        selected_songs = self.tableView.get_selected_songs_filepaths()
        for song in selected_songs:
            logging.info(
                f"main.py set_album_art_for_selected_songs() | updating album art for {song}"
            )
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

    def delete_album_art_for_current_song(self) -> None:
        """Handles deleting the ID3 tag APIC (album art) for current song"""
        file = self.tableView.get_current_song_filepath()
        # delete APIC data
        try:
            audio = ID3(file)
            if "APIC:" in audio:
                del audio["APIC"]
                audio.save()
        except Exception as e:
            logging.error(
                f"delete_album_art_for_selected_songs() | Error processing {file}: {e}"
            )

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
            logging.error(f"main.py volume_changed() | Changing volume error: {e}")

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
        logging.info("main.py on_previous_clicked()")

    def on_next_clicked(self) -> None:
        logging.info("main.py on_next_clicked()")

    def add_latest_playlist_to_tree(self) -> None:
        """Refreshes the playlist tree"""
        self.playlistTreeView.add_latest_playlist_to_tree()

    def open_files(self) -> None:
        """
        Opens the open files window
        - File > Open > List of song(s)
        """
        open_files_window = QFileDialog(
            self, "Open file(s)", ".", "Audio files (*.mp3)"
        )
        # QFileDialog.FileMode enum { AnyFile, ExistingFile, Directory, ExistingFiles }
        open_files_window.setFileMode(QFileDialog.ExistingFiles)
        open_files_window.exec_()
        filenames = open_files_window.selectedFiles()
        # Adds files to the library in a new thread
        worker = Worker(add_files_to_library, filenames)
        worker.signals.signal_finished.connect(self.tableView.load_music_table)
        worker.signals.signal_progress.connect(self.handle_progress)
        self.threadpool.start(worker)

    def handle_progress(self, data):
        """
        updates the status bar when progress is emitted
        """
        self.show_status_bar_message(data)

    # File

    def create_playlist(self) -> None:
        """Creates a database record for a playlist, given a name"""
        window = CreatePlaylistWindow(self.playlistCreatedSignal)
        window.playlistCreatedSignal.connect(self.add_latest_playlist_to_tree)
        window.exec_()

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

    # Edit

    def open_preferences(self) -> None:
        """Opens the preferences window"""
        preferences_window = PreferencesWindow(self.config)
        preferences_window.exec_()  # Display the preferences window modally
        self.reload_config()

    # Quick Actions

    def scan_libraries(self) -> None:
        """
        Scans for new files in the configured library folder
        Refreshes the datagridview
        """
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
        """Audio visualizer buffer processing"""
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
                    logging.info(f"executing [{statement}]")
                    db.execute(statement, ())
    # logging setup
    file_handler = logging.FileHandler(filename="log", encoding="utf-8")
    stdout_handler = logging.StreamHandler(stream=sys.stdout)
    handlers = [file_handler, stdout_handler]
    # logging.basicConfig(filename="log", encoding="utf-8", level=logging.DEBUG)
    logging.basicConfig(
        level=logging.INFO,
        format="[%(asctime)s] {%(filename)s:%(lineno)d} %(levelname)s - %(message)s",
        handlers=handlers,
    )
    # Allow for dynamic imports of my custom classes and utilities
    project_root = os.path.abspath(os.path.dirname(__file__))
    sys.path.append(project_root)
    # Start the app
    app = QApplication(sys.argv)
    # Dark theme >:3
    qdarktheme.setup_theme()
    # Show the UI
    ui = ApplicationWindow()
    ui.show()
    sys.exit(app.exec_())
