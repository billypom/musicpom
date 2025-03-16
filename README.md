# MusicPom

PyQt5 music player for Linux inspired by MusicBee & iTunes

## Installation:
clone the repo
```bash
git clone https://github.com/billypom/musicpom
```

install system packages
```bash
sudo apt install ffmpeg, python3-pyqt5
```

create environment
```bash
cd musicpom
virtualenv venv
cd ..
cd musicpom
pip install -r requirements.txt
```

create ui.py from ui.ui
```bash
pyuic5 ui.ui -o ui.py
```

run
```bash
python3 main.py
```

## Todo:

- ~~right-click menu~~
- ~~editable lyrics window~~
- ~~batch metadata changer (red highlight fields that have differing info)~~
- ~~playlists~~
- playlist autoexporting
- delete songs from library (del key || right-click delete)
- .wav, .ogg, .flac convertor
- FIXME: dbaccess is instantiated for every track being reorganized
- automatic "radio" based on artist or genre
- search bar, full text search on song, artist, album
- when table is focused, start typing to match against the primary sort column
- "installer" - put files in /opt? script to install and uninstall
- .deb package?
