from typing import Optional
from dataclasses import dataclass
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
class ID3Field:
    db: str                             # e.g., "title"
    gui: str                            # e.g., "Title"
    frame_class: Optional[type] = None  # e.g., TPE1
    frame_id: Optional[str] = None      # e.g., "TPE1"
    editable: bool = True


class HeaderTags2:
    def __init__(self):
        self.headers = [
            ID3Field(frame_class=TIT2, frame_id="TIT2", db="title", gui="Title"),
            ID3Field(frame_class=TPE1, frame_id="TPE1", db="artist", gui="Artist"),
            ID3Field(frame_class=TALB, frame_id="TALB", db="album", gui="Album"),
            ID3Field(frame_class=TPE2, frame_id="TPE2", db="album_artist", gui="Album Artist"),
            ID3Field(frame_class=TRCK, frame_id="TRCK", db="track_number", gui="Track"),
            ID3Field(frame_class=TCON, frame_id="TCON", db="genre", gui="Genre"),
            ID3Field(frame_class=TDRC, frame_id="TDRC", db="album_date", gui="Year"),
            ID3Field(frame_class=TLEN, frame_id="TLEN", db="length_ms", gui="Time", editable=False),
            ID3Field(db="codec", gui="Codec", editable=False),
            ID3Field(db="bitrate", gui="Bitrate", editable=False),
            ID3Field(db="filepath", gui="Filepath", editable=False),
        ]
        # Lookup dicts 
        # - Usage example: frame_id['TPE1'].db  # => "artist"
        self.frame_id = {f.frame_id: f for f in self.headers}
        self.db = {f.db: f for f in self.headers}
        self.gui = {f.gui: f for f in self.headers}

        # Simple lists
        self.frame_id_list = [f.frame_id for f in self.headers]
        self.db_list = [f.db for f in self.headers]
        self.gui_list = [f.gui for f in self.headers]

    def get_editable_db_list(self) -> list:
        return [f.db for f in self.headers if f.editable]

