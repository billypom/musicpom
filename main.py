import os
import configparser
import sys
import logging
from subprocess import run
import qdarktheme
from pyqtgraph import PlotWidget
from pyqtgraph import mkBrush
from mutagen.id3 import ID3
from mutagen.id3._frames import APIC
from configparser import ConfigParser
import DBA
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import (
    QFileDialog,
    QMainWindow,
    QApplication,
    QGraphicsScene,
    QHeaderView,
    QGraphicsPixmapItem,
    QMessageBox,
)
from PyQt5.QtCore import QUrl, QTimer, Qt
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent, QAudioProbe
from PyQt5.QtGui import QCloseEvent, QPixmap
from utils import scan_for_music, delete_and_create_library_database, initialize_db
from components import (
    PreferencesWindow,
    AudioVisualizer,
    AlbumArtGraphicsView,
    MusicTable,
)


class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        global stopped
        stopped = False
        # Vars
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
        # Initialization
        self.config.read("config.ini")
        self.player.setVolume(self.current_volume)
        # Audio probe for processing audio signal in real time
        self.probe.setSource(self.player)
        self.probe.audioBufferProbed.connect(self.process_probe)
        # Slider Timer (realtime playback feedback horizontal bar)
        self.timer: QTimer = QTimer(self)  # Audio timing things
        self.timer.start(
            150
        )  # 150ms update interval solved problem with drag seeking halting playback
        self.timer.timeout.connect(self.move_slider)

        # Graphics plot
        self.PlotWidget.setXRange(0, 100, padding=0)  # x axis range
        self.PlotWidget.setYRange(0, 0.8, padding=0)  # y axis range
        # Remove axis labels and decorations
        # self.PlotWidget.setLogMode(False, False)
        self.PlotWidget.getAxis("bottom").setTicks([])  # Remove x-axis ticks
        self.PlotWidget.getAxis("bottom").setLabel("")  # Remove x-axis label
        self.PlotWidget.getAxis("left").setTicks([])  # Remove y-axis ticks
        self.PlotWidget.getAxis("left").setLabel("")  # Remove y-axis label

        #  _____________
        # |             |
        # | CONNECTIONS |
        # | CONNECTIONS |
        # | CONNECTIONS |
        # |_____________|

        #  FIXME: moving the slider while playing is happening frequently causes playback to halt - the pyqtgraph is also affected by this
        #  so it must be affecting our QMediaPlayer as well
        #  self.playbackSlider.sliderMoved[int].connect(
        #     lambda: self.player.setPosition(self.playbackSlider.value())
        # )
        self.playbackSlider.sliderReleased.connect(
            lambda: self.player.setPosition(self.playbackSlider.value())
        )  # maybe sliderReleased works better than sliderMoved
        self.volumeSlider.sliderMoved[int].connect(
            lambda: self.volume_changed()
        )  # Move slider to adjust volume
        # Playback controls
        self.playButton.clicked.connect(self.on_play_clicked)
        self.prevButton.clicked.connect(self.on_previous_clicked)
        self.nextButton.clicked.connect(self.on_next_clicked)
        # FILE MENU
        self.actionOpenFiles.triggered.connect(self.open_files)  # Open files window
        # EDIT MENU
        self.actionPreferences.triggered.connect(
            self.open_preferences
        )  # Open preferences menu
        # VIEW MENU
        # QUICK ACTIONS MENU
        self.actionScanLibraries.triggered.connect(self.scan_libraries)
        self.actionDeleteLibrary.triggered.connect(self.clear_database)
        self.actionDeleteDatabase.triggered.connect(self.delete_database)
        ## Music Table | self.tableView triggers
        # Listens for the double click event, then plays the song
        self.tableView.doubleClicked.connect(self.play_audio_file)
        # Listens for the enter key event, then plays the song
        self.tableView.enterKey.connect(self.play_audio_file)
        # Spacebar for toggle play/pause
        self.tableView.playPauseSignal.connect(self.on_play_clicked)
        # Album Art | self.albumGraphicsView
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

    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(1152, 894)
        MainWindow.setStatusTip("")
        # Main
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        #
        self.verticalLayout_3 = QtWidgets.QVBoxLayout(self.centralwidget)
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.hLayoutHead = QtWidgets.QHBoxLayout()
        self.hLayoutHead.setObjectName("hLayoutHead")
        self.vlayoutAlbumArt = QtWidgets.QVBoxLayout()
        self.vlayoutAlbumArt.setSizeConstraint(QtWidgets.QLayout.SetFixedSize)
        self.vlayoutAlbumArt.setObjectName("vlayoutAlbumArt")
        self.albumGraphicsView = AlbumArtGraphicsView(self.centralwidget)
        sizePolicy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum
        )
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(
            self.albumGraphicsView.sizePolicy().hasHeightForWidth()
        )
        self.albumGraphicsView.setSizePolicy(sizePolicy)
        self.albumGraphicsView.setMinimumSize(QtCore.QSize(200, 200))
        self.albumGraphicsView.setMaximumSize(QtCore.QSize(16777215, 16777215))
        self.albumGraphicsView.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.albumGraphicsView.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.albumGraphicsView.setHorizontalScrollBarPolicy(
            QtCore.Qt.ScrollBarAlwaysOff
        )
        self.albumGraphicsView.setSizeAdjustPolicy(
            QtWidgets.QAbstractScrollArea.AdjustIgnored
        )
        self.albumGraphicsView.setInteractive(False)
        self.albumGraphicsView.setResizeAnchor(QtWidgets.QGraphicsView.AnchorViewCenter)
        self.albumGraphicsView.setViewportUpdateMode(
            QtWidgets.QGraphicsView.FullViewportUpdate
        )
        self.albumGraphicsView.setObjectName("albumGraphicsView")
        self.vlayoutAlbumArt.addWidget(self.albumGraphicsView)
        self.hLayoutHead.addLayout(self.vlayoutAlbumArt)
        self.vLayoutSongDetails = QtWidgets.QVBoxLayout()
        self.vLayoutSongDetails.setObjectName("vLayoutSongDetails")
        self.artistLabel = QtWidgets.QLabel(self.centralwidget)
        font = QtGui.QFont()
        font.setPointSize(24)
        font.setBold(True)
        font.setWeight(75)
        self.artistLabel.setFont(font)
        self.artistLabel.setObjectName("artistLabel")
        self.vLayoutSongDetails.addWidget(self.artistLabel)
        self.titleLabel = QtWidgets.QLabel(self.centralwidget)
        font = QtGui.QFont()
        font.setPointSize(18)
        self.titleLabel.setFont(font)
        self.titleLabel.setObjectName("titleLabel")
        self.vLayoutSongDetails.addWidget(self.titleLabel)
        self.albumLabel = QtWidgets.QLabel(self.centralwidget)
        font = QtGui.QFont()
        font.setPointSize(16)
        font.setBold(False)
        font.setItalic(True)
        font.setWeight(50)
        self.albumLabel.setFont(font)
        self.albumLabel.setObjectName("albumLabel")
        self.vLayoutSongDetails.addWidget(self.albumLabel)
        self.hLayoutHead.addLayout(self.vLayoutSongDetails)
        self.vLayoutPlaybackVisuals = QtWidgets.QVBoxLayout()
        self.vLayoutPlaybackVisuals.setObjectName("vLayoutPlaybackVisuals")
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.playbackSlider = QtWidgets.QSlider(self.centralwidget)
        self.playbackSlider.setOrientation(QtCore.Qt.Horizontal)
        self.playbackSlider.setObjectName("playbackSlider")
        self.horizontalLayout.addWidget(self.playbackSlider)
        self.startTimeLabel = QtWidgets.QLabel(self.centralwidget)
        self.startTimeLabel.setObjectName("startTimeLabel")
        self.horizontalLayout.addWidget(self.startTimeLabel)
        self.slashLabel = QtWidgets.QLabel(self.centralwidget)
        self.slashLabel.setObjectName("slashLabel")
        self.horizontalLayout.addWidget(self.slashLabel)
        self.endTimeLabel = QtWidgets.QLabel(self.centralwidget)
        self.endTimeLabel.setObjectName("endTimeLabel")
        self.horizontalLayout.addWidget(self.endTimeLabel)
        self.vLayoutPlaybackVisuals.addLayout(self.horizontalLayout)
        self.PlotWidget = PlotWidget(self.centralwidget)
        self.PlotWidget.setObjectName("PlotWidget")
        self.vLayoutPlaybackVisuals.addWidget(self.PlotWidget)
        self.hLayoutHead.addLayout(self.vLayoutPlaybackVisuals)
        self.hLayoutHead.setStretch(0, 1)
        self.hLayoutHead.setStretch(1, 4)
        self.hLayoutHead.setStretch(2, 6)
        self.verticalLayout_3.addLayout(self.hLayoutHead)
        self.hLayoutMusicTable = QtWidgets.QHBoxLayout()
        self.hLayoutMusicTable.setObjectName("hLayoutMusicTable")
        self.tableView = MusicTable(self.centralwidget)
        sizePolicy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Maximum
        )
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(1)
        sizePolicy.setHeightForWidth(self.tableView.sizePolicy().hasHeightForWidth())
        self.tableView.setSizePolicy(sizePolicy)
        self.tableView.setMaximumSize(QtCore.QSize(32000, 32000))
        self.tableView.setAcceptDrops(True)
        self.tableView.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.tableView.setSizeAdjustPolicy(
            QtWidgets.QAbstractScrollArea.AdjustToContents
        )
        self.tableView.setEditTriggers(
            QtWidgets.QAbstractItemView.AnyKeyPressed
            | QtWidgets.QAbstractItemView.EditKeyPressed
        )
        self.tableView.setAlternatingRowColors(True)
        self.tableView.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.tableView.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.tableView.setSortingEnabled(True)
        self.tableView.setObjectName("tableView")
        self.tableView.horizontalHeader().setCascadingSectionResizes(True)
        self.tableView.horizontalHeader().setStretchLastSection(True)
        self.tableView.verticalHeader().setVisible(False)
        self.hLayoutMusicTable.addWidget(self.tableView)
        self.verticalLayout_3.addLayout(self.hLayoutMusicTable)
        self.hLayoutControls = QtWidgets.QHBoxLayout()
        self.hLayoutControls.setObjectName("hLayoutControls")
        self.prevButton = QtWidgets.QPushButton(self.centralwidget)
        font = QtGui.QFont()
        font.setPointSize(28)
        self.prevButton.setFont(font)
        self.prevButton.setObjectName("prevButton")
        self.hLayoutControls.addWidget(self.prevButton)
        self.playButton = QtWidgets.QPushButton(self.centralwidget)
        font = QtGui.QFont()
        font.setPointSize(28)
        self.playButton.setFont(font)
        self.playButton.setObjectName("playButton")
        self.hLayoutControls.addWidget(self.playButton)
        self.nextButton = QtWidgets.QPushButton(self.centralwidget)
        font = QtGui.QFont()
        font.setPointSize(28)
        self.nextButton.setFont(font)
        self.nextButton.setObjectName("nextButton")
        self.hLayoutControls.addWidget(self.nextButton)
        self.verticalLayout_3.addLayout(self.hLayoutControls)
        self.hLayoutControls2 = QtWidgets.QHBoxLayout()
        self.hLayoutControls2.setObjectName("hLayoutControls2")
        self.volumeSlider = QtWidgets.QSlider(self.centralwidget)
        self.volumeSlider.setMaximum(100)
        self.volumeSlider.setProperty("value", 50)
        self.volumeSlider.setOrientation(QtCore.Qt.Horizontal)
        self.volumeSlider.setObjectName("volumeSlider")
        self.hLayoutControls2.addWidget(self.volumeSlider)
        self.verticalLayout_3.addLayout(self.hLayoutControls2)
        self.verticalLayout_3.setStretch(0, 3)
        self.verticalLayout_3.setStretch(1, 8)
        self.verticalLayout_3.setStretch(2, 1)
        self.verticalLayout_3.setStretch(3, 1)
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 1152, 41))
        self.menubar.setObjectName("menubar")
        self.menuFile = QtWidgets.QMenu(self.menubar)
        self.menuFile.setObjectName("menuFile")
        self.menuEdit = QtWidgets.QMenu(self.menubar)
        self.menuEdit.setObjectName("menuEdit")
        self.menuView = QtWidgets.QMenu(self.menubar)
        self.menuView.setObjectName("menuView")
        self.menuQuick_Actions = QtWidgets.QMenu(self.menubar)
        self.menuQuick_Actions.setObjectName("menuQuick_Actions")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)
        self.actionPreferences = QtWidgets.QAction(MainWindow)
        self.actionPreferences.setObjectName("actionPreferences")
        self.actionScanLibraries = QtWidgets.QAction(MainWindow)
        self.actionScanLibraries.setObjectName("actionScanLibraries")
        self.actionDeleteLibrary = QtWidgets.QAction(MainWindow)
        self.actionDeleteLibrary.setObjectName("actionDeleteLibrary")
        self.actionOpenFiles = QtWidgets.QAction(MainWindow)
        self.actionOpenFiles.setObjectName("actionOpenFiles")
        self.actionDeleteDatabase = QtWidgets.QAction(MainWindow)
        self.actionDeleteDatabase.setObjectName("actionDeleteDatabase")
        self.menuFile.addAction(self.actionOpenFiles)
        self.menuEdit.addAction(self.actionPreferences)
        self.menuQuick_Actions.addAction(self.actionScanLibraries)
        self.menuQuick_Actions.addAction(self.actionDeleteLibrary)
        self.menuQuick_Actions.addAction(self.actionDeleteDatabase)
        self.menubar.addAction(self.menuFile.menuAction())
        self.menubar.addAction(self.menuEdit.menuAction())
        self.menubar.addAction(self.menuView.menuAction())
        self.menubar.addAction(self.menuQuick_Actions.menuAction())

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow"))
        self.artistLabel.setText(_translate("MainWindow", "artist"))
        self.titleLabel.setText(_translate("MainWindow", "song title"))
        self.albumLabel.setText(_translate("MainWindow", "album"))
        self.startTimeLabel.setText(_translate("MainWindow", "00:00"))
        self.slashLabel.setText(_translate("MainWindow", "/"))
        self.endTimeLabel.setText(_translate("MainWindow", "00:00"))
        self.prevButton.setText(_translate("MainWindow", "⏮️"))
        self.playButton.setText(_translate("MainWindow", "▶️"))
        self.nextButton.setText(_translate("MainWindow", "⏭️"))
        self.menuFile.setTitle(_translate("MainWindow", "File"))
        self.menuEdit.setTitle(_translate("MainWindow", "Edit"))
        self.menuView.setTitle(_translate("MainWindow", "View"))
        self.menuQuick_Actions.setTitle(_translate("MainWindow", "Quick-Actions"))
        self.actionPreferences.setText(_translate("MainWindow", "Preferences"))
        self.actionPreferences.setStatusTip(
            _translate("MainWindow", "Open preferences")
        )
        self.actionScanLibraries.setText(_translate("MainWindow", "Scan libraries"))
        self.actionDeleteLibrary.setText(_translate("MainWindow", "Delete Library"))
        self.actionOpenFiles.setText(_translate("MainWindow", "Open file(s)"))
        self.actionDeleteDatabase.setText(_translate("MainWindow", "Delete Database"))

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

    def play_audio_file(self) -> None:
        """Start playback of tableView.current_song_filepath track & moves playback slider"""
        self.current_song_metadata = self.tableView.get_current_song_metadata()
        self.current_song_album_art = self.tableView.get_current_song_album_art()
        # read the file
        url = QUrl.fromLocalFile(self.tableView.get_current_song_filepath())
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

    def open_files(self) -> None:
        """Opens the open files window"""
        open_files_window = QFileDialog(
            self, "Open file(s)", ".", "Audio files (*.mp3)"
        )
        # QFileDialog.FileMode enum { AnyFile, ExistingFile, Directory, ExistingFiles }
        open_files_window.setFileMode(QFileDialog.ExistingFiles)
        open_files_window.exec_()
        filenames = open_files_window.selectedFiles()
        print("file names chosen")
        print(filenames)
        self.tableView.add_files(filenames)

    def open_preferences(self) -> None:
        """Opens the preferences window"""
        preferences_window = PreferencesWindow(self.config)
        preferences_window.exec_()  # Display the preferences window modally

    def scan_libraries(self) -> None:
        """Scans for new files in the configured library folder
        Refreshes the datagridview"""
        scan_for_music()
        self.tableView.fetch_library()

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
            self.tableView.fetch_library()

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
            self.tableView.fetch_library()

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
            self.tableView.fetch_library()

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
        path_as_string = "/".join(db_path)
        if not os.path.exists(path_as_string):
            os.makedirs(path_as_string)
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
    print(f"main.py app: {app}")
    # Dark theme >:3
    qdarktheme.setup_theme()
    # Show the UI
    ui = MainWindow()
    ui.show()
    sys.exit(app.exec_())
