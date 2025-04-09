import os
from logging import debug, error
from mutagen.id3 import ID3
from mutagen.id3._frames import TIT2
from mutagen.id3._util import ID3NoHeaderError

def get_mp3_tags(filename: str) -> tuple[ID3 | dict, str]:
    """Get ID3 tags for mp3 file"""
    try:
        # Open the MP3 file and read its content
        audio = ID3(filename)
    except ID3NoHeaderError:
        audio = ID3()

    try:
        if os.path.exists(filename):
            audio.save(os.path.abspath(filename))

        # NOTE: If 'TIT2' tag is not set, we add it with a default value
        # title = filename without extension

        title = os.path.splitext(os.path.basename(filename))[0]
        if "TIT2" in list(audio.keys()):
            audio.save()
            return audio, ""
        else:
            # if title tag doesnt exist,
            # create it and return
            tit2_tag = TIT2(encoding=3, text=[title])
            audio["TIT2"] = tit2_tag
        # Save the updated tags
        audio.save()
        return audio, ""

    except Exception as e:
        return {}, f"Could not assign ID3 tag to file: {e}"

def get_id3_tags(filename: str) -> tuple[ID3 | dict, str]:
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
        {'TIT2': TIT2(encoding=<Encoding.UTF8: 3>, text=['song title']), 'TSSE': TSSE(encoding=<Encoding.UTF8: 3>, text=['Lavf59.27.100'])}
    """
    if filename.endswith(".mp3"):
        tags, details = get_mp3_tags(filename)
    else:
        tags, details = {}, "non mp3 file"
    return tags, details


