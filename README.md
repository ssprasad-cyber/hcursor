# HCursor

**HCursor** is an AI-powered assistive desktop application designed to control the operating system using only eye-tracking and voice commands. By combining MediaPipe face-mesh algorithms with precise sound transcription, users with mobility limitations can maneuver a computer smoothly without relying on conventional pointing hardware.

## Features
- **Hands-Free Cursor Control**: Track eyes to maneuver your mouse pointer across the screen.
- **Blink to Click**: Perform Left Click via normal blink, Right Click via long blink.
- **Voice Assistant**: Talk directly to the system to "scroll down", "double click", or use voice-to-text dictation ("type Hello").
- **Local AI Edge Tracking**: Ensures high levels of privacy and near real-time latency by running eye-recognition on device.

## Setup Instructions
1. Clone this repository to your local system and navigate to the folder.
2. Install the necessary pip packages by running:
```bash
pip install -r requirements.txt
```
3. Boot the application using:
```bash
python main.py
```

## Hardware Requirements
- Functioning Web-Camera (Integrated or External USB)
- Functioning Microphone
- Display Monitor

## Additional Information
- To quit the tracker manually without interaction, `CTRL+C` from the launch terminal can safely shut down background threads alongside the main process.
- PyAutoGUI's Fail-Safe has been explicitly disabled during setup to prevent crashes when the tracker naturally places the cursor in screen edges.