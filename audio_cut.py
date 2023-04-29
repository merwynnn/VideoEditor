import numpy as np
import matplotlib.pyplot as plt
import soundfile as sf

def beat_detection(audio_file):
    # Load audio file
    data, sample_rate = sf.read(audio_file)

    if len(data.shape) > 1:
        # Average the two channels to get a mono signal
        data = np.mean(data, axis=1)

    # Compute the short-time Fourier transform (STFT)
    window_size = 1024
    hop_size = 512
    fft_size = window_size // 2 + 1

    window = np.hanning(window_size)
    stft = np.array([np.fft.rfft(window * data[i:i + window_size])
                     for i in range(0, len(data) - window_size, hop_size)])

    # Compute the magnitude spectrogram
    magnitude_spectrogram = np.abs(stft)

    # Compute the onset strength envelope
    onset_strength_envelope = np.sum(np.diff(magnitude_spectrogram, axis=0) > 0, axis=1)

    # Compute the tempo (in beats per minute)
    tempo = 60 / (np.median(np.diff(np.where(onset_strength_envelope > np.median(onset_strength_envelope) * 1.5)[0])) / sample_rate * hop_size)

    # Plot the onset strength envelope and detected beats
    plt.figure(figsize=(10, 4))
    plt.plot(onset_strength_envelope)
    plt.plot(np.where(onset_strength_envelope > np.median(onset_strength_envelope) * 1.5)[0], onset_strength_envelope[onset_strength_envelope > np.median(onset_strength_envelope) * 1.5], 'ro')
    plt.xlabel('Frame')
    plt.ylabel('Onset strength')
    plt.title(f'Tempo: {tempo:.2f} BPM')
    plt.show()

audio_file = 'montero.wav'
beat_detection(audio_file)