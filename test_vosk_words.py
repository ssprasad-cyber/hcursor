from vosk import Model, KaldiRecognizer
import wave
import json

model = Model(lang="en-us")
rec = KaldiRecognizer(model, 16000)
rec.SetWords(True)

# Create a dummy silent/noisy audio buffer
audio = bytes([0] * 3200)
rec.AcceptWaveform(audio)
print(rec.Result())
