# musicpom

PyQt5 music library manager and audio player for Linux, inspired by MusicBee & iTunes

## Installation:
___
clone the repo
```bash
# github - not up to date, need to mirror this eventually
git clone https://github.com/billypom/musicpom
# gitea - need to move to forgejo eventually
git clone https://git.billypom.com/billy/musicpom.git
```

install system packages
```bash
sudo apt install ffmpeg python3-pyqt5 virtualenv
```

create environment
```bash
cd musicpom
virtualenv venv
cd ..
cd musicpom
pip install -r requirements.txt
```

run
```bash
python3 main.py
```
## Editing the UI
i use Qt Designer, so download that if you want to try editing the UI. good luck
___
```bash
# generate python ui from qt designer .ui file
pyuic5 ui.ui -o ui.py
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
- playlist m3u files
- playlist autoexporting
- fix table headers being resized and going out window bounds
- delete songs from library (del key || right-click delete)
- .wav, .ogg, .flac convertor
- FIXME: dbaccess is instantiated for every track being reorganized
- automatic "radio" based on artist or genre
- search bar, full text search on song, artist, album
- when table is focused, start typing to match against the primary sort column
- improve audio visualizer - see Renoise
- "installer" - put files in /opt? script to install and uninstall... eh
- .deb package?
