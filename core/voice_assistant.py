import speech_recognition as sr
import threading
import logging

logger = logging.getLogger("VoiceAssistant")
logging.basicConfig(level=logging.INFO)

class VoiceAssistant:
    def __init__(self, on_command=None):
        self.on_command = on_command
        self.running = False
        self.recognizer = sr.Recognizer()
        
        # Hardcoding device_index=5 to force PyAudio to use the physical laptop microphone
        # (HD-Audio Generic: ALC245 Analog) instead of the default silent HDMI output.
        self.microphone = sr.Microphone(device_index=5)
        
        # Adjust for ambient noise on initialization
        with self.microphone as source:
            logger.info("Calibrating microphone for ambient noise...")
            # We run the ambient adjustment, but then override the threshold 
            self.recognizer.adjust_for_ambient_noise(source, duration=2)
            self.recognizer.energy_threshold = 300 # Hardcode lower value for extremely high sensitivity
            self.recognizer.dynamic_energy_threshold = False
            logger.info(f"Microphone calibrated. Energy threshold fixed at {self.recognizer.energy_threshold}")

        self.stop_listening_fn = None

    def start(self):
        if not self.running:
            self.running = True
            logger.info("Starting Voice Assistant background listener...")
            # listen_in_background returns a callback that can be called to stop the thread
            self.stop_listening_fn = self.recognizer.listen_in_background(
                self.microphone, 
                self._callback
            )

    def stop(self):
        if self.running:
            self.running = False
            logger.info("Stopping Voice Assistant...")
            if self.stop_listening_fn:
                self.stop_listening_fn(wait_for_stop=False)
                self.stop_listening_fn = None

    def _callback(self, recognizer, audio):
        if not self.running: return
        
        try:
            # Using Google Web Speech API for simplicity and no-setup.
            # For purely offline, pocketsphinx or whisper could be integrated here.
            text = recognizer.recognize_google(audio)
            text = text.lower().strip()
            
            logger.info(f"Recognized voice: '{text}'")
            
            if self.on_command:
                self.on_command(text)
                
        except sr.UnknownValueError:
            logger.info("Speech recognition could not understand audio")
        except sr.RequestError as e:
            logger.warning(f"Could not request results from Speech Recognition service; {e}")
        except Exception as e:
            logger.error(f"VoiceAssistant Error: {e}")

if __name__ == "__main__":
    def my_cmd(cmd):
        print(f"COMMAND RECEIVED: {cmd}")
        
    va = VoiceAssistant(on_command=my_cmd)
    va.start()
    
    import time
    time.sleep(15)
    va.stop()
