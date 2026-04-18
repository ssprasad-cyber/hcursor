import threading
import logging
import queue
import time
import json
import sounddevice as sd
from vosk import Model, KaldiRecognizer

logger = logging.getLogger("VoiceAssistant")
logging.basicConfig(level=logging.INFO)

class VoiceAssistant:
    def __init__(self, on_command=None):
        self.on_command = on_command
        self.running = False
        
        logger.info("Loading Vosk Model (this may take a few seconds on first run)...")
        # Initialize Vosk Model (Downloads automatically to cache if missing)
        self.model = Model(lang="en-us")
        
        try:
            device_info = sd.query_devices(kind='input')
            self.sample_rate = int(device_info['default_samplerate'])
            logger.info(f"Using default input device: {device_info['name']} at {self.sample_rate}Hz")
        except Exception as e:
            logger.warning(f"Could not query default device, falling back to 16000Hz: {e}")
            self.sample_rate = 16000
            
        self.recognizer = KaldiRecognizer(self.model, self.sample_rate)
        
        self.capture_thread = None
        self.process_thread = None
        self.audio_queue = queue.Queue()
        self.paused_until = 0

    def start(self):
        if not self.running:
            self.running = True
            logger.info("Starting Offline Vosk Voice Assistant...")
            self.capture_thread = threading.Thread(target=self._capture_loop, daemon=True)
            self.process_thread = threading.Thread(target=self._process_loop, daemon=True)
            self.capture_thread.start()
            self.process_thread.start()

    def stop(self):
        if self.running:
            self.running = False
            logger.info("Stopping Voice Assistant...")
            if self.capture_thread: self.capture_thread.join(timeout=1.0)
            if self.process_thread: self.process_thread.join(timeout=1.0)

    def _audio_callback(self, indata, frames, time_info, status):
        """ Hardware interrupt callback fired continuously yielding raw bytes """
        if not self.running: return
        if time.time() < self.paused_until:
            return
            
        if status:
            # Drop minor overflow warnings
            pass
            
        self.audio_queue.put(bytes(indata))

    def _capture_loop(self):
        try:
            with sd.RawInputStream(
                channels=1,
                samplerate=self.sample_rate,
                dtype='int16',
                blocksize=int(self.sample_rate * 0.1),
                callback=self._audio_callback
            ) as stream:
                logger.info(f"Microphone connected safely via Sounddevice at {self.sample_rate}Hz.")
                while self.running:
                    time.sleep(0.1)
        except Exception as e:
            logger.error(f"InputStream hardware crash: {e}")

    def _process_loop(self):
        while self.running:
            try:
                audio_bytes = self.audio_queue.get(timeout=1)
            except queue.Empty:
                continue
                
            try:
                if self.recognizer.AcceptWaveform(audio_bytes):
                    result = json.loads(self.recognizer.Result())
                    text = result.get('text', '').lower().strip()
                    if text:
                        self._handle_command(text)
            except Exception as e:
                logger.error(f"Transcription processing block error: {e}")

                
                
    def _handle_command(self, text):
        words = text.split()
        is_type_cmd = any(text.startswith(w) for w in ["type ", "tie ", "time ", "tight ", "typed "])
        
        # Valid if it's a short phrase containing a known action verb, or a type command
        is_short_cmd = len(words) <= 3 and any(k in text for k in ["click", "scroll", "up", "down", "enter", "center", "hunter", "stop"])
        
        if is_type_cmd or is_short_cmd:
            logger.info(f"🎤 Command: '{text}'")
            if "stop listening" in text:
                logger.info("⏸️ Voice assistant paused for 10 seconds...")
                self.paused_until = time.time() + 10
            else:
                if self.on_command:
                    self.on_command(text)
        else:
            pass

if __name__ == "__main__":
    def my_cmd(cmd):
        print(f"COMMAND RECEIVED: {cmd}")
        
    va = VoiceAssistant(on_command=my_cmd)
    va.start()
    time.sleep(20)
    va.stop()

