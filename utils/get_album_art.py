from mutagen.id3 import ID3, APIC

def get_album_art(file):
    """Get the album art for an audio file
    # Parameters
    `file` | str | Fully qualified path to file
    
    # Returns
    dict of all id3 tags
    """
    try:
        audio = ID3(file)
        album_art = audio.get('APIC:').data if 'APIC:' in audio else None
        return album_art
    except Exception as e:
        print(f"Error: {e}")
        return {}