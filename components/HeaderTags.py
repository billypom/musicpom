class HeaderTags:
    """
    Utility class to converting between different "standards" for tags (headers, id3, etc)
    """

    def __init__(self):
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
