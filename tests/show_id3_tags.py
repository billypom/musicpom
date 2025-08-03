import sys
from mutagen.id3 import ID3
# i just added the below line - APIC was originally in the above
# but pyright yelled at me...
from mutagen.id3._frames import APIC
import os
from logging import debug


def print_id3_tags(file_path):
    """Prints all ID3 tags for a given audio file to debug out."""
    try:
        audio = ID3(file_path)
    except Exception as e:
        debug(f"Error reading ID3 tags: {e}")
        return

    for tag in audio.keys():
        # Special handling for APIC frames (attached pictures)
        if isinstance(audio[tag], APIC):
            debug(
                f"{tag}: Picture, MIME type: {audio[tag].mime}, Description: {audio[tag].desc}"
            )
        else:
            debug(f"{tag}: {audio[tag].pprint()}")


def main():
    if len(sys.argv) != 2:
        debug("Usage: python show_id3_tags.py /path/to/audio/file")
        sys.exit(1)
    file_path = sys.argv[1]
    if not os.path.exists(file_path):
        debug("File does not exist.")
        sys.exit(1)
    print_id3_tags(file_path)


if __name__ == "__main__":
    main()
