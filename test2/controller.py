import cv2
import mediapipe as mp
import pyautogui
import time
from collections import deque
import math
import statistics

# Configuration
SMOOTHING_FACTOR = 0.7  # Higher = more smoothing
CLICK_THRESHOLD = 25    # Distance threshold for click gesture
DOUBLE_TAP_TIME = 0.5   # Time window for double tap (seconds)
GESTURE_COOLDOWN = 0.3  # Cooldown between gestures
DEADZONE_PIXELS = 4     # Ignore tiny movements under this many pixels
MEDIAN_WINDOW = 5       # Number of recent points for median filter
CLICK_LOCK_AFTER = 0.15 # Extra time to keep cursor locked after clicking (seconds)

class HandCursorController:
    
    def __init__(self, mode='general', sensitivity=0.7, click_threshold=25, voice_enabled=True):
        self.cap = cv2.VideoCapture(0)
        # Upgrade: set desired camera resolution to 1280x720
        self.cap.set(3, 1280)
        self.cap.set(4, 720)

        # Upgrade: use up to 2 hands and updated detection settings
        self.hand_detector = mp.solutions.hands.Hands(
            static_image_mode=False,
            max_num_hands=2,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.8
        )
        self.drawing_utils = mp.solutions.drawing_utils
        self.drawing_styles = mp.solutions.drawing_styles
        self.hands_module = mp.solutions.hands
        self.screen_width, self.screen_height = pyautogui.size()
        
        # Smoothing variables
        self.prev_x = 0
        self.prev_y = 0
        self.is_first_frame = True
        self.position_history = deque(maxlen=MEDIAN_WINDOW)
        
        # Gesture state management
        self.is_clicking = False
        self.last_click_time = 0
        self.click_count = 0
        self.last_gesture_time = 0
        self.is_touching = False  # For double-touch edge detection
        self.click_visual_until = 0
        
        # Gesture history for better detection
        self.gesture_history = deque(maxlen=5)
        
        # Cursor lock to stabilize clicks
        self.cursor_locked = False
        self.lock_pos = (0, 0)
        self.lock_release_time = 0.0
        
        # Mode and settings
        self.mode = mode
        self.sensitivity = sensitivity
        self.voice_enabled = voice_enabled
        
        # Update thresholds based on settings
        global CLICK_THRESHOLD, SMOOTHING_FACTOR
        CLICK_THRESHOLD = click_threshold
        SMOOTHING_FACTOR = sensitivity
        
        # Initialize voice engine for medical mode
        self.voice_engine = None
        if self.mode == 'medical' and self.voice_enabled:
            try:
                import pyttsx3
                self.voice_engine = pyttsx3.init()
                self.voice_engine.setProperty('rate', 150)  # Slower speech for medical
            except Exception as e:
                print(f"Voice engine initialization failed: {e}")
        
        # Disable pyautogui failsafe for smoother operation
        pyautogui.FAILSAFE = False
        pyautogui.PAUSE = 0
    
    @staticmethod
    def calculate_distance(point1, point2):
        """Calculate Euclidean distance between two points"""
        return math.sqrt((point1[0] - point2[0])**2 + (point1[1] - point2[1])**2)
    
    def smooth_coordinates(self, x, y):
        """Apply median filter + exponential moving average + deadzone for smooth movement"""
        if self.is_first_frame:
            self.prev_x = x
            self.prev_y = y
            self.is_first_frame = False
            return x, y

        # Median filtering using recent points
        self.position_history.append((x, y))
        xs = [p[0] for p in self.position_history]
        ys = [p[1] for p in self.position_history]
        median_x = int(statistics.median(xs))
        median_y = int(statistics.median(ys))

        # Exponential moving average towards the median
        smooth_x = int(SMOOTHING_FACTOR * self.prev_x + (1 - SMOOTHING_FACTOR) * median_x)
        smooth_y = int(SMOOTHING_FACTOR * self.prev_y + (1 - SMOOTHING_FACTOR) * median_y)

        # Deadzone: ignore tiny jitter
        if math.hypot(smooth_x - self.prev_x, smooth_y - self.prev_y) < DEADZONE_PIXELS:
            return self.prev_x, self.prev_y

        self.prev_x = smooth_x
        self.prev_y = smooth_y

        return smooth_x, smooth_y
    
    def detect_gestures(self, landmarks, frame_width, frame_height):
        """Detect various hand gestures"""
        # Get key landmark positions
        index_tip = landmarks[8]   # Index finger tip
        index_pip = landmarks[6]   # Index finger PIP joint
        thumb_tip = landmarks[4]   # Thumb tip
        thumb_ip = landmarks[3]    # Thumb IP joint
        pinky_tip = landmarks[20]  # Pinky tip
        middle_tip = landmarks[12]
        middle_pip = landmarks[10]
        ring_tip = landmarks[16]
        ring_pip = landmarks[14]
        pinky_pip = landmarks[18]
        
        # Convert to pixel coordinates
        index_x = int(index_tip.x * frame_width)
        index_y = int(index_tip.y * frame_height)
        thumb_x = int(thumb_tip.x * frame_width)
        thumb_y = int(thumb_tip.y * frame_height)
        thumb_ip_x = int(thumb_ip.x * frame_width)
        pinky_x = int(pinky_tip.x * frame_width)
        
        # Calculate distances
        thumb_index_distance = self.calculate_distance(
            (thumb_x, thumb_y), (index_x, index_y)
        )
        
        # Check if fingers are extended (for better gesture recognition)
        index_extended = index_tip.y < index_pip.y
        middle_extended = middle_tip.y < middle_pip.y
        ring_extended = ring_tip.y < ring_pip.y
        pinky_extended = pinky_tip.y < pinky_pip.y

        # Thumb extended/folded detection inspired by exp1 logic
        # Determine orientation using thumb tip vs pinky tip along x-axis
        # If thumb tip is to the right of pinky tip, consider orientation A, else B
        if thumb_x > pinky_x:
            thumb_extended = thumb_x >= thumb_ip_x
        else:
            thumb_extended = thumb_x <= thumb_ip_x
        thumb_folded = not thumb_extended
        
        fingers_extended = [thumb_extended, index_extended, middle_extended, ring_extended, pinky_extended]
        all_folded = not any(fingers_extended)
        all_extended = all(fingers_extended)
        # Note: We no longer gate movement on thumb+index-only
        
        # Store gesture state
        gesture_state = {
            'thumb_index_distance': thumb_index_distance,
            'index_extended': index_extended,
            'index_pos': (index_x, index_y),
            'thumb_pos': (thumb_x, thumb_y),
            'thumb_folded': thumb_folded,
            'fingers_extended': fingers_extended,
            'all_folded': all_folded,
            'all_extended': all_extended
        }
        
        self.gesture_history.append(gesture_state)
        
        return gesture_state
    
    
    def handle_cursor_movement(self, gesture_state, frame_width, frame_height):
        """Handle smooth cursor movement; idle when all fingers folded"""
        index_x, index_y = gesture_state['index_pos']

        # Map to screen coordinates
        screen_x = int(self.screen_width / frame_width * index_x)
        screen_y = int(self.screen_height / frame_height * index_y)

        # Idle when all folded
        if gesture_state.get('all_folded', False):
            return self.prev_x, self.prev_y

        # If cursor is locked (during click gesture), keep it steady
        if self.cursor_locked:
            # Unlock when touch is over and extra lock time has passed
            if (not self.is_touching) and (time.time() > self.lock_release_time):
                self.cursor_locked = False
            else:
                pyautogui.moveTo(self.lock_pos[0], self.lock_pos[1], duration=0)
                return self.lock_pos[0], self.lock_pos[1]

        # Apply smoothing
        smooth_x, smooth_y = self.smooth_coordinates(screen_x, screen_y)
        # Move cursor
        pyautogui.moveTo(smooth_x, smooth_y, duration=0)
        return smooth_x, smooth_y
    
    def handle_click_gesture(self, gesture_state):
        """Handle click via double-touch of thumb and index (two quick touches => click)"""
        current_time = time.time()
        distance = gesture_state['thumb_index_distance']

        # Detect touch edges for debounced taps
        if distance < CLICK_THRESHOLD and not self.is_touching:
            self.is_touching = True

            # Lock cursor at current stable position for the duration of the touch
            try:
                self.lock_pos = pyautogui.position()
            except Exception:
                self.lock_pos = (self.prev_x, self.prev_y)
            self.cursor_locked = True

            # Double-tap detection window
            if current_time - self.last_click_time < DOUBLE_TAP_TIME:
                self.click_count += 1
            else:
                self.click_count = 1

            self.last_click_time = current_time

            if self.click_count == 2:
                # Single click on double-touch
                if current_time - self.last_gesture_time > GESTURE_COOLDOWN:
                    self.last_gesture_time = current_time
                    pyautogui.click()
                    self.click_visual_until = current_time + 0.3
                    print("Double-touch click!")
                    if self.mode == 'medical':
                        self.speak("Click")
                    self.click_count = 0
                    self.is_clicking = True
                    # Keep cursor locked briefly after the click to avoid post-click drift
                    self.lock_release_time = current_time + CLICK_LOCK_AFTER
                    return "double_touch_click"

        elif distance > CLICK_THRESHOLD + 8:
            # Reset touch state with hysteresis
            self.is_touching = False
            self.is_clicking = False
            # If the extra lock time has passed, unlock the cursor
            if time.time() > self.lock_release_time:
                self.cursor_locked = False

        return None
    
    # Pinch/drag feature removed
    
    def draw_ui_elements(self, frame, gesture_state, smooth_pos):
        """Draw UI elements and gesture indicators"""
        index_x, index_y = gesture_state['index_pos']
        thumb_x, thumb_y = gesture_state['thumb_pos']
        
        # Draw landmarks
        cv2.circle(frame, (index_x, index_y), 10, (0, 255, 0), cv2.FILLED)
        cv2.circle(frame, (thumb_x, thumb_y), 10, (255, 0, 0), cv2.FILLED)
        
        # Draw connection line between thumb and index
        cv2.line(frame, (thumb_x, thumb_y), (index_x, index_y), (255, 255, 0), 2)
        
        # Draw mode indicator
        cv2.putText(frame, f"Mode: {self.mode.title()}", (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        # Draw gesture status
        y_offset = 60
        
        if time.time() < self.click_visual_until:
            cv2.putText(frame, "CLICK: Active", (10, y_offset), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            y_offset += 30
        
        if self.cursor_locked:
            cv2.putText(frame, "Pointer Lock", (10, y_offset),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 215, 0), 2)
            y_offset += 28
        
        # Cursor activity
        cursor_active = not gesture_state.get('all_folded', False)
        cv2.putText(frame, f"Cursor: {'Active' if cursor_active else 'Idle'}", (10, y_offset), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0) if cursor_active else (0, 0, 255), 2)
        y_offset += 28

        # Per-finger status
        fingers = gesture_state.get('fingers_extended', [False]*5)
        labels = ['Thumb', 'Index', 'Middle', 'Ring', 'Pinky']
        for i, label in enumerate(labels):
            state_txt = 'Extended' if fingers[i] else 'Folded'
            color = (0, 255, 0) if fingers[i] else (0, 0, 255)
            cv2.putText(frame, f"{label}: {state_txt}", (10, y_offset),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
            y_offset += 20
        
        # Draw cursor position indicator
        cv2.circle(frame, (index_x, index_y), 20, (0, 255, 0), 2)
        
    def speak(self, text):
        """Speak text using voice engine (for medical mode)"""
        if self.voice_engine and self.mode == 'medical':
            try:
                self.voice_engine.say(text)
                self.voice_engine.runAndWait()
            except Exception as e:
                print(f"Voice error: {e}")
    
    def run(self):
        """Main application loop"""
        print(f"Hand Cursor Controller Started in {self.mode} mode!")
        print("Gestures:")
        print("- Move index finger to control cursor")
        print("- All fingers folded: Idle")
        print("- Double touch (Thumb+Index twice quickly): Click")
        print("- Press ESC to exit")
        
        if self.mode == 'medical':
            print("Medical Mode: Voice feedback enabled for safety")
            self.speak("Medical mode activated")
        elif self.mode == 'education':
            print("Education Mode: Presentation controls enabled")
        
        while True:
            success, frame = self.cap.read()
            if not success:
                print("Failed to read from camera")
                break
            
            # Flip frame horizontally for mirror effect
            frame = cv2.flip(frame, 1)
            frame_height, frame_width, _ = frame.shape
            
            # Convert to RGB for MediaPipe
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Process frame
            output = self.hand_detector.process(rgb_frame)
            
            # Check if hands are detected
            if output.multi_hand_landmarks:
                for hand in output.multi_hand_landmarks:
                    # Draw hand landmarks with upgraded drawing styles and connections
                    self.drawing_utils.draw_landmarks(
                        frame,
                        hand,
                        self.hands_module.HAND_CONNECTIONS,
                        self.drawing_styles.get_default_hand_landmarks_style(),
                        self.drawing_styles.get_default_hand_connections_style(),
                    )
                    
                    # Detect gestures
                    gesture_state = self.detect_gestures(
                        hand.landmark, frame_width, frame_height
                    )
                    
                    # Handle gestures first (may lock cursor)
                    self.handle_click_gesture(gesture_state)

                    # Handle cursor movement
                    smooth_pos = self.handle_cursor_movement(
                        gesture_state, frame_width, frame_height
                    )
                    
                    # Draw UI elements
                    self.draw_ui_elements(frame, gesture_state, smooth_pos)
            
            # Display frame
            cv2.imshow('Enhanced Hand Cursor Controller', frame)
            
            # Exit condition
            key = cv2.waitKey(1) & 0xFF
            if key == 27:  # ESC key
                break
        
        self.cleanup()
    
    def cleanup(self):
        """Clean up resources"""
        # Pinch/drag removed
        
        self.cap.release()
        cv2.destroyAllWindows()
        print("Hand Cursor Controller stopped.") 