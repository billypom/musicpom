# MusicPom

PyQt5 music player for Linux inspired by MusicBee & iTunes

## Installation:
clone the repo
```
git clone https://github.com/billypom/musicpom
```
install system packages
```
sudo apt install ffmpeg
sudo apt install python3-pyqt5
```
create environment
```
cd musicpom
virtualenv venv
cd ..
cd musicpom
pip install -r requirements.txt
```
run the program
```
python3 main.py
```

## Todo:

- [x] right-click menu
- [x] editable lyrics window
- [ ] playlists
- [ ] delete songs from library (del key || right-click delete)
- [ ] .wav, .ogg, .flac convertor
- [ ] batch metadata changer (red text on fields that have differing info)
