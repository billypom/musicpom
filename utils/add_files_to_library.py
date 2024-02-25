import DBA
from configparser import ConfigParser
from utils import get_id3_tags
from utils import safe_get

config = ConfigParser()
config.read("config.ini")


def add_files_to_library(files):
    """Adds audio file(s) to the sqllite db
    
    files | list() of fully qualified paths to audio file(s)
    
    Returns true if any files were added
    """
    if not files:
        return False
    print(f"utils | adding files to library: {files}")
    extensions = config.get("settings", "extensions").split(",")
    insert_data = []  # To store data for batch insert
    for filepath in files:
        if any(filepath.lower().endswith(ext) for ext in extensions):
            filename = filepath.split("/")[-1]
            audio = get_id3_tags(filepath)
            if "title" not in audio:
                return False
            # Append data tuple to insert_data list
            insert_data.append(
                (
                    filepath,
                    safe_get(audio, "title", [])[0],
                    safe_get(audio, "album", [])[0] if "album" in audio else None,
                    safe_get(audio, "artist", [])[0] if "artist" in audio else None,
                    ",".join(safe_get(audio, "genre", []))
                    if "genre" in audio
                    else None,
                    filename.split(".")[-1],
                    safe_get(audio, "date", [])[0] if "date" in audio else None,
                    safe_get(audio, "bitrate", [])[0] if "birate" in audio else None,
                )
            )

            # Check if batch size is reached
            if len(insert_data) >= 1000:
                with DBA.DBAccess() as db:
                    db.executemany(
                        "INSERT OR IGNORE INTO library (filepath, title, album, artist, genre, codec, album_date, bitrate) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                        insert_data,
                    )
                insert_data = []  # Reset the insert_data list

        # Insert any remaining data
        if insert_data:
            with DBA.DBAccess() as db:
                db.executemany(
                    "INSERT OR IGNORE INTO library (filepath, title, album, artist, genre, codec, album_date, bitrate) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
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
