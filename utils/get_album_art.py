from mutagen.id3 import ID3
from logging import debug, error


def get_album_art(file: str | None) -> bytes:
    """Get the album art for an audio file
    # Parameters
    `file` | str | Fully qualified path to file
    # Returns
    bytes for album art or placeholder artwork
    """
    default_image_path = "./assets/default_album_art.jpg"
    if file:
        try:
            audio = ID3(file)
            for tag in audio.getall("APIC"):
                if tag.type == 3:  # 3 is the type for front cover
                    return tag.data
            if audio.getall("APIC"):
                return audio.getall("APIC")[0].data
        except Exception as e:
            error(f"Error retrieving album art: {e}")
            return bytes()
    with open(default_image_path, "rb") as f:
        # debug("loading placeholder album art")
        return f.read()
