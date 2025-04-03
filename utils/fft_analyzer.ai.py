# Credit
# https://github.com/ravenkls/MilkPlayer/blob/master/audio/fft_analyser.py

import time
from PyQt5 import QtCore
from pydub import AudioSegment
import numpy as np
from scipy.ndimage.filters import gaussian_filter1d
from logging import debug, info


class FFTAnalyser(QtCore.QThread):
    """Analyses a song using FFTs."""

    calculatedVisual = QtCore.pyqtSignal(np.ndarray)
    calculatedVisualRs = QtCore.pyqtSignal(np.ndarray)

    def __init__(self, player, x_resolution):  # noqa: F821
        super().__init__()
        self.player = player
        self.reset_media()
        self.player.currentMediaChanged.connect(self.reset_media)

        self.resolution = x_resolution
        # this length is a number, in seconds, of how much audio is sampled to determine the frequencies
        # of the audio at a specific point in time
        # in this case, it takes 5% of the samples at some point in time
        self.sampling_window_length = 0.05
        self.visual_delta_threshold = 1000
        self.sensitivity = 0.2

    def reset_media(self):
        """Resets the media to the currently playing song."""
        audio_file = self.player.currentMedia().canonicalUrl().path()
        # if os.name == "nt" and audio_file.startswith("/"):
        #     audio_file = audio_file[1:]
        if audio_file:
            try:
                self.song = AudioSegment.from_file(audio_file).set_channels(1)
            except PermissionError:
                self.start_animate = False
            else:
                self.samples = np.array(self.song.get_array_of_samples())

                self.max_sample = self.samples.max()
                self.points = np.zeros(self.resolution)
                self.start_animate = True
        else:
            self.start_animate = False

    def calculate_amps(self):
        """Calculates the amplitudes used for visualising the media."""

        sample_count = int(self.song.frame_rate * self.sampling_window_length)
        start_index = int((self.player.position() / 1000) * self.song.frame_rate)
        # samples to analyse
        v_sample = self.samples[start_index : start_index + sample_count]

        # Use a window function to reduce spectral leakage
        window = np.hanning(len(v_sample))
        v_sample = v_sample * window

        # use FFTs to analyse frequency and amplitudes
        fourier = np.fft.fft(v_sample)
        freq = np.fft.fftfreq(fourier.size, d=1/self.song.frame_rate)
        amps = np.abs(fourier)[:len(fourier)//2]  # Only take positive frequencies
        freq = freq[:len(fourier)//2]  # Match frequencies to amplitudes
        
        # Define frequency bands (in Hz)
        bands = np.logspace(np.log10(10), np.log10(23000), self.resolution + 1)
        point_samples = np.zeros(self.resolution)
        
        # Calculate average amplitude for each frequency band
        for i in range(len(bands) - 1):
            mask = (freq >= bands[i]) & (freq < bands[i+1])
            if np.any(mask):
                point_samples[i] = np.mean(amps[mask])
        
        # Calculate RMS of the sample for dynamic sensitivity
        rms = np.sqrt(np.mean(np.square(v_sample)))
        rms_ratio = min(0.2, rms / (0.01 * self.max_sample))  # Smooth transition near silence
        
        # Normalize and apply sensitivity with RMS-based scaling
        if np.max(point_samples) > 0:
            point_samples = point_samples / np.max(point_samples)
            point_samples = point_samples * self.sensitivity * rms_ratio
        else:
            point_samples = np.zeros(self.resolution)

        # Update visualization points with decay
        for n in range(self.resolution):
            amp = point_samples[n]
            if self.player.state() in (self.player.PausedState, self.player.StoppedState):
                self.points[n] *= 0.95  # Fast decay when paused/stopped
            elif amp < self.points[n]:
                # More aggressive decay for very quiet signals
                decay_factor = 0.7 if rms_ratio < 0.1 else 0.9
                self.points[n] = max(amp, self.points[n] * decay_factor)
            else:
                self.points[n] = amp

        # Apply Gaussian smoothing
        rs = gaussian_filter1d(self.points, sigma=1)
        
        # Emit the smoothed data
        self.calculatedVisual.emit(rs)

    def run(self):
        """Runs the animate function depending on the song."""
        while True:
            if self.start_animate:
                try:
                    self.calculate_amps()
                except ValueError:
                    self.calculatedVisual.emit(np.zeros(self.resolution))
                    self.start_animate = False
            time.sleep(0.033)
