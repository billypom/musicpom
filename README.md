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
- playlist autoexporting
- .wav, .ogg, .flac convertor
- playback modes (normal, repeat playlist, repeat 1 song, shuffle)
- autoplay next song in all modes
- allow spectrum analyzer to fall when playback stops or song is paused
- ability to delete playlist
- automatic "radio" based on artist or genre
- "installer" - put files in /opt? script to install and uninstall... eh
- .deb package?
