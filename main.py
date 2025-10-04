import os
import sys
import logging
import typing
import DBA
import qdarktheme
from PyQt5 import QtCore
from subprocess import run
# from pyqtgraph import mkBrush
from mutagen.id3 import ID3
# from mutagen.id3._frames import APIC
from configparser import ConfigParser
from pathlib import Path
from appdirs import user_config_dir
from logging import debug, error, basicConfig, DEBUG
from ui import Ui_MainWindow
from PyQt5.QtWidgets import (
    QFileDialog,
    QLabel,
    QLineEdit,
    QMainWindow,
    QApplication,
    QGraphicsScene,
    QMessageBox,
    QPushButton,
    QStatusBar,
    QStyle,
)
from PyQt5.QtCore import (
    QModelIndex,
    QSize,
    QUrl,
    QTimer,
    QThreadPool,
)
from PyQt5.QtMultimedia import (
    QMediaPlayer,
    QMediaContent,
    QAudioProbe,
)
from PyQt5.QtGui import QCloseEvent, QFont, QResizeEvent
from utils import (
    delete_album_art,
    get_tags,
    scan_for_music,
    initialize_db,
    add_files_to_database,
    set_album_art,
    id3_remap,
    get_album_art,
    Worker
)
from components import (
    MediaPlayer,
    MusicTable,
    PreferencesWindow,
    AudioVisualizer,
    CreatePlaylistWindow,
    ExportPlaylistWindow,
    HeaderTags2,
)
from utils.export_playlist_by_id import export_playlist_by_id

# good help with signals slots in threads
# https://stackoverflow.com/questions/52993677/how-do-i-setup-signals-and-slots-in-pyqt-with-qthreads-in-both-directions

# GOOD
# https://www.pythonguis.com/tutorials/multithreading-pyqt-applications-qthreadpool/


class ApplicationWindow(QMainWindow, Ui_MainWindow):
    def __init__(self, clipboard):
        super(ApplicationWindow, self).__init__()
        self.clipboard = clipboard
        self.config: ConfigParser = ConfigParser()
        self.cfg_file: Path = (
            Path(user_config_dir(appname="musicpom", appauthor="billypom"))
            / "config.ini"
        )
        self.config.read(self.cfg_file)
        self.threadpool: QThreadPool = QThreadPool()
        # UI
        self.setupUi(self)
        self.setWindowTitle("musicpom")
        self.setup_labels()

        # self.vLayoutAlbumArt.SetFixedSize()
        self.status_bar: QStatusBar = QStatusBar()
        self.permanent_status_label: QLabel = QLabel("")
        self.status_bar.addPermanentWidget(self.permanent_status_label)
        self.setStatusBar(self.status_bar)

        # table
        self.selected_song_filepath: str | None = None
        self.current_song_filepath: str | None = None
        self.current_song_metadata: ID3 | dict | None = None
        self.current_song_album_art: bytes | None = None

        # widget bits
        self.tableView: MusicTable
        self.tableView.saved_column_ratios: list[str] = str(self.config["table"]["column_ratios"]).split(",") # type: ignore
        self.album_art_scene: QGraphicsScene = QGraphicsScene()
        self.player: QMediaPlayer = MediaPlayer()
        # set index on choose song
        # index is the model2's row number? i guess?
        self.probe: QAudioProbe = QAudioProbe()  # Gets audio buffer data
        self.audio_visualizer: AudioVisualizer = AudioVisualizer(self.player, self.probe, self.PlotWidget)
        self.timer: QTimer = QTimer(parent=self)  # for playback slider and such

        # Button styles
        style: QStyle | None
        if not self.style():
            style = QStyle()
        else:
            style = self.style()
        assert style is not None
        pixmapi = QStyle.StandardPixmap.SP_MediaSkipForward
        icon = style.standardIcon(pixmapi)
        self.nextButton.setIcon(icon)
        pixmapi = QStyle.StandardPixmap.SP_MediaSkipBackward
        icon = style.standardIcon(pixmapi)
        self.previousButton.setIcon(icon)
        pixmapi = QStyle.StandardPixmap.SP_MediaPlay
        icon = style.standardIcon(pixmapi)
        self.playButton: QPushButton
        self.playButton.setIcon(icon)

        # sharing functions with other classes and that
        self.tableView.load_qapp(self)
        self.albumGraphicsView.load_qapp(self)
        self.playlistTreeView.load_qapp(self)
        self.headers = HeaderTags2()

        # Settings init
        self.current_volume: int = int(self.config["settings"]["volume"])
        self.player.setVolume(self.current_volume)
        self.volumeLabel.setText(str(self.current_volume))
        self.volumeSlider.setValue(self.current_volume)

        # Slider Timer (realtime playback feedback horizontal bar)
        self.timer.start(100)
        self.timer.timeout.connect(self.move_slider)

        # Set fixed size for album art
        self.albumGraphicsView.setFixedSize(250, 250)

        # Connections
        self.playbackSlider.sliderReleased.connect(lambda: self.player.setPosition(self.playbackSlider.value()))  # sliderReleased works better than sliderMoved
        self.volumeSlider.sliderMoved[int].connect(lambda: self.on_volume_changed())
        self.speedSlider.sliderMoved.connect(lambda: self.on_speed_changed(self.speedSlider.value()))
        # self.speedSlider.doubleClicked.connect(lambda: self.on_speed_changed(1))
        self.playButton.clicked.connect(self.on_play_clicked)  # Click to play/pause
        self.previousButton.clicked.connect(self.on_prev_clicked)
        self.nextButton.clicked.connect(self.on_next_clicked)  # Click to next song

        # FILE MENU
        self.actionOpenFiles.triggered.connect(self.open_files)  # Open files window
        self.actionNewPlaylist.triggered.connect(self.playlistTreeView.create_playlist)
        self.actionExportPlaylist.triggered.connect(self.export_playlist)

        # EDIT MENU
        self.actionPreferences.triggered.connect(self.open_preferences)
        # VIEW MENU

        # QUICK ACTIONS MENU
        self.actionScanLibraries.triggered.connect(self.scan_libraries)
        self.actionDeleteDatabase.triggered.connect(self.delete_database)
        self.actionSortColumns.triggered.connect(self.tableView.sort_table_by_multiple_columns)

        # QTableView
        # for drag & drop functionality
        self.tableView.viewport().installEventFilter(self)

        # Search box
        self.lineEditSearch: QLineEdit

        # CONNECTIONS
        self.lineEditSearch.textTypedSignal.connect(self.handle_search_box_text)
        # tableView
        self.tableView.playSignal.connect(self.play_audio_file)
        self.tableView.playPauseSignal.connect(self.on_play_clicked)  # Spacebar toggle play/pause signal
        self.tableView.handleProgressSignal.connect(self.handle_progress)
        self.tableView.searchBoxSignal.connect(self.handle_search_box_visibility)
        self.tableView.playlistStatsSignal.connect(self.set_permanent_status_bar_message)
        self.tableView.load_music_table()
        self.player.playlistNextSignal.connect(self.on_next_clicked)

        # playlistTreeView
        self.playlistTreeView.playlistChoiceSignal.connect(self.tableView.load_music_table)
        self.playlistTreeView.allSongsSignal.connect(self.tableView.load_music_table)

        # albumGraphicsView
        self.albumGraphicsView.albumArtDropped.connect(self.set_album_art_for_selected_songs)
        self.albumGraphicsView.albumArtDeleted.connect(self.delete_album_art_for_current_song)

    #  _________________
    # |                 |
    # |                 |
    # | Built-in Events |
    # |                 |
    # |_________________|

    def resizeEvent(self, a0: typing.Optional[QResizeEvent]) -> None:
        """Do something when the window resizes"""
        if a0 is not None:
            return super().resizeEvent(a0)

    def closeEvent(self, a0: QCloseEvent | None) -> None:
        """Save settings when closing the application"""
        # MusicTable/tableView column widths
        # list_of_column_widths = []
        # for i in range(self.tableView.model2.columnCount()):
        #     list_of_column_widths.append(str(self.tableView.columnWidth(i)))
        # column_widths_as_string = ",".join(list_of_column_widths)
        # debug(f"saving column widths: {column_widths_as_string}")
        # self.config["table"]["column_widths"] = column_widths_as_string

        self.config["settings"]["volume"] = str(self.current_volume)
        self.config["settings"]["window_size"] = (str(self.width()) + "," + str(self.height()))
        self.config['table']['column_ratios'] = ",".join(self.tableView.get_current_header_width_ratios())
        # Save the config
        try:
            with open(self.cfg_file, "w") as configfile:
                self.config.write(configfile)
        except Exception as e:
            debug(f"wtf man {e}")
        # auto export any playlists that want it
        try:
            with DBA.DBAccess() as db:
                result = db.query('SELECT id FROM playlist WHERE auto_export = true;', ())
            ids = [id[0] for id in result]
            for id in ids:
                export_playlist_by_id(id)
        except Exception:
            pass
        if a0 is not None:
            super().closeEvent(a0)

    #  ____________________
    # |                    |
    # |                    |
    # | On action handlers |
    # |                    |
    # |____________________|

    def on_playlist_media_changed(self, media: QMediaContent):
        """Update stuff when the song changes"""
        if not media.isNull():
            file_url = media.canonicalUrl().toLocalFile()
            metadata = id3_remap(get_tags(file_url)[0])
            if metadata is not None:
                self.set_ui_metadata(
                    metadata["title"], metadata["artist"], metadata["album"], file_url
                )

    def on_volume_changed(self) -> None:
        """Handles volume changes"""
        try:
            self.current_volume = self.volumeSlider.value()
            self.player.setVolume(self.current_volume)
            self.volumeLabel.setText(str(self.current_volume))
        except Exception as e:
            error(f"main.py on_volume_changed() | Changing volume error: {e}")

    def on_speed_changed(self, rate: int) -> None:
        """Handles playback speed changes"""
        self.player.setPlaybackRate(rate / 50)
        self.speedLabel.setText("{:.2f}".format(rate / 50))

    def on_play_clicked(self) -> None:
        """
        Plays & pauses the song
        Updates the button icons
        """
        pixmapi = QStyle.StandardPixmap.SP_MediaPlay
        play_icon = self.style().standardIcon(pixmapi)  # type: ignore
        pixmapi = QStyle.StandardPixmap.SP_MediaPause
        pause_icon = self.style().standardIcon(pixmapi)  # type: ignore
        if self.player.state() == QMediaPlayer.State.PlayingState:
            self.player.pause()
            self.playButton.setText(None)
            self.playButton.setIcon(pause_icon)
        else:
            if self.player.state() == QMediaPlayer.State.PausedState:
                self.player.play()
                self.playButton.setText(None)
                self.playButton.setIcon(play_icon)
            else:
                self.playButton.setText("👽")

    def on_prev_clicked(self) -> None:
        """click previous - go to previous song"""
        current_real_index = self.tableView.current_song_qmodel_index
        try:
            index = self.tableView.proxymodel.mapFromSource(current_real_index)
        except Exception:
            return
        row: int = index.row()
        prev_row: int = row - 1
        prev_index: QModelIndex = self.tableView.proxymodel.index(prev_row, index.column())
        prev_filepath = prev_index.siblingAtColumn(self.headers.db_list.index("filepath")).data()
        if prev_filepath is None:
            return

        self.play_audio_file(prev_filepath)
        self.tableView.set_current_song_qmodel_index(prev_index)
        self.tableView.set_current_song_filepath(prev_filepath)

    def on_next_clicked(self) -> None:
        """click next (or song ended) - go to next song"""
        current_real_index = self.tableView.current_song_qmodel_index
        try:
            # FIXME: seg fault here but only sometimes???
            # when playing song in lib, switch to playlist, back to lib, next song
            index = self.tableView.proxymodel.mapFromSource(current_real_index)
        except Exception:
            return
        row: int = index.row()
        next_row: int = row + 1
        next_index: QModelIndex = self.tableView.proxymodel.index(next_row, index.column())
        next_filepath = next_index.siblingAtColumn(self.headers.db_list.index("filepath")).data()
        if next_filepath is None:
            return
        self.play_audio_file(next_filepath)
        self.tableView.set_current_song_qmodel_index(next_index)
        self.tableView.set_current_song_filepath(next_filepath)

    #  ____________________
    # |                    |
    # |                    |
    # |       Verbs        |
    # |                    |
    # |____________________|

    def setup_labels(self):
        """Initializes attributes and behaviors for various UI labels"""
        font: QFont = QFont()
        font.setPointSize(12)
        font.setBold(True)
        self.artistLabel: QLabel
        self.artistLabel.setFont(font)
        self.artistLabel.setTextInteractionFlags(
            QtCore.Qt.TextInteractionFlag.TextSelectableByMouse
        )
        self.artistLabel.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.artistLabel.setWordWrap(True)

        font.setPointSize(12)
        font.setBold(False)
        self.titleLabel.setFont(font)
        self.titleLabel.setTextInteractionFlags(
            QtCore.Qt.TextInteractionFlag.TextSelectableByMouse
        )
        self.titleLabel.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.titleLabel.setWordWrap(True)

        font.setPointSize(12)
        font.setItalic(True)
        self.albumLabel: QLabel
        self.albumLabel.setFont(font)
        self.albumLabel.setTextInteractionFlags(
            QtCore.Qt.TextInteractionFlag.TextSelectableByMouse
        )
        self.albumLabel.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.albumLabel.setWordWrap(True)

    def load_config(self) -> None:
        """does what it says"""
        cfg_file = (
            Path(user_config_dir(appname="musicpom",
                 appauthor="billypom")) / "config.ini"
        )
        self.config.read(cfg_file)
        debug("load_config()")

    def set_permanent_status_bar_message(self, message: str) -> None:
        """
        Sets the permanent message label in the status bar
        """
        self.permanent_status_label.setText(message)

    def show_status_bar_message(self, message: str, timeout: int | None = None) -> None:
        """
        Show a `message` in the status bar for a length of time - `timeout` in ms
        (bottom left)
        """
        if timeout:
            self.status_bar.showMessage(message, timeout)
        else:
            self.status_bar.showMessage(message)

    def handle_search_box_visibility(self):
        """show or hide the searchbox"""
        visible = self.lineEditSearch.toggle_visibility()
        if visible:
            self.lineEditSearch.setFocus()
        else:
            self.tableView.setFocus()

    def handle_search_box_text(self, text: str):
        """when text changes, update the music table thingie"""
        self.tableView.set_search_string(text)
        self.tableView.load_music_table()

    def play_audio_file(self, filepath=None) -> None:
        """
        Start playback of filepath & moves playback slider

        filepath default value = `tableView.current_song_filepath`
        """
        if not filepath:
            filepath = self.tableView.get_selected_song_filepath()
        metadata = id3_remap(get_tags(filepath)[0])
        # read the file
        url = QUrl.fromLocalFile(filepath)
        # load the audio content
        content = QMediaContent(url)
        # set the player to play the content
        self.player.setMedia(content)
        # self.player.setMedia(QUrl("gst-pipeline: videotestsrc ! autovideosink"))
        self.player.play()  # play
        self.move_slider()  # mover

        # assign "now playing" labels & album artwork
        if metadata is not None:
            self.set_ui_metadata(
                metadata["title"], metadata["artist"], metadata["album"], filepath
            )

    def set_ui_metadata(self, title, artist, album, filepath):
        """
        Loads metadata into UI, presumably for current song
        But you could pass any text here i guess
        album art will always try to be current song
        """
        self.artistLabel.setText(artist)
        self.albumLabel.setText(album)
        self.titleLabel.setText(title)
        # set album artwork
        album_art_data = get_album_art(filepath)
        self.albumGraphicsView.load_album_art(album_art_data)

    def set_album_art_for_selected_songs(self, album_art_path: str) -> None:
        """Sets the ID3 tag APIC (album art) for all selected song filepaths"""
        selected_songs = self.tableView.get_selected_songs_filepaths()
        for song in selected_songs:
            debug(
                f"main.py set_album_art_for_selected_songs() | updating album art for {
                    song}"
            )
            set_album_art(song, album_art_path)

    def delete_album_art_for_current_song(self) -> None:
        """Handles deleting the ID3 tag APIC (album art) for current song"""
        file = self.tableView.get_current_song_filepath()
        result = delete_album_art(file)
        if result:
            # Load the default album artwork in the qgraphicsview
            album_art_data = get_album_art(None)
            self.albumGraphicsView.load_album_art(album_art_data)

    def move_slider(self) -> None:
        """Handles moving the playback slider"""
        if self.player.state() == QMediaPlayer.State.StoppedState:
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
                current_minutes, current_seconds = divmod(
                    slider_position / 1000, 60)
                duration_minutes, duration_seconds = divmod(
                    self.player.duration() / 1000, 60
                )
                self.startTimeLabel.setText(
                    f"{int(current_minutes):02d}:{int(current_seconds):02d}"
                )
                self.endTimeLabel.setText(
                    f"{int(duration_minutes):02d}:{int(duration_seconds):02d}"
                )

    def add_latest_playlist_to_tree(self) -> None:
        """Refreshes the playlist tree"""
        self.playlistTreeView.add_latest_playlist_to_tree()

    def handle_progress(self, data):
        """
        updates the status bar when progress is emitted
        """
        self.show_status_bar_message(data)

    #  ____________________
    # |                    |
    # |                    |
    # |   menubar verbs    |
    # |                    |
    # |____________________|

    # File

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
        worker = Worker(add_files_to_database, filenames)
        worker.signals.signal_finished.connect(self.tableView.load_music_table)
        worker.signals.signal_progress.connect(self.handle_progress)
        self.threadpool.start(worker)

    def create_playlist(self) -> None:
        """Creates a database record for a playlist, given a name"""
        window = CreatePlaylistWindow(self.playlistCreatedSignal)
        window.playlistCreatedSignal.connect(
            self.add_latest_playlist_to_tree)  # type: ignore
        window.exec_()

    def import_playlist(self) -> None:
        """
        Imports a .m3u file, given a base path attempts to match playlist files to
        database records that currently exist
        """
        # TODO: implement this
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
        preferences_window = PreferencesWindow()
        preferences_window.reloadConfigSignal.connect(self.load_config)
        preferences_window.reloadDatabaseSignal.connect(self.tableView.load_music_table)
        preferences_window.exec_()  # Display the preferences window modally

    # Quick Actions

    def scan_libraries(self) -> None:
        """
        Scans for new files in the configured library folder
        then, refreshes the datagridview
        """
        worker = Worker(scan_for_music)
        worker.signals.signal_finished.connect(self.tableView.load_music_table)
        worker.signals.signal_progress.connect(self.handle_progress)
        self.threadpool.start(worker)

    def delete_database(self) -> None:
        """Deletes the entire database"""
        reply = QMessageBox.question(
            parent=self,
            title="Confirmation",
            text="Delete database?",
            buttons=QMessageBox.Yes | QMessageBox.No,
            defaultButton=QMessageBox.Yes,
        )
        if reply == QMessageBox.Yes:
            initialize_db()
            self.tableView.load_music_table()


def update_database_file() -> bool:
    """
    Reads the database file (specified by config file)
    """
    cfg_file = (
        Path(user_config_dir(appname="musicpom",
             appauthor="billypom")) / "config.ini"
    )
    cfg_path = str(Path(user_config_dir(
        appname="musicpom", appauthor="billypom")))
    config = ConfigParser()
    config.read(cfg_file)
    db_filepath: str
    db_filepath= config.get("settings", "db")

    # If the database location isnt set at the config location, move it
    if not db_filepath.startswith(cfg_path):
        new_path = f"{cfg_path}/{db_filepath}"
        debug(
            f"Set new config [db] database path: \n> Current: {
                db_filepath}\n> New:{new_path}"
        )
        config["settings"]["db"] = new_path
        # Save the config
        with open(cfg_file, "w") as configfile:
            config.write(configfile)
        config.read(cfg_file)
        db_filepath = config.get("settings", "db")

    db_path = db_filepath.split("/")
    db_path.pop()
    db_path = "/".join(db_path)

    if os.path.exists(db_filepath):
        try:
            size = os.path.getsize(db_filepath)
        except OSError:
            error("Database file exists but could not read.")
            return False
        if size == 0:
            initialize_db()
    if not os.path.exists(db_filepath):
        if not os.path.exists(db_path):
            os.makedirs(db_path)
        # still make the db even if the directory existed
        initialize_db()
    return True


def update_config_file() -> ConfigParser:
    """
    If the user config file is not up to date, update it with examples from sample config
    """
    cfg_file = (
        Path(user_config_dir(appname="musicpom",
             appauthor="billypom")) / "config.ini"
    )
    cfg_path = str(Path(user_config_dir(
        appname="musicpom", appauthor="billypom")))

    # If config path doesn't exist, create it
    if not os.path.exists(cfg_path):
        os.makedirs(cfg_path)
    # If the config file doesn't exist, create it from the sample config
    if not os.path.exists(cfg_file):
        debug("copying sample config")
        # Create config file from sample
        run(["cp", "./sample_config.ini", cfg_file])
        config = ConfigParser()
        config.read(cfg_file)
        return config

    # Current config - add new sections
    config = ConfigParser()
    config.read(cfg_file)
    sample_config = ConfigParser()
    sample_cfg_file = "./sample_config.ini"
    sample_config.read(sample_cfg_file)
    orig_sections = config.sections()
    sample_sections = sample_config.sections()
    for section in sample_sections:
        if section not in orig_sections:
            config.add_section(section)
        orig_options = dict(config.items(section))
        sample_options = dict(sample_config.items(section))
        for option, value in sample_options.items():
            if option not in orig_options:
                # add new options to the section, for current config
                config.set(section, option, value)

    with open(cfg_file, "w") as configfile:
        config.write(configfile)
    return config


if __name__ == "__main__":
    # logging setup
    file_handler = logging.FileHandler(filename="log", encoding="utf-8")
    stdout_handler = logging.StreamHandler(stream=sys.stdout)
    handlers = [file_handler, stdout_handler]
    basicConfig(
        level=DEBUG,
        # format="[%(asctime)s] {%(filename)s:%(lineno)d} %(levelname)s - %(message)s",
        format="{%(filename)s:%(lineno)d} %(levelname)s - %(message)s",
        handlers=handlers,
    )
    debug('--------- musicpom debug started')
    debug('---------------------|          ')
    debug(f'----------------------> {handlers}      ')
    # Initialization
    config: ConfigParser = update_config_file()
    if not update_database_file():
        sys.exit(1)

    # Allow for dynamic imports of my custom classes and utilities
    # ?
    project_root = os.path.abspath(os.path.dirname(__file__))
    sys.path.append(project_root)
    # Start the app
    app = QApplication(sys.argv)
    clipboard = app.clipboard()
    # Dark theme >:3
    qdarktheme.setup_theme()
    # qdarktheme.setup_theme("auto")  # this is supposed to work but doesnt
    # Show the UI
    ui = ApplicationWindow(clipboard)
    # window size
    width, height = tuple(config.get("settings", "window_size").split(","))
    window_size = QSize(int(width), int(height))
    ui.resize(window_size)
    ui.show()
    sys.exit(app.exec_())
