from mutagen.easyid3 import EasyID3
from mutagen import File

def get_id3_tags(file):
    """Get the ID3 tags for an audio file
    # Parameters
    `file` | str | Fully qualified path to file
    
    # Returns
    dict of all id3 tags
    """
    try:
        audio = EasyID3(file)
        print(f'ID3 Tags: {audio}')
        return audio
    except Exception as e:
        print(f"Error: {e}")
        return {}