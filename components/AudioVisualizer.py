import numpy as np
from PyQt5 import QtWidgets
from utils import FFTAnalyser


class AudioVisualizer(QtWidgets.QWidget):
    """_Audio Visualizer component_

    Args:
        QtWidgets (_type_): _description_

    Returns:
        _type_: _description_
    """

    def __init__(self, media_player, x_resolution):
        super().__init__()
        self.media_player = media_player
        self.x_resolution = x_resolution
        self.fft_analyser = FFTAnalyser(self.media_player, self.x_resolution)
        self.fft_analyser.calculated_visual.connect(self.set_amplitudes)
        self.fft_analyser.start()
        self.amps = np.array([])
        self._plot_item = None
        self._x_data = np.arange(self.x_resolution)

    def get_amplitudes(self):
        return self.amps

    def set_amplitudes(self, amps):
        self.amps = np.array(amps)
