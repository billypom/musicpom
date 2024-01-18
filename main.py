import DBA
from ui import Ui_MainWindow
from PyQt5.QtWidgets import QMainWindow, QApplication
import qdarktheme
from PyQt5.QtCore import QUrl, QTimer, QFile, QTextStream
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent, QAudioProbe
from PyQt5.QtGui import QStandardItem, QStandardItemModel
from utils import scan_for_music
from utils import initialize_library_database
from utils import AudioVisualizer
from pyqtgraph import mkBrush


class ApplicationWindow(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super(ApplicationWindow, self).__init__()
        self.setupUi(self)
        self.setWindowTitle('MusicPom')
        self.selected_song_filepath = None
        self.current_song_filepath = None
        
        global stopped
        stopped = False
        
        # Initialization
        self.player = QMediaPlayer(None, QMediaPlayer.VideoSurface) # Audio player
        self.probe = QAudioProbe() # Get audio data
        self.timer = QTimer(self) # Audio timing things
        self.model = QStandardItemModel() # Table library listing
        self.audio_visualizer = AudioVisualizer(self.player)
        self.current_volume = 50
        self.player.setVolume(self.current_volume)
        
        # Audio probe for processing audio signal in real time
        # Provides faster updates than move_slider
        self.probe.setSource(self.player)
        self.probe.audioBufferProbed.connect(self.process_probe)
        
        # Probably move all the table logic to its own class
        # Promote the wigdet to my custom class from utils
        # inherit from QTableView
        # then i can handle click events for editing metadata in a class
        
        # current song should also be its own class
        # selected song should be its own class too...
        
        #  ______________
        # |              |
        # | Table making |
        # |              |
        # |______________|
        
        # Fetch library data
        with DBA.DBAccess() as db:
            data = db.query('SELECT title, artist, album, genre, codec, album_date, filepath FROM library;', ())
        headers = ['title', 'artist', 'album', 'genre', 'codec', 'year', 'path']
        self.model.setHorizontalHeaderLabels(headers)
        for row_data in data: # Populate the model
            items = [QStandardItem(str(item)) for item in row_data]
            self.model.appendRow(items)
        # Set the model to the tableView
        self.tableView.setModel(self.model)
        # self.tableView.resizeColumnsToContents()
        
        
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
        self.playbackSlider.sliderMoved[int].connect(lambda: self.player.setPosition(self.playbackSlider.value()))
        self.volumeSlider.sliderMoved[int].connect(lambda: self.volume_changed())
        self.playButton.clicked.connect(self.on_play_clicked)
        # self.pauseButton.clicked.connect(self.on_pause_clicked)
        self.previousButton.clicked.connect(self.on_previous_clicked)
        self.nextButton.clicked.connect(self.on_next_clicked)
        self.tableView.clicked.connect(self.set_clicked_cell_filepath)
        self.actionPreferences.triggered.connect(self.actionPreferencesClicked)
        self.actionScanLibraries.triggered.connect(self.scan_libraries)
        self.actionClearDatabase.triggered.connect(initialize_library_database)
    
    def play_audio_file(self):
        """Start playback of selected track & move playback slider"""
        self.current_song_filepath = self.selected_song_filepath
        url = QUrl.fromLocalFile(self.current_song_filepath) # read the file
        content = QMediaContent(url) # load the audio content
        
        self.player.setMedia(content) # what content to play
        self.player.play() # play
        self.move_slider() # mover
        
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

    def set_clicked_cell_filepath(self):
        """Sets the filepath of the currently selected song"""
        self.selected_song_filepath = self.tableView.currentIndex().siblingAtColumn(6).data()
        
    def on_previous_clicked(self):
        """"""
        print('previous')
        
    def on_next_clicked(self):
        print('next')
        
    def actionPreferencesClicked(self):
        print('preferences')
        
    def scan_libraries(self):
        scan_for_music()
        # refresh datatable
        
    def process_probe(self, buff):
        buff.startTime()
        self.update_audio_visualization()
        
    
        

if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    qdarktheme.setup_theme()
    ui = ApplicationWindow()
    ui.show()
    sys.exit(app.exec_())