import ell

from pydub import AudioSegment
import numpy as np

# Helper function to load and convert audio files
def load_audio_sample(file_path):
    audio = AudioSegment.from_file(file_path)
    samplearray = np.array(audio.get_array_of_samples())
    return samplearray


ell.init(verbose=True)

@ell.complex("gpt-4o-audio-preview")
def test():
    return [ell.user(["Hey! what do you think about this?", load_audio_sample("toronto.mp3")])]


if __name__ == "__main__":
    response = test()
    print(response.audios[0])
