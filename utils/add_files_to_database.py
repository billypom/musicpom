from PyQt5.QtWidgets import QMessageBox
from mutagen.id3 import ID3
import DBA
from logging import debug
from utils import get_id3_tags, convert_id3_timestamp_to_datetime, id3_remap
from configparser import ConfigParser
from pathlib import Path
from appdirs import user_config_dir


def add_files_to_database(files, progress_callback=None):
    """
    Adds audio file(s) to the sqllite db "song" table
    Args:
        files: list() of fully qualified paths to audio file(s)
        progress_callback: emit data for user feedback

    Returns a tuple where the first value is the success state
    and the second value is a list of failed to add items
    ```
    (True, {"filename.mp3":"failed because i said so"})
    ```
    """
    config = ConfigParser()
    cfg_file = (
        Path(user_config_dir(appname="musicpom", appauthor="billypom")) / "config.ini"
    )
    config.read(cfg_file)
    if not files:
        return False, {"Failure": "All operations failed in add_files_to_database()"}
    extensions = config.get("settings", "extensions").split(",")
    failed_dict = {}
    insert_data = []  # To store data for batch insert
    for filepath in files:
        if any(filepath.lower().endswith(ext) for ext in extensions):
            if progress_callback:
                progress_callback.emit(filepath)
            filename = filepath.split("/")[-1]

            tags, details = get_id3_tags(filepath)
            if details:
                failed_dict[filepath] = details
                continue
            audio = id3_remap(tags)

            # Append data tuple to insert_data list
            insert_data.append(
                (
                    filepath,
                    audio["title"],
                    audio["album"],
                    audio["artist"],
                    audio["track_number"],
                    audio["genre"],
                    filename.split(".")[-1],
                    audio["date"],
                    audio["bitrate"],
                )
            )
            # Check if batch size is reached
            if len(insert_data) >= 1000:
                debug(f"inserting a LOT of songs: {len(insert_data)}")
                with DBA.DBAccess() as db:
                    db.executemany(
                        "INSERT OR IGNORE INTO song (filepath, title, album, artist, track_number, genre, codec, album_date, bitrate) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                        insert_data,
                    )
                insert_data = []  # Reset the insert_data list
            else:
                # continue adding files if we havent reached big length
                continue
    # Insert any remaining data
    debug("i check for insert data")
    if insert_data:
        debug(f"inserting some songs: {len(insert_data)}")
        with DBA.DBAccess() as db:
            db.executemany(
                "INSERT OR IGNORE INTO song (filepath, title, album, artist, track_number, genre, codec, album_date, bitrate) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                insert_data,
            )
    return True, failed_dict


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
