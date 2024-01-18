from PyQt5 import QtWidgets, QtGui, QtCore
import numpy as np

from .fft_analyser import FFTAnalyser

class AudioVisualizer(QtWidgets.QWidget):

    def __init__(self, media_player):
        super().__init__()
        self.media_player = media_player
        self.fft_analyser = FFTAnalyser(self.media_player)
        self.fft_analyser.calculated_visual.connect(self.set_amplitudes)
        self.fft_analyser.start()
        self.amps = np.array([])
    
    def get_amplitudes(self):
        return self.amps

    def set_amplitudes(self, amps):
        self.amps = np.array(amps)