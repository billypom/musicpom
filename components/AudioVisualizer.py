from PyQt5.QtCore import QTimer
from PyQt5.QtMultimedia import QAudioProbe, QMediaPlayer
import numpy as np
from PyQt5 import QtWidgets
from pyqtgraph.Qt.QtWidgets import QWidget
from utils import FFTAnalyser
from pyqtgraph import mkBrush


class AudioVisualizer(QtWidgets.QWidget):
    """Audio Visualizer component"""

    def __init__(self, player, probe, PlotWidget):
        super().__init__()
        self.player: QMediaPlayer = player
        self.probe: QAudioProbe = probe
        self.PlotWidget: QWidget = PlotWidget
        self.x_resolution = 100
        self.fft_analyser = FFTAnalyser(self.player, self.x_resolution)
        self.fft_analyser.calculatedVisual.connect(self.set_amplitudes)
        self.fft_analyser.calculatedVisualRs.connect(self.set_rs)
        self.fft_analyser.start()
        self.amps = np.array([])
        self._plot_item = None
        self._x_data = np.arange(self.x_resolution)
        self.use_decibels = True  # Set to True to use decibel scale

        # Generate logarithmic frequency scale (20Hz - 20kHz)
        self.min_freq = 20
        self.max_freq = 23000
        self.frequency_values = np.logspace(
            np.log10(self.min_freq), np.log10(self.max_freq), self.x_resolution
        )

        # Audio probe for processing audio signal in real time
        self.probe.setSource(self.player)
        self.probe.audioBufferProbed.connect(self.process_probe)

        self.is_playing = False
        self.visualizer_timer = QTimer(self)
        self.visualizer_timer.setInterval(20)  # Update every 100ms (adjust as needed)
        self.visualizer_timer.timeout.connect(self.update_audio_visualization)

        # Graphics plot
        # Make sure PlotWidget doesn't exceed album art height
        # Adjust to leave room for playback controls
        self.PlotWidget.setFixedHeight(225)
        # x range
        self.PlotWidget.setXRange(
            0, self.get_x_resolution(), padding=0
        )
        # y axis range for decibals (-96db to 0db)
        self.PlotWidget.setYRange(-96, 0, padding=0)
        # Logarithmic x-axis for frequency display
        self.PlotWidget.setLogMode(x=False, y=False)
        self.PlotWidget.setMouseEnabled(x=False, y=False)
        self.PlotWidget.showGrid(x=True, y=True)
        # Performance optimizations
        self.PlotWidget.setAntialiasing(False)
        self.PlotWidget.setDownsampling(auto=True, mode="peak")
        self.PlotWidget.setClipToView(True)

        # Add tick marks for common decibel values (expanded range)
        y_ticks = [
            (-84, "-84dB"),
            (-60, "-60dB"),
            (-36, "-36dB"),
            (-12, "-12dB"),
            (0, "0dB"),
        ]
        self.PlotWidget.getAxis("left").setTicks([y_ticks])

        # Add frequency ticks on x-axis
        freq_ticks = self.get_frequency_ticks()
        self.PlotWidget.getAxis("bottom").setTicks([freq_ticks])

    def get_x_resolution(self):
        """Returns the resolution for the graphics plot"""
        return self.x_resolution

    def get_frequency_ticks(self):
        """Returns frequency ticks for x-axis display

        Returns:
            list: List of tuples with (position, label) for each tick
        """
        # Standard frequency bands for audio visualization
        standard_freqs = [20, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000]

        # Map frequencies to x-axis positions
        ticks = []
        for freq in standard_freqs:
            # Find closest index to this frequency
            idx = np.argmin(np.abs(self.frequency_values - freq))
            # Format labels: Hz for <1000, kHz for >=1000
            if freq < 1000:
                label = f"{freq}Hz"
            else:
                label = f"{freq / 1000:.0f}kHz"
            ticks.append((idx, label))

        return ticks

    def get_frequencies(self):
        """Return the frequency values for x-axis"""
        return self.frequency_values

    def get_amplitudes(self):
        return self.amps

    def get_rs(self):
        return self.rs

    def get_decibels(self):
        """Convert amplitude values to decibel scale

        Formula: dB = 20 * log10(amplitude)
        For normalized amplitude values, this gives a range of approx -96dB to 0dB
        With a noise floor cutoff at around -96dB (for very small values)
        """
        # Avoid log(0) by adding a small epsilon
        epsilon = 1e-7
        amplitudes = np.maximum(self.amps, epsilon)
        # Convert to decibels (20*log10 is the standard formula for amplitude to dB)
        db_values = 20 * np.log10(amplitudes)
        # Clip very low values to have a reasonable floor (e.g. -96dB)
        db_values = np.maximum(db_values, -96)
        return db_values

    def set_rs(self, rs):
        self.rs = np.array(rs)

    def set_amplitudes(self, amps):
        """
        This function is hooked into the calculatedVisual signal from FFTAnalyzer() object
        Amps are assigned here, based on values passed by the signal
        """
        # self.amps = np.maximum(np.array(amps), 1e-12)  # Set a very small threshold
        # print(self.amps)
        self.amps = np.array(amps)


    def process_probe(self, buff):
        """Audio visualizer buffer processing"""
        # buff.startTime() # what is this? why need? dont need...
        self.is_playing = True

        # If music is playing, reset the timer
        if not self.visualizer_timer.isActive():
            self.visualizer_timer.start()

    def update_audio_visualization(self):
        """Update the visualization for audio signal"""
        if not self.is_playing:
            # If music stopped, continue updating visualizer for a few seconds
            self.visualizer_timer.stop()  # Stop the timer once it's done

        # Assuming y is the decibel data
        y = self.get_decibels()

        if len(y) == 0:
            return

        # Clear the previous plot
        self.PlotWidget.clear()

        # Plot new values
        self._plot_item = self.PlotWidget.plot(
            self._x_data,
            y,
            pen="b",
            fillLevel=-96 if self.use_decibels else 0,
            fillBrush=mkBrush("b"),
        )

        # If the visualizer is done, stop updating
        if all(val == -96 for val in y):
            self.is_playing = False
            self.visualizer_timer.stop()

    def clear_audio_visualization(self) -> None:
        self.PlotWidget.clear()
        self._plot_item = None
