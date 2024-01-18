import matplotlib.pyplot as plt
import numpy as np
import wave
import math

file = 'output.wav'

with wave.open(file,'r') as wav_file:
    num_channels = wav_file.getnchannels()
    frame_rate = wav_file.getframerate()
    downsample = math.ceil(frame_rate * num_channels / 2) # Get two samples per second!

    process_chunk_size = 600000 - (600000 % frame_rate)

    signal = None
    waveform = np.array([])

    while signal is None or signal.size > 0:
        signal = np.frombuffer(wav_file.readframes(process_chunk_size), dtype='int16')
        signal = signal.astype(float)  # Convert to float
        # padding_value = 0
        # Take mean of absolute values per 0.5 seconds
        sub_waveform = np.nanmean(
            # np.pad(np.absolute(signal), (0, ((downsample - (signal.size % downsample)) % downsample)), mode='constant', constant_values=padding_value).reshape(-1, downsample),
            np.pad(np.absolute(signal), (0, ((downsample - (signal.size % downsample)) % downsample)), mode='constant', constant_values=np.NaN).reshape(-1, downsample),
            axis=1
        )

        waveform = np.concatenate((waveform, sub_waveform))

    #Plot
    plt.figure(1)
    plt.title('Waveform')
    plt.plot(waveform)
    plt.plot(-waveform)
    plt.show()