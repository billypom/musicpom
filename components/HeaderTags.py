from configparser import ConfigParser
from pathlib import Path
from appdirs import user_config_dir


class HeaderTags:
    """
    Utility class to converting between different "standards" for tags (headers, id3, etc)

    `db`: dict = "db name": "db name string"
    `gui`: dict = "db name": "gui string"
    `id3`: dict = "db name": "id3 tag string"
    `id3_keys`: dict = "id3 tag string": "db name"
    `editable_db_tags`: list = "list of db names that are user editable"
    `user_headers`: list = "list of db headers that the user has chosen to see in gui"
    """

    def __init__(self):
        cfg_file = (
            Path(user_config_dir(appname="musicpom", appauthor="billypom"))
            / "config.ini"
        )
        self.config = ConfigParser()
        self.config.read(cfg_file)
        self.user_headers = str(self.config["table"]["columns"]).split(",")
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

        self.editable_db_tags: list = [
            "title",
            "artist",
            "album_artist",
            "album",
            "track_number",
            "genre",
            "album_date",
        ]

    def get_user_gui_headers(self) -> list:
        """Returns a list of headers for the GUI"""
        gui_headers = []
        for db, gui in self.gui.items():
            if db in self.user_headers:
                gui_headers.append(gui)
        return gui_headers
