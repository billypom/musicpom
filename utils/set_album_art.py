from mutagen.id3._frames import APIC
from mutagen.id3 import ID3


def set_album_art(song_filepath: str, art_filepath: str) -> None:
    """Updates the ID3 tag APIC (album art) for a song

    Args:
        `song_filepath`: fully qualified path to audio file
        `art_filepath` : fully qualified path to picture file
    """
    audio = ID3(song_filepath)
    # Remove existing APIC Frames (album art)
    audio.delall("APIC")
    # Add the album art
    with open(art_filepath, "rb") as art:
        if art_filepath.endswith(".jpg") or art_filepath.endswith(".jpeg"):
            audio.add(
                APIC(
                    encoding=3,  # 3 = utf-8
                    mime="image/jpeg",
                    type=3,  # 3 = cover image
                    desc="Cover",
                    data=art.read(),
                )
            )
        elif art_filepath.endswith(".png"):
            audio.add(
                APIC(
                    encoding=3,  # 3 = utf-8
                    mime="image/png",
                    type=3,  # 3 = cover image
                    desc="Cover",
                    data=art.read(),
                )
            )
    audio.save()
