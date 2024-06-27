import DBA
from configparser import ConfigParser
from utils import get_id3_tags, id3_timestamp_to_datetime

config = ConfigParser()
config.read("config.ini")


def add_files_to_library(files):
    """Adds audio file(s) to the sqllite db
    files = list() of fully qualified paths to audio file(s)
    Returns a list of dictionaries of metadata
    """
    if not files:
        return []
    extensions = config.get("settings", "extensions").split(",")
    insert_data = []  # To store data for batch insert
    for filepath in files:
        if any(filepath.lower().endswith(ext) for ext in extensions):
            filename = filepath.split("/")[-1]
            audio = get_id3_tags(filepath)
            # print("add_files_to_library audio:")
            # print(audio)

            # Skip if no title is found (but should never happen
            if "TIT2" not in audio:
                continue
            title = audio["TIT2"].text[0]
            try:
                artist = audio["TPE1"].text[0]
            except KeyError:
                artist = ""
            try:
                album = audio["TALB"].text[0]
            except KeyError:
                album = ""
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
                    genre,
                    filename.split(".")[-1],
                    date,
                    bitrate,
                )
            )
            # Check if batch size is reached
            if len(insert_data) >= 1000:
                with DBA.DBAccess() as db:
                    db.executemany(
                        "INSERT OR IGNORE INTO song (filepath, title, album, artist, genre, codec, album_date, bitrate) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                        insert_data,
                    )
                insert_data = []  # Reset the insert_data list
        # Insert any remaining data
        if insert_data:
            with DBA.DBAccess() as db:
                db.executemany(
                    "INSERT OR IGNORE INTO song (filepath, title, album, artist, genre, codec, album_date, bitrate) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
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
