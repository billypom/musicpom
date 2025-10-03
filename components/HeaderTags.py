from configparser import ConfigParser
from pathlib import Path
from typing import Optional
from appdirs import user_config_dir
from dataclasses import dataclass, asdict
from mutagen.id3._frames import (
    TIT2,
    TPE1,
    TALB,
    TRCK,
    TDRC,
    # TYER,
    TLEN,
    TCON,
    TPOS,
    COMM,
    TPE2,
    TCOM,
    TPE3,
    TPE4,
    TCOP,
    WOAR,
    USLT,
    APIC,
    TENC,
    TBPM,
    TKEY,
    # TDAT,
    TIME,
    TSSE,
    TOPE,
    TEXT,
    TOLY,
    TORY,
    TPUB,
    WCOM,
    WCOP,
    WOAS,
    WORS,
    WPAY,
    WPUB,
)


mutagen_id3_tag_mapping = {
    "title": TIT2,  # Title/song name/content description
    "artist": TPE1,  # Lead performer(s)/Soloist(s)
    "album": TALB,  # Album/Movie/Show title
    "album_artist": TPE2,  # Band/orchestra/accompaniment
    "genre": TCON,  # Content type
    "album_date": TDRC,
    # "year": TYER,  # Year of recording
    # "date": TDAT,  # Date
    "lyrics": USLT,  # Unsynchronized lyric/text transcription
    "track_number": TRCK,  # Track number/Position in set
    "album_cover": APIC,  # Attached picture
    "composer": TCOM,  # Composer
    "conductor": TPE3,  # Conductor/performer refinement
    "remixed_by": TPE4,  # Interpreted, remixed, or otherwise modified by
    "part_of_a_set": TPOS,  # Part of a set
    "comments": COMM,  # Comments
    "copyright": TCOP,  # Copyright message
    "url_artist": WOAR,  # Official artist/performer webpage
    "encoded_by": TENC,  # Encoded by
    "bpm": TBPM,  # BPM (beats per minute)
    "initial_key": TKEY,  # Initial key
    "time": TIME,  # Time
    "encoding_settings": TSSE,  # Software/Hardware and settings used for encoding
    "original_artist": TOPE,  # Original artist(s)/performer(s)
    "lyricist": TEXT,  # Lyricist/Text writer
    "original_lyricist": TOLY,  # Original lyricist(s)/text writer(s)
    "original_release_year": TORY,  # Original release year
    "publisher": TPUB,  # Publisher
    "commercial_info": WCOM,  # Commercial information
    "copyright_info": WCOP,  # Copyright information
    "official_audio_source_url": WOAS,  # Official audio source webpage
    "official_internet_radio_station_homepage": WORS,  # Official Internet radio station homepage
    "payment_url": WPAY,  # Payment (URL)
    "publishers_official_webpage": WPUB,  # Publishers official webpage
}


@dataclass
class SQLiteMap:
    title: str | TIT2 | None = None
    artist: str | TPE1 | None = None
    album: str | TALB | None = None
    album_artist: str | TPE2 | None = None
    track_number: str | TRCK | None = None
    genre: str | TCON | None = None
    length_ms: str | TLEN | None = None
    album_date: str | TDRC | None = None
    codec: str | None = None
    filepath: str | None = None
    bitrate: str | None = None
    # lyrics: str | USLT | None = None
    # album_art: str | APIC | None = None

@dataclass
class ID3Field:
    db: str                             # e.g., "title"
    gui: str                            # e.g., "Title"
    frame_class: Optional[type] = None  # e.g., TPE1
    frame_id: Optional[str] = None      # e.g., "TPE1"


class HeaderTags2:
    def __init__(self):
        self.headers = [
            ID3Field(frame_class=TIT2, frame_id="TIT2", db="title", gui="Title"),
            ID3Field(frame_class=TPE1, frame_id="TPE1", db="artist", gui="Artist"),
            ID3Field(frame_class=TALB, frame_id="TALB", db="album", gui="Album"),
            ID3Field(frame_class=TPE2, frame_id="TPE2", db="album_artist", gui="Album Artist"),
            ID3Field(frame_class=TRCK, frame_id="TRCK", db="track_number", gui="Track"),
            ID3Field(frame_class=TCON, frame_id="TCON", db="genre", gui="Genre"),
            ID3Field(frame_class=TLEN, frame_id="TLEN", db="length_ms", gui="Time"),
            ID3Field(frame_class=TDRC, frame_id="TDRC", db="album_date", gui="Year"),
            ID3Field(db="codec", gui="Codec"),
            ID3Field(db="filepath", gui="Filepath"),
            ID3Field(db="bitrate", gui="Bitrate"),
        ]
        # Lookup dicts 
        # - Usage example: frame_id['TPE1'].db  # => "artist"
        self.frame_id = {f.frame_id: f for f in self.headers}
        self.db = {f.db: f for f in self.headers}
        self.gui = {f.gui: f for f in self.headers}


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
        # print("header tag config")
        # print(self.config)
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
            album_date="year",
            codec="codec",
            length_ms="length",
            filepath="path",
            bitrate="bitrate",
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
            "album_date": "album_date",
            "codec": "codec",
            "length_seconds": "length_seconds",
            "filepath": "filepath",
            "bitrate": "bitrate",
        }
        self.gui: dict = {
            "title": "title",
            "artist": "artist",
            "album": "album",
            "album_artist": "alb artist",
            "track_number": "track",
            "genre": "genre",
            "album_date": "year",
            "codec": "codec",
            "length_seconds": "length",
            "filepath": "path",
            "bitrate": "bitrate",
        }
        self.id3: dict = {
            "title": "TIT2",
            "artist": "TPE1",
            "album_artist": "TPE2",
            "album": "TALB",
            "track_number": "TRCK",
            "genre": "TCON",
            "album_date": "TDRC",
            "codec": None,
            "length_seconds": "TLEN",
            "filepath": None,
            "bitrate": "TBIT",
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
