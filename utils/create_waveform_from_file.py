import matplotlib.pyplot as plt
import numpy as np
import math
from pydub import AudioSegment


def create_waveform_from_file(file):
    """_summary_

    Args:
        file (_type_): _description_
    """
    # Read the MP3 file
    audio = AudioSegment.from_file(file)
    # Convert to mono and get frame rate and number of channels
    num_channels = 1
    frame_rate = audio.frame_rate
    downsample = math.ceil(frame_rate * num_channels / 1)  # /1 = 1 sample per second
    # Process audio data
    process_chunk_size = 600000 - (600000 % frame_rate)
    signal = None
    waveform = np.array([])
    # Convert the audio data to numpy array
    audio_data = np.array(audio.get_array_of_samples())
    # Create waveforms
    start_index = 0
    while start_index < len(audio_data):
        end_index = start_index + process_chunk_size
        # Get chunk and convert to float
        signal = audio_data[start_index:end_index].astype(float)

        # Take mean of absolute values per 0.5 seconds
        sub_waveform = np.nanmean(
            np.pad(
                np.absolute(signal),
                (0, ((downsample - (signal.size % downsample)) % downsample)),
                mode="constant",
                constant_values=np.NaN,
            ).reshape(-1, downsample),
            axis=1,
        )

        waveform = np.concatenate((waveform, sub_waveform))
        start_index = end_index

    # Plot waveforms
    plt.figure(1)
    plt.plot(waveform, color="blue")
    plt.plot(-waveform, color="blue")  # Mirrored waveform
    # Fill in area
    plt.fill_between(
        np.arange(len(waveform)), waveform, -waveform, color="blue", alpha=0.5
    )
    # Remove decorations, labels, axes, etc
    plt.axis("off")
    # Graph goes to ends of pic
    plt.xlim(0, len(waveform))
    # Save pic
    plt.savefig(
        "assets/now_playing_waveform.png", dpi=64, bbox_inches="tight", pad_inches=0
    )
    # Show me tho
    # plt.show()


# create_waveform_from_file(sys.argv[1])
