import DBA
from configparser import ConfigParser
from utils import get_id3_tags

config = ConfigParser()
config.read("config.ini")


def add_files_to_library(files):
    """Adds audio file(s) to the sqllite db
    `files` | list() | List of fully qualified paths to audio file(s)
    Returns a count of records added
    """
    print(f'utils | adding files to library: {files}')
    extensions = config.get('settings', 'extensions').split(',')
    insert_data = [] # To store data for batch insert
    for file in files:
        if any(file.lower().endswith(ext) for ext in extensions):
            filename = file.split("/")[-1]
            audio = get_id3_tags(file)
            # Append data tuple to insert_data list
            insert_data.append(
                (
                    file,
                    audio.title,
                    audio.album,
                    audio.artist,
                    audio.genre,
                    filename.split(".")[-1],
                    audio.year,
                    audio.bitrate,
                )
            )

            # Check if batch size is reached
            if len(insert_data) >= 1000:
                with DBA.DBAccess() as db:
                    db.executemany('INSERT OR IGNORE INTO library (filepath, title, album, artist, genre, codec, album_date, bitrate) VALUES (?, ?, ?, ?, ?, ?, ?, ?)', insert_data)
                insert_data = []  # Reset the insert_data list

        # Insert any remaining data
        if insert_data:
            with DBA.DBAccess() as db:
                db.executemany('INSERT OR IGNORE INTO library (filepath, title, album, artist, genre, codec, album_date, bitrate) VALUES (?, ?, ?, ?, ?, ?, ?, ?)', insert_data)
    return True


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
