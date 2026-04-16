import cv2
import mediapipe as mp
import threading
import math
import logging

logger = logging.getLogger("EyeTracker")
logging.basicConfig(level=logging.INFO)

class EyeTracker:
    def __init__(self, camera_index=0, on_move=None, on_click=None, on_long_click=None):
        self.camera_index = camera_index
        self.on_move = on_move
        self.on_click = on_click
        self.on_long_click = on_long_click
        
        self.running = False
        self.cap = None
        self.thread = None
        self.latest_frame_rgb = None
        
        # Mediapipe setup
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            max_num_faces=1,
            refine_landmarks=True,  # Crucial for iris tracking
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        
        # Calibration state
        # In normalized coords from webcam (0 to 1). 
        # Typically x is inverted because camera is mirrored
        # Neutral Calibration
        self.neutral_x = 0.5
        self.neutral_y = 0.5
        self.neutral_calibrated = False
        
        # Smoothing and Velocity limits
        self.alpha = 0.2  # Exponential velocity smoothing (damping)
        self.sensitivity = 0.3  # Velocity multiplier (lowered per user request)
        self.deadzone_threshold = 0.002
        self.max_speed = 0.02 # Max cap speed per frame
        self.smooth_x = 0.5
        self.smooth_y = 0.5
        self.vx = 0.0
        self.vy = 0.0
        
        # Blink detection variables
        self.blink_threshold = 0.015 # Tune based on metric
        self.blink_frames = 0
        self.is_blinking = False
        self.frames_for_click = 3
        self.frames_for_long_click = 10

    def start(self):
        if not self.running:
            self.running = True
            logger.info("Starting Eye Tracker...")
            self.thread = threading.Thread(target=self._run, daemon=True)
            self.thread.start()

    def stop(self):
        if self.running:
            self.running = False
            logger.info("Stopping Eye Tracker...")
            if self.thread:
                self.thread.join()
            if self.cap:
                self.cap.release()
            self.face_mesh.close()

    def update_calibration(self, min_x, max_x, min_y, max_y):
        logger.info("Legacy absolute calibration bounds ignored in favor of relative dynamic calibration.")

    def recenter(self):
        self.neutral_calibrated = False
        self.smooth_x = 0.5
        self.smooth_y = 0.5
        self.vx = 0.0
        self.vy = 0.0
        logger.info("Recalibrating neutral position and clearing velocity...")

    def _euclidean_distance(self, pt1, pt2):
        return math.sqrt((pt1.x - pt2.x)**2 + (pt1.y - pt2.y)**2)

    def _get_ear(self, landmarks, left_indices, right_indices):
        """
        Calculate Eye Aspect Ratio (EAR) to detect blinks.
        Approximates the aspect ratio by taking distances between upper/lower eyelid points.
        """
        # Right eye indices (usually from user perspective)
        # MediaPipe landmarks for eyes:
        # Left eye: [33, 160, 158, 133, 153, 144]
        # Right eye: [362, 385, 387, 263, 373, 380]
        # We process one of the eyes here
        p2_p6 = self._euclidean_distance(landmarks[left_indices[1]], landmarks[left_indices[5]])
        p3_p5 = self._euclidean_distance(landmarks[left_indices[2]], landmarks[left_indices[4]])
        p1_p4 = self._euclidean_distance(landmarks[left_indices[0]], landmarks[left_indices[3]])
        return (p2_p6 + p3_p5) / (2.0 * p1_p4)

    def _run(self):
        self.cap = cv2.VideoCapture(self.camera_index)
        
        # Example landmarks arrays for EAR calculation
        RIGHT_EYE = [362, 385, 387, 263, 373, 380] 
        LEFT_EYE = [33, 160, 158, 133, 153, 144]

        # Iris center landmarks (rough approx using refine_landmarks)
        # Left iris center: 468, Right iris center: 473
        
        while self.running:
            success, frame = self.cap.read()
            if not success:
                logger.warning("Ignoring empty camera frame.")
                continue

            # Flip the frame horizontally for a selfie-view display.
            frame = cv2.flip(frame, 1)
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            self.latest_frame_rgb = frame_rgb.copy()
            results = self.face_mesh.process(frame_rgb)
            
            if results.multi_face_landmarks:
                landmarks = results.multi_face_landmarks[0].landmark
                
                # Check for blinks
                left_ear = self._get_ear(landmarks, LEFT_EYE, LEFT_EYE) # using left eye indices
                right_ear = self._get_ear(landmarks, RIGHT_EYE, RIGHT_EYE)
                ear = (left_ear + right_ear) / 2.0
                
                # Simple EAR threshold comparison. NOTE: you may need to calibrate this per user.
                # Since MediaPipe landmarks are normalized (0-1), euclidean distance might be very small.
                # Our EAR calculation is a ratio, so it's scale invariant. Typical EAR threshold is ~0.2.
                # However, MediaPipe's topological landmarks can sometimes have lower bounds. Let's use 0.15 threshold.
                ear_threshold = 0.22 
                if ear < ear_threshold:
                    self.blink_frames += 1
                    self.is_blinking = True
                else:
                    if self.is_blinking:
                        # Blink ended. Evaluate frames.
                        if self.blink_frames > self.frames_for_long_click:
                            if self.on_long_click:
                                self.on_long_click()
                        elif self.blink_frames >= self.frames_for_click:
                            if self.on_click:
                                self.on_click()
                        self.is_blinking = False
                        self.blink_frames = 0
                
                # Map position if not blinking (to avoid jitter)
                if not self.is_blinking:
                    # Using landmarks[468] for left iris center, landmarks[473] for right iris center
                    # We can average them to find a stable central point.
                    try:
                        # Head-based tracking logic: average of eyes and nose
                        left_eye = landmarks[33]
                        right_eye = landmarks[263]
                        nose = landmarks[1]
                        
                        face_x = (left_eye.x + right_eye.x + nose.x) / 3.0
                        face_y = (left_eye.y + right_eye.y + nose.y) / 3.0
                        
                        if getattr(self, 'neutral_calibrated', False) == False:
                            self.neutral_x = face_x
                            self.neutral_y = face_y
                            self.neutral_calibrated = True
                            self.smooth_x, self.smooth_y = 0.5, 0.5
                            self.vx, self.vy = 0.0, 0.0
                            logger.info(f"Neutral calc initialized at X:{self.neutral_x:.3f}, Y:{self.neutral_y:.3f}")
                        
                        dx = face_x - self.neutral_x
                        dy = face_y - self.neutral_y
                        
                        # Velocity target based calculation
                        target_vx = 0.0
                        target_vy = 0.0
                        
                        if abs(dx) > self.deadzone_threshold:
                            target_vx = dx * self.sensitivity
                        if abs(dy) > self.deadzone_threshold:
                            target_vy = dy * self.sensitivity
                            
                        # Smooth velocities (Momentum/Damping)
                        self.vx = self.vx * (1 - self.alpha) + target_vx * self.alpha
                        self.vy = self.vy * (1 - self.alpha) + target_vy * self.alpha
                        
                        # Speed clamp jumps
                        if self.vx > self.max_speed: self.vx = self.max_speed
                        if self.vx < -self.max_speed: self.vx = -self.max_speed
                        if self.vy > self.max_speed: self.vy = self.max_speed
                        if self.vy < -self.max_speed: self.vy = -self.max_speed
                        
                        # Accumulate onto coordinates
                        self.smooth_x += self.vx
                        self.smooth_y += self.vy
                        
                        # Enforce bounds ensuring cursor doesn't leave screen
                        self.smooth_x = max(0.0, min(1.0, self.smooth_x))
                        self.smooth_y = max(0.0, min(1.0, self.smooth_y))

                        if self.on_move:
                            self.on_move(self.smooth_x, self.smooth_y)
                            
                    except IndexError:
                        pass # No refined landmarks
                        
            # Sleep and parse user requests directly to recenter
            key = cv2.waitKey(1) & 0xFF
            if key == ord('r'):
                self.recenter()

if __name__ == "__main__":
    def move_cb(x, y):
        print(f"Norm X: {x:.2f}, Norm Y: {y:.2f}", end='\r')
        
    def click_cb():
        print("\nCLICK!")
        
    def long_click_cb():
        print("\nLONG CLICK!")
        
    tracker = EyeTracker(on_move=move_cb, on_click=click_cb, on_long_click=long_click_cb)
    tracker.start()
    import time
    time.sleep(10)
    tracker.stop()
