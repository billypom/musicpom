import os
import logging
from mutagen.id3 import ID3, TIT2, ID3NoHeaderError


def get_id3_tags(filename):
    """Get the ID3 tags for an audio file"""
    logging.info(f"filename: {filename}")

    try:
        # Open the MP3 file and read its content
        audio = ID3(filename)
    except ID3NoHeaderError:
        audio = ID3()

    try:
        if os.path.exists(filename):
            audio.save(os.path.abspath(filename))

        # If 'TIT2' tag is not set, add it with a default value (title will be the filename without extension)
        title = os.path.splitext(os.path.basename(filename))[0]
        list_of_id3_tags = list(audio.keys())
        if "TIT2" in list_of_id3_tags:
            audio.save()
            return audio
        else:
            tit2_tag = TIT2(encoding=3, text=[title])
            audio["TIT2"] = tit2_tag
        # Save the updated tags
        audio.save()

    except Exception as e:
        logging.error(f"Could not assign file ID3 tag: {e}")

    return audio
