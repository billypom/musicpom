from mutagen.id3 import ID3, APIC


def get_album_art(file: str) -> bytes:
    """Get the album art for an audio file
    # Parameters
    `file` | str | Fully qualified path to file
    # Returns
    Data for album art or default file
    """
    default_image_path = "./assets/default_album_art.jpg"
    try:
        audio = ID3(file)
        for tag in audio.getall("APIC"):
            if tag.type == 3:  # 3 is the type for front cover
                return tag.data
        if audio.getall("APIC"):
            return audio.getall("APIC")[0].data
    except Exception as e:
        print(f"Error retrieving album art: {e}")
    with open(default_image_path, "rb") as f:
        print(f"album art type: {type(f.read())}")
        return f.read()
