# from mutagen.id3 import ID3
# from mutagen.id3._frames import TIT2
# import os
#
#
# def get_id3_tags(file):
#     """Get the ID3 tags for an audio file
#
#     # Parameters
#     `file` | str | Fully qualified path to file
#
#     # Returns
#     dict of all id3 tags
#     at minimum we will get the filename as a title.[ID3:TIT2]
#     """
#
#     # Check if all tags are empty
#     # tags_are_empty = all(not values for values in audio.values())
#     audio = ID3()
#     try:
#         if not audio["TIT2"] or audio["TIT2"].text[0] == "":
#             title = os.path.splitext(os.path.basename(file))[0]
#             frame = TIT2(encoding=3, text=[title])
#             audio["TIT2"] = frame
#         audio.save()  # type: ignore
#     except Exception as e:
#         print(f"get_id3_tags.py | Could not assign file ID3 tag: {e}")
#     return audio


import os
from mutagen.id3 import ID3, TIT2


def get_id3_tags(file):
    """Get the ID3 tags for an audio file"""

    try:
        # Open the MP3 file and read its content
        audio = ID3(file)

        if os.path.exists(file):
            audio.save(os.path.abspath(file))

        # If 'TIT2' tag is not set, add it with a default value (title will be the filename without extension)
        title = os.path.splitext(os.path.basename(file))[0]
        for key in list(audio.keys()):
            if key == "TIT2":
                audio[key].text[0] = title
                break
        else:
            tit2_tag = TIT2(encoding=3, text=[title])
            audio["TIT2"] = tit2_tag

        # Save the updated tags
        audio.save()

    except Exception as e:
        print(f"get_id3_tags.py | Could not assign file ID3 tag: {e}")

    return audio
