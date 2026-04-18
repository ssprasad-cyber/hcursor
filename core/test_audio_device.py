import sounddevice as sd
device_info = sd.query_devices(5, 'input')
print("Device 5 Info:", device_info)
try:
    sd.check_input_settings(device=5, channels=1, samplerate=16000, dtype='int16')
    print("16000 supported!")
except Exception as e:
    print("16000 not supported:", e)

try:
    sd.check_input_settings(device=5, channels=1, samplerate=44100, dtype='int16')
    print("44100 supported!")
except Exception as e:
    print("44100 not supported:", e)

try:
    sd.check_input_settings(device=5, channels=1, samplerate=48000, dtype='int16')
    print("48000 supported!")
except Exception as e:
    print("48000 not supported:", e)

