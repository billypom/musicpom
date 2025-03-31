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

    calculated_visual = QtCore.pyqtSignal(np.ndarray)

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
        self.sensitivity = 10

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
        v_sample = self.samples[
            start_index : start_index + sample_count
        ]  # samples to analyse


        # use FFTs to analyse frequency and amplitudes
        fourier = np.fft.fft(v_sample)
        freq = np.fft.fftfreq(fourier.size, d=self.sampling_window_length)
        amps = 2 / v_sample.size * np.abs(fourier)
        data = np.array([freq, amps]).T
        # print(freq * .05 * self.song.frame_rate)

        # NOTE:
        # given 520 hz sine wave
        # np.argmax(fourier) = 2374
        # freq[2374] * .05 * self.song.frame_rate = 520 :O omg! thats the hz value
        # x values = freq * self.song.frame_rate * self.sampling_window_length
        # print(freq * self.song.frame_rate * .05)

        point_range = 1 / self.resolution

        # Logarithmic frequency scaling
        min_freq = np.min(freq[freq > 0])  # minimum positive frequency
        # 20hz
        # print('min')
        # print(min_freq * .05 * self.song.frame_rate)
        max_freq = np.max(freq)  # maximum frequency
        # 20khz
        # print('max')
        # print(max_freq * .05 * self.song.frame_rate)
        log_freqs = np.logspace(np.log10(min_freq), np.log10(max_freq), self.resolution)

        point_samples = []

        if not data.size:
            return

        #for i, freq in enumerate(np.arange(0, 1, point_range), start=1):
        for i, log_freq in enumerate(log_freqs):
            # get the amps which are in between the frequency range
            #amps = data[(freq - point_range < data[:, 0]) & (data[:, 0] < freq)]
            amps = data[(log_freq - point_range < data[:, 0]) & (data[:, 0] < log_freq)]
            if not amps.size:
                point_samples.append(0)
            else:
                point_samples.append(
                    amps.max()
                    * (
                        (1 + self.sensitivity / 10 + (self.sensitivity - 1) / 10)
                        ** (i / 50)
                    )
                )

        # Add the point_samples to the self.points array, the reason we have a separate
        # array (self.bars) is so that we can fade out the previous amplitudes from
        # the past
        for n, amp in enumerate(point_samples):
            # amp *= 2

            if (
                self.points[n] > 0
                and amp < self.points[n]
                or self.player.state()
                in (self.player.PausedState, self.player.StoppedState)
            ):
                self.points[n] -= self.points[n] / 10  # fade out
            elif abs(self.points[n] - amp) > self.visual_delta_threshold:
                self.points[n] = amp
            if self.points[n] < 1:
                self.points[n] = 1e-5

        # interpolate points
        rs = gaussian_filter1d(self.points, sigma=1.5)

        # divide by the highest sample in the song to normalise the
        # amps in terms of decimals from 0 -> 1
        self.calculated_visual.emit(rs / self.max_sample)
        # self.calculated_visual.emit(rs)
        # print(rs)
        # print(rs/self.max_sample)

    def run(self):
        """Runs the animate function depending on the song."""
        while True:
            if self.start_animate:
                try:
                    self.calculate_amps()
                except ValueError:
                    self.calculated_visual.emit(np.zeros(self.resolution))
                    self.start_animate = False
            time.sleep(0.033)
