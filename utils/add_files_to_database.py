import DBA
import os
from logging import debug
from utils import get_id3_tags, id3_timestamp_to_datetime
from configparser import ConfigParser
from pathlib import Path
from appdirs import user_config_dir
import platform


def add_files_to_database(files, progress_callback=None):
    """
    Adds audio file(s) to the sqllite db "song" table
    Args:
        files: list() of fully qualified paths to audio file(s)
        progress_callback: emit data for user feedback
    Returns:
        True on success, else False
    """
    config = ConfigParser()
    cfg_file = (
        Path(user_config_dir(appname="musicpom", appauthor="billypom")) / "config.ini"
    )
    config.read(cfg_file)

    if not files:
        return False
    extensions = config.get("settings", "extensions").split(",")
    insert_data = []  # To store data for batch insert
    for filepath in files:
        if any(filepath.lower().endswith(ext) for ext in extensions):
            if progress_callback:
                progress_callback.emit(filepath)
            # if "microsoft-standard" in platform.uname().release:
            # filename = filepath.split(r"\\")[-1]
            # filepath = os.path.join(filepath)
            # else:
            filename = filepath.split("/")[-1]
            audio = get_id3_tags(filepath)

            try:
                title = audio["TIT2"].text[0]
            except KeyError:
                title = filename
            try:
                artist = audio["TPE1"].text[0]
            except KeyError:
                artist = ""
            try:
                album = audio["TALB"].text[0]
            except KeyError:
                album = ""
            try:
                track_number = audio["TRCK"].text[0]
            except KeyError:
                track_number = None
            try:
                genre = audio["TCON"].text[0]
            except KeyError:
                genre = ""
            try:
                date = id3_timestamp_to_datetime(audio["TDRC"].text[0])
            except KeyError:
                date = ""
            try:
                bitrate = audio["TBIT"].text[0]
            except KeyError:
                bitrate = ""

            # Append data tuple to insert_data list
            insert_data.append(
                (
                    filepath,
                    title,
                    album,
                    artist,
                    track_number,
                    genre,
                    filename.split(".")[-1],
                    date,
                    bitrate,
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
