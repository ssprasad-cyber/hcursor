import time
from core.voice_assistant import VoiceAssistant

def on_command(cmd_text):
    print(f"\n=======================================")
    print(f"🎤 I HEARD: {cmd_text}")
    print(f"=======================================\n")

if __name__ == "__main__":
    print("🎙️ Initializing SoundDevice Voice Assistant Test Environment...")
    
    # Instantiate without EyeTracker/System hooks
    va = VoiceAssistant(on_command=on_command)
    va.start()
    
    print("\n[✅ Backend Running -> Start speaking into your microphone! Press Ctrl+C to quit.]\n")
    
    try:
        # Keep main thread alive
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Shutting down Voice Assistant...")
    finally:
        va.stop()