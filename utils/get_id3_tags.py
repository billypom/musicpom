import os
from logging import debug, error
from mutagen.id3 import ID3
from mutagen.id3._frames import TIT2
from mutagen.id3._util import ID3NoHeaderError


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
    """
    # debug(filename)

    if filename.endswith(".mp3"):
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
            list_of_id3_tags = list(audio.keys())
            if "TIT2" in list_of_id3_tags:
                audio.save()
                return audio, ""
            else:
                tit2_tag = TIT2(encoding=3, text=[title])
                audio["TIT2"] = tit2_tag
            # Save the updated tags
            audio.save()
            return audio, ""

        except Exception as e:
            error(f"Could not assign file ID3 tag: {e}")
            return {}, f"Could not assign ID3 tag to file: {e}"
    return {}, "non mp3 file"


