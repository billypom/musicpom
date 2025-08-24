import DBA
from logging import debug
from utils import get_tags, convert_id3_timestamp_to_datetime, id3_remap
from configparser import ConfigParser
from pathlib import Path
from appdirs import user_config_dir


def add_files_to_database(files: list[str], playlist_id: int | None = None, progress_callback=None) -> tuple[bool, dict[str, str]]:
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
    # yea
    if playlist_id:
        pass

    config = ConfigParser()
    cfg_file = (
        Path(user_config_dir(appname="musicpom", appauthor="billypom")) / "config.ini"
    )
    _ = config.read(cfg_file)
    if not files:
        return False, {"Failure": "All operations failed in add_files_to_database()"}
    failed_dict: dict[str, str] = {}
    insert_data: list[tuple[
    str, 
    str | int | None, 
    str | int | None, 
    str | int | None, 
    str | int | None, 
    str | int | None, 
    str, 
    str | int | None, 
    str | int | None, 
    str | int | None]] = []  # To store data for batch insert
    for filepath in files:
        if progress_callback:
            progress_callback.emit(filepath)
        filename = filepath.split("/")[-1]
        tags, fail_reason = get_tags(filepath)
        if fail_reason:
            # if we fail to get audio tags, skip to next song
            failed_dict[filepath] = fail_reason
            continue
        # remap tags from ID3 to database tags
        audio: dict[str, str | int | None] = id3_remap(tags)
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
                audio["length"],
            )
        )
        # Check if batch size is reached
        if len(insert_data) >= 1000:
            debug(f"inserting a LOT of songs: {len(insert_data)}")
            with DBA.DBAccess() as db:
                result = db.executemany(
                    "INSERT OR IGNORE INTO song (filepath, title, album, artist, track_number, genre, codec, album_date, bitrate, length_seconds) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?) RETURNING id",
                    insert_data,
                )
            debug('IMPORTANT')
            debug(f'batch insert result: {result}')
            debug('IMPORTANT')
            insert_data = []  # Reset the insert_data list
    # Insert any remaining data after reading every file
    if insert_data:
        with DBA.DBAccess() as db:
            result = db.executemany(
                "INSERT OR IGNORE INTO song (filepath, title, album, artist, track_number, genre, codec, album_date, bitrate, length_seconds) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?) RETURNING id",
                insert_data,
            )
        debug('IMPORTANT')
        debug(f'batch insert result: {result}')
        debug('IMPORTANT')
    return True, failed_dict
