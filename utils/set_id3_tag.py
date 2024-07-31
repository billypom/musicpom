import logging
from components import ErrorDialog
from utils.handle_year_and_date_id3_tag import handle_year_and_date_id3_tag
from mutagen.id3 import ID3
from mutagen.id3._util import ID3NoHeaderError
from mutagen.id3._frames import (
    Frame,
    TIT2,
    TPE1,
    TALB,
    TRCK,
    # TYER,
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

id3_tag_mapping = {
    "title": TIT2,  # Title/song name/content description
    "artist": TPE1,  # Lead performer(s)/Soloist(s)
    "album": TALB,  # Album/Movie/Show title
    "album_artist": TPE2,  # Band/orchestra/accompaniment
    "genre": TCON,  # Content type
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


def set_id3_tag(filepath: str, tag_name: str, value: str):
    """Sets the ID3 tag for a file given a filepath, tag_name, and a value for the tag

    Args:
        filepath: path to the mp3 file
        tag_name: common name of the ID3 tag
        value: value to set for the tag

    Returns:
        True / False"""
    print(
        f"set_id3_tag.py | filepath: {filepath} | tag_name: {tag_name} | value: {value}"
    )

    try:
        try:  # Load existing tags
            audio_file = ID3(filepath)
        except ID3NoHeaderError:  # Create new tags if none exist
            audio_file = ID3()
        # Date handling - TDRC vs TYER+TDAT
        if tag_name == "album_date":
            tyer_tag, tdat_tag = handle_year_and_date_id3_tag(value)
            # always update TYER
            audio_file.add(tyer_tag)
            if tdat_tag:
                # update TDAT if we have it
                audio_file.add(tdat_tag)
        # Lyrics
        elif tag_name == "lyrics" or tag_name == "USLT":
            try:
                audio = ID3(filepath)
            except Exception as e:
                logging.debug(
                    f"set_id3_tag.py set_id3_tag() ran into an exception: {e}"
                )
                audio = ID3()
            audio.delall("USLT")
            frame = USLT(encoding=3, text=value)
            audio.add(frame)
            audio.save()
            return True
        # Other
        elif tag_name in id3_tag_mapping:  # Tag accounted for
            tag_class = id3_tag_mapping[tag_name]
            if issubclass(tag_class, Frame):
                frame = tag_class(encoding=3, text=[value])
                audio_file.add(frame)  # Add the tag
            else:
                pass
        else:
            pass
        audio_file.save(filepath)
        return True
    except Exception as e:
        dialog = ErrorDialog(f"An unhandled exception occurred:\n{e}")
        dialog.exec_()
        return False
