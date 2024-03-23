from mutagen.easyid3 import EasyID3
from mutagen import File


def get_id3_tags(file):
    """Get the ID3 tags for an audio file
    # Parameters
    `file` | str | Fully qualified path to file
    # Returns
    dict of all id3 tags
    if all tags are empty, at minimum fill in the 'title'
    """
    try:
        audio = EasyID3(file)
        # Check if all tags are empty
        tags_are_empty = all(not values for values in audio.values())
        if tags_are_empty:
            audio['title'] = [file.split('/')[-1]]
        return audio
    except Exception as e:
        print(f"Error: {e}")
        return {}

# import sys
# my_file = sys.argv[1]
# data = get_id3_tags(my_file)
# print(data)
