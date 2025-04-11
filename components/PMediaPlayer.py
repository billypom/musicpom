import gi
import os
from gi.repository import Gst, GObject

gi.require_version("Gst", "1.0")

Gst.init(None)


class PMediaPlayer:
    def __init__(self):
        self.pipeline = Gst.ElementFactory.make("playbin", "player")
        self.uri = None
        self.rate = 1.0

        # Set initial audio filter
        self.pipeline.set_property("audio-filter", self._build_pitch_filter(self.rate))

    def setSource(self, file_path: str):
        if not os.path.isfile(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        self.uri = Gst.filename_to_uri(file_path)
        self.pipeline.set_property("uri", self.uri)

    def play(self):
        if not self.uri:
            raise RuntimeError("No media source set.")
        self.pipeline.set_state(Gst.State.PLAYING)

    def pause(self):
        self.pipeline.set_state(Gst.State.PAUSED)

    def stop(self):
        self.pipeline.set_state(Gst.State.NULL)

    def setPlaybackRate(self, rate: float):
        if rate <= 0:
            raise ValueError("Playback rate must be greater than 0.")

        self.rate = rate
        # Fully rebuild the pitch filter with new rate
        self.pipeline.set_state(Gst.State.NULL)
        self.pipeline.set_property("audio-filter", self._build_pitch_filter(rate))
        if self.uri:
            self.pipeline.set_property("uri", self.uri)
        self.pipeline.set_state(Gst.State.PLAYING)

    def _build_pitch_filter(self, rate: float):
        pitch = Gst.ElementFactory.make("pitch", "pitch")
        pitch.set_property("pitch", 1.0)  # Keep pitch constant
        pitch.set_property("rate", rate)

        bin = Gst.Bin.new("filter_bin")
        conv = Gst.ElementFactory.make("audioconvert", "conv")
        resample = Gst.ElementFactory.make("audioresample", "resample")

        bin.add(conv)
        bin.add(resample)
        bin.add(pitch)
        conv.link(resample)
        resample.link(pitch)

        # Ghost pads
        sink_pad = conv.get_static_pad("sink")
        src_pad = pitch.get_static_pad("src")
        bin.add_pad(Gst.GhostPad.new("sink", sink_pad))
        bin.add_pad(Gst.GhostPad.new("src", src_pad))

        return bin

    def cleanup(self):
        self.pipeline.set_state(Gst.State.NULL)


# Example usage:
if __name__ == "__main__":
    import time

    GObject.threads_init()
    player = PMediaPlayer()

    try:
        player.setSource("/path/to/your/audio/file.mp3")
        player.play()
        time.sleep(2)

        print("Speeding up to 1.5x...")
        player.setPlaybackRate(1.5)
        time.sleep(5)

        print("Slowing down to 0.75x...")
        player.setPlaybackRate(0.75)
        time.sleep(5)

        print("Pausing...")
        player.pause()
        time.sleep(2)

        print("Resuming...")
        player.play()
        time.sleep(5)

    finally:
        player.cleanup()
