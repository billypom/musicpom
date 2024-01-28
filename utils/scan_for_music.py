import os
import DBA
from configparser import ConfigParser
from utils import get_id3_tags

config = ConfigParser()
config.read('config.ini')


def scan_for_music():
    root_dir = config.get('directories', 'library')
    extensions = config.get('settings', 'extensions').split(',')
    insert_data = []  # To store data for batch insert

    for dirpath, dirnames, filenames in os.walk(root_dir):
        for filename in filenames:
            if any(filename.lower().endswith(ext) for ext in extensions):
                filepath = os.path.join(dirpath, filename)
                audio = get_id3_tags(filepath)
                
                # Append data tuple to insert_data list
                insert_data.append((
                    filepath,
                    audio.title,
                    audio.album,
                    audio.artist,
                    audio.genre,
                    filename.split('.')[-1],
                    audio.year,
                    audio.bitrate
                ))

                # Check if batch size is reached
                if len(insert_data) >= 1000:
                    with DBA.DBAccess() as db:
                        db.executemany('INSERT OR IGNORE INTO library (filepath, title, album, artist, genre, codec, album_date, bitrate) VALUES (?, ?, ?, ?, ?, ?, ?, ?)', insert_data)
                    insert_data = []  # Reset the insert_data list

    # Insert any remaining data
    if insert_data:
        with DBA.DBAccess() as db:
            db.executemany('INSERT OR IGNORE INTO library (filepath, title, album, artist, genre, codec, album_date, bitrate) VALUES (?, ?, ?, ?, ?, ?, ?, ?)', insert_data)

                
# id int unsigned auto_increment,
# title varchar(255),
# album varchar(255),
# artist varchar(255),
# genre varchar(255),
# codec varchar(15),
# album_date date,
# bitrate int unsigned,
# date_added TIMESTAMP default CURRENT_TIMESTAMP,

# scan_for_music(config.get('directories', 'library1'))