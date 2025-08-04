from PyQt5.QtCore import (
    pyqtSignal,
    QObject,
    pyqtSlot,
    QRunnable,
)
from logging import error
from sys import exc_info
from traceback import format_exc, print_exc


class WorkerSignals(QObject):
    """
    How to use signals for a QRunnable class;
    Unlike most cases where signals are defined as class attributes directly in the class,
    here we define a class that inherits from QObject
    and define the signals as class attributes in that class.
    Then we can instantiate that class and use it as a signal object.
    """

    # 1)
    # Use a naming convention for signals that makes it clear that they are signals
    # and a corresponding naming convention for the slots that handle them.
    # For example signal_* and handle_*.
    # 2)
    # And try to make the signal content as small as possible. DO NOT pass large objects through signals, like
    # pandas DataFrames or numpy arrays. Instead, pass the minimum amount of information needed
    # (i.e. lists of filepaths)

    signal_started: pyqtSignal = pyqtSignal()
    signal_result: pyqtSignal = pyqtSignal(object)
    signal_finished: pyqtSignal = pyqtSignal()
    signal_progress: pyqtSignal = pyqtSignal(str)


class Worker(QRunnable):
    """
    This is the thread that is going to do the work so that the
    application doesn't freeze

    Inherits from QRunnable to handle worker thread setup, signals, and tear down
    :param callback: the function callback to run on this worker thread. Supplied
                    arg and kwargs will be passed through to the runner
    :type callback: function
    :param args: Arguments to pass to the callback function
    :param kwargs: Keywords to pass to the callback function
    """

    def __init__(self, fn, *args: object, **kwargs: object):
        super(Worker, self).__init__()
        # Store constructor arguments (re-used for processing)
        self.fn = fn
        self.args: object = args
        self.kwargs: object = kwargs
        self.signals: WorkerSignals = WorkerSignals()

        # Add a callback to our kwargs
        self.kwargs["progress_callback"] = self.signals.signal_progress

    @pyqtSlot()
    def run(self) -> None:  # type: ignore
        """
        This is where the work is done.
        MUST be called run() in order for QRunnable to work

        Initialize the runner function with passed args & kwargs
        """
        self.signals.signal_started.emit()
        try:
            result = self.fn(*self.args, **self.kwargs)
        except Exception:
            print_exc()
            exctype, value = exc_info()[:2]
            self.signals.signal_finished.emit((exctype, value, format_exc()))
            error(f"Worker failed: {exctype} | {value} | {format_exc()}")
        else:
            if result:
                self.signals.signal_finished.emit()
                self.signals.signal_result.emit(result)
            else:
                self.signals.signal_finished.emit()
