import numpy as np
import math
from PyQt5 import QtWidgets
from numpy.lib import math
from utils import FFTAnalyser


class AudioVisualizer(QtWidgets.QWidget):
    """Audio Visualizer component"""

    def __init__(self, media_player, x_resolution):
        super().__init__()
        self.media_player = media_player
        self.x_resolution = x_resolution
        self.fft_analyser = FFTAnalyser(self.media_player, self.x_resolution)
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
        epsilon = 1e-30
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
