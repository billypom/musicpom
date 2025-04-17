import os
from logging import debug, error
from mutagen.id3 import ID3
from mutagen.mp3 import MP3
from mutagen.flac import FLAC
from mutagen.id3._frames import TIT2
from mutagen.id3._util import ID3NoHeaderError

from utils import convert_id3_timestamp_to_datetime


def get_mp3_tags(filename: str) -> tuple[MP3 | ID3 | FLAC, str]:
    """Get ID3 tags for mp3 file"""
    try:
        # Open the MP3 file and read its content
        audio = MP3(filename)
    except ID3NoHeaderError:
        audio = MP3()

    try:
        if os.path.exists(filename):
            audio.save(os.path.abspath(filename))

        title = os.path.splitext(os.path.basename(filename))[0]
        if "TIT2" not in list(audio.keys()):
            # if title tag doesnt exist, create it - filename
            tit2_tag = TIT2(encoding=3, text=[title])
            audio["TIT2"] = tit2_tag
        # Save the updated tags
        audio.save()
        return audio, ""

    except Exception as e:
        return MP3(), f"Could not assign ID3 tag to file: {e}"


def id3_remap(audio: MP3 | ID3 | FLAC) -> dict:
    """
    Turns an ID3 dict into a normal dict that I, the human, can use.
    Add extra fields too :D yahooo
    """
    remap = {}
    if isinstance(audio, MP3):
        # so ugly
        uslt_tags = [tag for tag in audio.keys() if tag.startswith("USLT::")]
        lyrics = next((audio[tag].text for tag in uslt_tags), "")
        # so ugly
        remap = {
            "title": audio.get("TIT2"),
            "artist": audio.get("TPE1"),
            "album": audio.get("TALB"),
            "track_number": audio.get("TRCK"),
            "genre": audio.get("TCON"),
            "date": convert_id3_timestamp_to_datetime(audio.get("TDRC")),
            "bitrate": audio.get("TBIT"),
            "lyrics": lyrics,
            "length": int(round(audio.info.length, 0)),
        }
    return remap


def get_id3_tags(filename: str) -> tuple[MP3 | ID3 | FLAC, str]:
    """
    Get the ID3 tags for an audio file
    Returns a tuple of:
    - mutagen ID3 object OR python dictionary
    - string reason for failure (failure = empty dict above)

    Args
        - filename
    Returns
        - tuple(ID3/dict, fail_reason)

    ID3 dict looks like this:
    {
        'TIT2': TIT2(encoding=<Encoding.UTF8: 3>, text=['song title']),
        'TSSE': TSSE(encoding=<Encoding.UTF8: 3>, text=['Lavf59.27.100'],
        ...
    }
    """
    if filename.endswith(".mp3"):
        tags, details = get_mp3_tags(filename)
    else:
        tags, details = ID3(), "non mp3 file"
    return tags, details
