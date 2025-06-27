# musicpom

PyQt5 music library manager and audio player for Linux, inspired by MusicBee & iTunes

## Installation:
___
clone the repo

install system packages
```bash
sudo apt install ffmpeg python3-pyqt5 virtualenv
```

additional packages needed for wsl
```bash
sudo apt install gstreamer1.0-plugins-good
```

create environment
```bash
cd musicpom
virtualenv venv
source venv/bin/activate
pip install -r requirements.txt
```

run
```bash
python3 main.py
```
## Editing the UI
___
i use Qt Designer, so download that if you want to try editing the UI. good luck
```bash
# generate python ui from qt designer .ui file
pyuic5 ui.ui -o ui.py
# shell script to do the same thing
./create_ui.sh
```
## Config
___
config file and databases (libraries) are stored in user home directory `.config` folder
```bash
cd ~/.config/musicpom
# you should see config file and db folder
config.ini db/
```

## Todo:

- ~~right-click menu~~
- ~~editable lyrics window~~
- ~~batch metadata changer (red highlight fields that have differing info)~~
- ~~playlists~~
- ~~delete songs from library (del key || right-click delete)~~
- ~~improve audio visualizer - logarithmic x-axis ISO octave bands - see Renoise~~
- ~~when table is focused, start typing to match against the primary sort column~~
- ~~remember last window size~~
- ~~automatically fix broken config before loading app (new config options added)~~
- ~~allow spectrum analyzer to fall when playback stops or song is paused~~
- ~~ability to delete playlist~~
- ~~jump to currently playing song~~
##### QMediaPlaylist
https://doc.qt.io/qtforpython-5/PySide2/QtMultimedia/QMediaPlaylist.html#PySide2.QtMultimedia.PySide2.QtMultimedia.QMediaPlaylist
- playback modes (normal, repeat playlist, repeat 1 song, shuffle)
> Use `PySide2.QtMultimedia.QMediaPlaylist.PlaybackMode` ?
> Use `PySide2.QtMultimedia.QMediaPlaylist.shuffle()` ?
- autoplay next song in all modes
> Use `PySide2.QtMultimedia.QMediaPlaylist.next()` after implementing playlist?
- playback rate audio quality fix?
> https://doc.qt.io/qtforpython-5/PySide2/QtMultimedia/QAudioDecoder.html#qaudiodecoder
> Since Qt 5.12.2, the url scheme gst-pipeline provides custom pipelines for the GStreamer backend.
```py
player = new QMediaPlayer;
player->setMedia(QUrl("gst-pipeline: videotestsrc ! autovideosink"));
player->play();
```
QMultimedia.EncodingMode / Encoding quality...
##### misc
- database playlist autoexporting
- .wav, .ogg, .flac convertor
- automatic "radio" (based on artist, genre, etc?)
- title artist album labels - fit to window size
