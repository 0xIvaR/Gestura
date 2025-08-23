import cv2
import mediapipe as mp
import pyautogui
import time
from collections import deque
import math

# Configuration
SMOOTHING_FACTOR = 0.7  # Higher = more smoothing
CLICK_THRESHOLD = 25    # Distance threshold for click gesture
PINCH_THRESHOLD = 30    # Distance threshold for pinch gesture
DOUBLE_TAP_TIME = 0.5   # Time window for double tap (seconds)
GESTURE_COOLDOWN = 0.3  # Cooldown between gestures

class HandCursorController:
    def __init__(self, mode='general', sensitivity=0.7, click_threshold=25, voice_enabled=True):
        self.cap = cv2.VideoCapture(0)
        self.hand_detector = mp.solutions.hands.Hands(
            max_num_hands=1,
            min_detection_confidence=0.8,
            min_tracking_confidence=0.8
        )
        self.drawing_utils = mp.solutions.drawing_utils
        self.screen_width, self.screen_height = pyautogui.size()
        
        # Smoothing variables
        self.prev_x = 0
        self.prev_y = 0
        self.is_first_frame = True
        
        # Gesture state management
        self.is_pinching = False
        self.is_clicking = False
        self.last_click_time = 0
        self.click_count = 0
        self.last_gesture_time = 0
        
        # Gesture history for better detection
        self.gesture_history = deque(maxlen=5)
        
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
        """Apply exponential moving average for smooth cursor movement"""
        if self.is_first_frame:
            self.prev_x = x
            self.prev_y = y
            self.is_first_frame = False
            return x, y
        
        # Exponential moving average
        smooth_x = int(SMOOTHING_FACTOR * self.prev_x + (1 - SMOOTHING_FACTOR) * x)
        smooth_y = int(SMOOTHING_FACTOR * self.prev_y + (1 - SMOOTHING_FACTOR) * y)
        
        self.prev_x = smooth_x
        self.prev_y = smooth_y
        
        return smooth_x, smooth_y
    
    def detect_gestures(self, landmarks, frame_width, frame_height):
        """Detect various hand gestures"""
        # Get key landmark positions
        index_tip = landmarks[8]   # Index finger tip
        index_pip = landmarks[6]   # Index finger PIP joint
        thumb_tip = landmarks[4]   # Thumb tip
        
        # Convert to pixel coordinates
        index_x = int(index_tip.x * frame_width)
        index_y = int(index_tip.y * frame_height)
        thumb_x = int(thumb_tip.x * frame_width)
        thumb_y = int(thumb_tip.y * frame_height)
        
        # Calculate distances
        thumb_index_distance = self.calculate_distance(
            (thumb_x, thumb_y), (index_x, index_y)
        )
        
        # Check if fingers are extended (for better gesture recognition)
        index_extended = index_tip.y < index_pip.y
        
        # Store gesture state
        gesture_state = {
            'thumb_index_distance': thumb_index_distance,
            'index_extended': index_extended,
            'index_pos': (index_x, index_y),
            'thumb_pos': (thumb_x, thumb_y)
        }
        
        self.gesture_history.append(gesture_state)
        
        return gesture_state
    
    def handle_cursor_movement(self, gesture_state, frame_width, frame_height):
        """Handle smooth cursor movement"""
        index_x, index_y = gesture_state['index_pos']
        
        # Map to screen coordinates
        screen_x = int(self.screen_width / frame_width * index_x)
        screen_y = int(self.screen_height / frame_height * index_y)
        
        # Apply smoothing
        smooth_x, smooth_y = self.smooth_coordinates(screen_x, screen_y)
        
        # Move cursor
        pyautogui.moveTo(smooth_x, smooth_y, duration=0)
        
        return smooth_x, smooth_y
    
    def handle_click_gesture(self, gesture_state):
        """Handle click and double-tap gestures"""
        current_time = time.time()
        thumb_index_distance = gesture_state['thumb_index_distance']
        
        # Check for click gesture (thumb and index close together)
        if thumb_index_distance < CLICK_THRESHOLD and not self.is_clicking:
            if current_time - self.last_gesture_time > GESTURE_COOLDOWN:
                self.is_clicking = True
                self.last_gesture_time = current_time
                
                # Check for double tap
                if current_time - self.last_click_time < DOUBLE_TAP_TIME:
                    self.click_count += 1
                    if self.click_count == 2:
                        pyautogui.doubleClick()
                        self.click_count = 0
                        print("Double tap detected!")
                        return "double_tap"
                else:
                    self.click_count = 1
                
                self.last_click_time = current_time
                pyautogui.click()
                print("Single click detected!")
                if self.mode == 'medical':
                    self.speak("Click confirmed")
                return "single_click"
        
        elif thumb_index_distance > CLICK_THRESHOLD + 10:  # Hysteresis
            self.is_clicking = False
        
        return None
    
    def handle_pinch_gesture(self, gesture_state):
        """Handle pinch gesture for text selection"""
        thumb_index_distance = gesture_state['thumb_index_distance']
        
        # Pinch gesture (slightly larger distance than click)
        if CLICK_THRESHOLD < thumb_index_distance < PINCH_THRESHOLD:
            if not self.is_pinching:
                self.is_pinching = True
                pyautogui.mouseDown()
                print("Pinch started - text selection mode!")
                return "pinch_start"
        elif thumb_index_distance > PINCH_THRESHOLD + 10:  # Hysteresis
            if self.is_pinching:
                self.is_pinching = False
                pyautogui.mouseUp()
                print("Pinch ended - text selection complete!")
                return "pinch_end"
        
        return "pinch_active" if self.is_pinching else None
    
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
        if self.is_pinching:
            cv2.putText(frame, "PINCH: Text Selection Active", (10, y_offset), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
            y_offset += 30
        
        if self.is_clicking:
            cv2.putText(frame, "CLICK: Active", (10, y_offset), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            y_offset += 30
        
        # Draw distance indicator
        distance = gesture_state['thumb_index_distance']
        cv2.putText(frame, f"Distance: {distance:.1f}", (10, y_offset), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
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
        print("- Pinch (thumb + index close): Click")
        print("- Pinch twice quickly: Double click")
        print("- Partial pinch: Hold and drag for text selection")
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
                    # Draw hand landmarks
                    self.drawing_utils.draw_landmarks(frame, hand)
                    
                    # Detect gestures
                    gesture_state = self.detect_gestures(
                        hand.landmark, frame_width, frame_height
                    )
                    
                    # Handle cursor movement
                    smooth_pos = self.handle_cursor_movement(
                        gesture_state, frame_width, frame_height
                    )
                    
                    # Handle gestures
                    self.handle_click_gesture(gesture_state)
                    self.handle_pinch_gesture(gesture_state)
                    
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
        if self.is_pinching:
            pyautogui.mouseUp()
        
        self.cap.release()
        cv2.destroyAllWindows()
        print("Hand Cursor Controller stopped.") 