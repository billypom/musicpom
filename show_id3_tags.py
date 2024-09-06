import sys
from mutagen.id3 import ID3, APIC
import os
import logging


def print_id3_tags(file_path):
    """Prints all ID3 tags for a given audio file."""
    try:
        audio = ID3(file_path)
    except Exception as e:
        print(f"Error reading ID3 tags: {e}")
        return

    for tag in audio.keys():
        # Special handling for APIC frames (attached pictures)
        if isinstance(audio[tag], APIC):
            print(
                f"{tag}: Picture, MIME type: {audio[tag].mime}, Description: {audio[tag].desc}"
            )
        else:
            print(f"{tag}: {audio[tag].pprint()}")


def main():
    if len(sys.argv) != 2:
        print("Usage: python show_id3_tags.py /path/to/audio/file")
        sys.exit(1)
    file_path = sys.argv[1]
    if not os.path.exists(file_path):
        print("File does not exist.")
        sys.exit(1)
    print_id3_tags(file_path)


if __name__ == "__main__":
    main()
