from configparser import ConfigParser
from pathlib import Path
from appdirs import user_config_dir
from dataclasses import dataclass, asdict
from typing import Optional


@dataclass
class SQLiteMap:
    title: str | None = None
    artist: str | None = None
    album: str | None = None
    album_artist: str | None = None
    track_number: str | None = None
    genre: str | None = None
    length_seconds: str | None = None
    album_date: str | None = None
    codec: str | None = None
    filepath: str | None = None


"""
db names are called FIELDS (e.g., title, track_number, length_seconds)
gui names are called HEADERS (e.g., title, track, length, year)
id3 names are called TAGS (e.g., TIT2, TPE1, TALB)

is dataclasses rly worth it?
"""


class HeaderTags:
    """
    Utility class to converting between different "standards" for tags (headers, id3, etc)

    `db`: dict = "db name": "db name string"
    `gui`: dict = "db name": "gui string"
    `id3`: dict = "db name": "id3 tag string"
    `id3_keys`: dict = "id3 tag string": "db name"
    `editable_fields`: list = "list of db names that are user editable"
    `user_fields`: list = "list of db headers that the user has chosen to see in gui"
    """

    def __init__(self):
        cfg_file = (
            Path(user_config_dir(appname="musicpom", appauthor="billypom"))
            / "config.ini"
        )
        self.config = ConfigParser()
        self.config.read(cfg_file)
        print("header tag config")
        print(self.config)
        self.user_fields: list = str(self.config["table"]["columns"]).split(",")
        self.editable_fields: list = [
            "title",
            "artist",
            "album_artist",
            "album",
            "track_number",
            "genre",
            "album_date",
        ]
        self.fields = SQLiteMap()
        self.headers = SQLiteMap(
            title="title",
            artist="artist",
            album="album",
            album_artist="alb artist",
            track_number="track",
            genre="genre",
            codec="codec",
            length_seconds="length",
            album_date="year",
            filepath="path",
        )
        # self.id3 = SQLiteMap(
        #     title = "TIT2",
        #     artist = "TPE1",
        #     album = "TALB",
        #     album_artist = "TPE2",
        #     track_number = "TRCK",
        #     genre = "TCON",
        #     length_seconds = "TLEN",
        #     album_date = "TDRC",
        #     codec = None,
        #     filepath = None
        # )
        self.db: dict = {
            "title": "title",
            "artist": "artist",
            "album": "album",
            "album_artist": "album_artist",
            "track_number": "track_number",
            "genre": "genre",
            "codec": "codec",
            "length_seconds": "length_seconds",
            "album_date": "album_date",
            "filepath": "filepath",
        }
        self.gui: dict = {
            "title": "title",
            "artist": "artist",
            "album": "album",
            "album_artist": "alb artist",
            "track_number": "track",
            "genre": "genre",
            "codec": "codec",
            "length_seconds": "length",
            "album_date": "year",
            "filepath": "path",
        }
        self.id3: dict = {
            "title": "TIT2",
            "artist": "TPE1",
            "album_artist": "TPE2",
            "album": "TALB",
            "track_number": "TRCK",
            "genre": "TCON",
            "codec": None,
            "length_seconds": "TLEN",
            "album_date": "TDRC",
            "filepath": None,
        }
        # id3 is the key
        self.id3_keys: dict = {}
        for k, v in self.id3.items():
            if v is not None:
                self.id3_keys[v] = k

    def get_user_gui_headers(self) -> list:
        """Returns a list of headers for the GUI"""
        gui_headers = []
        for db, gui in asdict(self.headers).items():
            if db in self.user_fields:
                gui_headers.append(gui)
        return gui_headers
