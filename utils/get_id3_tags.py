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
        return audio
    except Exception as e:
        print(f"Error: {e}")
        return {}
    
filepath = '/home/billy/Music/songs/meanings/blah99/H.mp3'
id3_tags = get_id3_tags(filepath)
print(id3_tags)