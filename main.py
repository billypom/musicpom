import DBA
from ui import Ui_MainWindow
from PyQt5.QtWidgets import QMainWindow, QApplication, QGraphicsScene
import qdarktheme
from PyQt5.QtCore import QUrl, QTimer, QEvent, Qt, QRect
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent, QAudioProbe
from PyQt5.QtGui import QPixmap
from utils import scan_for_music
from utils import initialize_library_database
from components import AudioVisualizer
from pyqtgraph import mkBrush
import configparser

# Create ui.py file from Qt Designer
# pyuic5 ui.ui -o ui.py

class ApplicationWindow(QMainWindow, Ui_MainWindow):
    def __init__(self, qapp):
        super(ApplicationWindow, self).__init__()
        self.setupUi(self)
        self.setWindowTitle('MusicPom')
        self.selected_song_filepath = None
        self.current_song_filepath = None
        self.current_song_metadata = None
        self.current_song_album_art = None
        self.album_art_scene = QGraphicsScene()
        self.qapp = qapp
        print(f'ApplicationWindow self.qapp: {self.qapp}')
        self.tableView.load_qapp(self.qapp)
        self.config = configparser.ConfigParser()
        self.config.read('config.ini')
        
        global stopped
        stopped = False
        
        # Initialization
        self.player = QMediaPlayer() # Audio player
        self.probe = QAudioProbe() # Get audio data
        self.timer = QTimer(self) # Audio timing things
        # self.model = QStandardItemModel() # Table library listing
        self.audio_visualizer = AudioVisualizer(self.player)
        self.current_volume = 50
        self.player.setVolume(self.current_volume)
        
        # Audio probe for processing audio signal in real time
        # Provides faster updates than move_slider
        self.probe.setSource(self.player)
        self.probe.audioBufferProbed.connect(self.process_probe)
        
        # Slider Timer (realtime playback feedback horizontal bar)
        self.timer.start(150) # 150ms update interval solved problem with drag seeking halting playback
        self.timer.timeout.connect(self.move_slider)
        
        # Graphics plot
        self.PlotWidget.setXRange(0,100,padding=0) # x axis range
        self.PlotWidget.setYRange(0,0.3,padding=0) # y axis range
        self.PlotWidget.getAxis('bottom').setTicks([]) # Remove x-axis ticks
        self.PlotWidget.getAxis('bottom').setLabel('') # Remove x-axis label
        self.PlotWidget.setLogMode(False,False)
        # Remove y-axis labels and decorations
        self.PlotWidget.getAxis('left').setTicks([]) # Remove y-axis ticks
        self.PlotWidget.getAxis('left').setLabel('') # Remove y-axis label
        
        
        # Connections
        # ! FIXME moving the slider while playing is happening frequently causes playback to halt - the pyqtgraph is also affected by this
        self.playbackSlider.sliderMoved[int].connect(lambda: self.player.setPosition(self.playbackSlider.value())) # Move slidet to adjust playback time
        self.volumeSlider.sliderMoved[int].connect(lambda: self.volume_changed()) # Move slider to adjust volume
        self.playButton.clicked.connect(self.on_play_clicked) # Click to play/pause
        # self.pauseButton.clicked.connect(self.on_pause_clicked)
        self.previousButton.clicked.connect(self.on_previous_clicked) # Click to previous song
        self.nextButton.clicked.connect(self.on_next_clicked) # Click to next song
        self.actionPreferences.triggered.connect(self.actionPreferencesClicked) # Open preferences menu
        self.actionScanLibraries.triggered.connect(self.scan_libraries) # Scan library
        self.actionClearDatabase.triggered.connect(self.clear_database) # Clear database
        ## tableView
        # self.tableView.clicked.connect(self.set_clicked_cell_filepath)
        self.tableView.doubleClicked.connect(self.play_audio_file) # Double click to play song
        self.tableView.viewport().installEventFilter(self) # for drag & drop functionality
        # self.tableView.model.layoutChanged()
        ### set column widths
        table_view_column_widths = str(self.config['table']['column_widths']).split(',')
        for i in range(self.tableView.model.columnCount()):
            self.tableView.setColumnWidth(i, int(table_view_column_widths[i]))
        
    def eventFilter(self, source, event):
        """Handles events"""
        # tableView (drag & drop)
        if (source is self.tableView.viewport() and
            (event.type() == QEvent.DragEnter or
             event.type() == QEvent.DragMove or
             event.type() == QEvent.Drop) and
            event.mimeData().hasUrls()):
            files = []
            if event.type() == QEvent.Drop:
                for url in event.mimeData().urls():
                    if url.isLocalFile():
                        files.append(url.path())
            self.tableView.add_files(files)
            event.accept()
            return True
        return super().eventFilter(source, event)
    
    def closeEvent(self, event):
        """Save settings when closing the application"""
        # MusicTable/tableView column widths
        list_of_column_widths = []
        for i in range(self.tableView.model.columnCount()):
            list_of_column_widths.append(str(self.tableView.columnWidth(i)))
        column_widths_as_string = ','.join(list_of_column_widths)
        self.config['table']['column_widths'] = column_widths_as_string
        
        
        # Save the config
        with open('config.ini', 'w') as configfile:
            self.config.write(configfile)
        super().closeEvent(event)
    
    def play_audio_file(self):
        """Start playback of selected track & moves playback slider"""
        self.current_song_metadata = self.tableView.get_current_song_metadata() # get metadata
        self.current_song_album_art = self.tableView.get_current_song_album_art()
        url = QUrl.fromLocalFile(self.tableView.get_current_song_filepath()) # read the file
        content = QMediaContent(url) # load the audio content
        self.player.setMedia(content) # what content to play
        self.player.play() # play
        self.move_slider() # mover
        
        # assign metadata
        # FIXME when i change tinytag to something else
        artist = self.current_song_metadata["artist"][0] if "artist" in self.current_song_metadata else None
        album = self.current_song_metadata["album"][0] if "album" in self.current_song_metadata else None
        title = self.current_song_metadata["title"][0]
        # edit labels
        self.artistLabel.setText(artist)
        self.albumLabel.setText(album)
        self.titleLabel.setText(title)
        # set album artwork
        self.load_album_art(self.current_song_album_art)
        

    def load_album_art(self, album_art_data):
        """Sets the album art for the currently playing track"""
        if self.current_song_album_art:
            # Create pixmap for album art
            pixmap = QPixmap()
            pixmap.loadFromData(self.current_song_album_art)
            self.album_art_scene.addPixmap(pixmap)
            # Reset the scene
            self.albumGraphicsView.setScene(None)
            # Set the scene
            self.albumGraphicsView.setScene(self.album_art_scene)
            # Put artwork in the scene, fit to graphics view widget
            self.albumGraphicsView.fitInView(self.album_art_scene.sceneRect(), Qt.KeepAspectRatio)
        
        
    def update_audio_visualization(self):
        """Handles upading points on the pyqtgraph visual"""
        self.clear_audio_visualization()
        self.y = self.audio_visualizer.get_amplitudes()
        self.x = [i for i in range(len(self.y))]
        self.PlotWidget.plot(self.x, self.y, fillLevel=0, fillBrush=mkBrush('b'))
        self.PlotWidget.show()
    
    def clear_audio_visualization(self):
        self.PlotWidget.clear()
    
    def move_slider(self):
        """Handles moving the playback slider"""
        if stopped:
            return
        else:
            # Update the slider
            if self.player.state() == QMediaPlayer.PlayingState:
                self.playbackSlider.setMinimum(0)
                self.playbackSlider.setMaximum(self.player.duration())
                slider_position = self.player.position()
                self.playbackSlider.setValue(slider_position)

                current_minutes, current_seconds = divmod(slider_position / 1000, 60)
                duration_minutes, duration_seconds = divmod(self.player.duration() / 1000, 60)

                self.startTimeLabel.setText(f"{int(current_minutes):02d}:{int(current_seconds):02d}")
                self.endTimeLabel.setText(f"{int(duration_minutes):02d}:{int(duration_seconds):02d}")
    
    def volume_changed(self):
        """Handles volume changes"""
        try:
            self.current_volume = self.volumeSlider.value()
            self.player.setVolume(self.current_volume)
        except Exception as e:
            print(f"Changing volume error: {e}")
        
    def on_play_clicked(self):
        """Updates the Play & Pause buttons when clicked"""
        if self.player.state() == QMediaPlayer.PlayingState:
            self.player.pause()
            self.playButton.setText("▶️")
        else:
            if self.player.state() == QMediaPlayer.PausedState:
                self.player.play()
                self.playButton.setText("⏸️")
            else:
                self.play_audio_file()
                self.playButton.setText("⏸️")
        
    def on_previous_clicked(self):
        """"""
        print('previous')
        
    def on_next_clicked(self):
        print('next')
        
    def actionPreferencesClicked(self):
        print('preferences')
        
    def scan_libraries(self):
        scan_for_music()
        self.tableView.fetch_library()
        
    def clear_database(self):
        initialize_library_database()
        self.tableView.fetch_library()
        
    def process_probe(self, buff):
        buff.startTime()
        self.update_audio_visualization()
        
    
        

if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    print(f'main.py app: {app}')
    qdarktheme.setup_theme()
    ui = ApplicationWindow(app)
    ui.show()
    sys.exit(app.exec_())