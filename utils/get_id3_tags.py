from mutagen.id3 import ID3
from mutagen.id3._frames import TIT2
import os


def get_id3_tags(file):
    """Get the ID3 tags for an audio file

    # Parameters
    `file` | str | Fully qualified path to file

    # Returns
    dict of all id3 tags
    at minimum we will get the filename as a title.[ID3:TIT2]
    """

    try:
        audio = ID3(file)
    except Exception:
        audio = {}

    # Check if all tags are empty
    # tags_are_empty = all(not values for values in audio.values())
    try:
        if audio["TIT2"] is None:
            title = os.path.splitext(os.path.basename(file))[0]
            frame = TIT2(encoding=3, text=[title])
            audio["TIT2"] = frame
    except Exception as e:
        print(f"get_id3_tags.py | Could not assign file ID3 tag: {e}")
        pass
    try:
        audio.save()  # type: ignore
    except Exception:
        pass
    return audio
