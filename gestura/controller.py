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
# Scroll configuration
SCROLL_COOLDOWN = 0.25  # Minimum time between scroll events (seconds)
SCROLL_STEP = 120       # Amount to scroll per gesture (positive=up, negative=down)
# Converge point horizontal offset to the left of the hand (in hand widths)
LEFT_OFFSET_FACTOR = 1.1
# Hold and drag configuration
HOLD_THRESHOLD = 30     # Distance threshold for hold gesture (thumb-index + ring extended)
HOLD_MIN_TIME = 0.3     # Minimum time to maintain hold gesture before activating
DRAG_MIN_DISTANCE = 10  # Minimum cursor movement to start dragging

class HandCursorController:
    
    def __init__(self, mode='general', sensitivity=0.7, click_threshold=25, voice_enabled=True):
        self.cap = cv2.VideoCapture(0)
        self.cap.set(3, 1280)
        self.cap.set(4, 720)

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
        self.is_touching = False
        self.click_visual_until = 0
        
        # Gesture history
        self.gesture_history = deque(maxlen=5)
        self.last_scroll_time = 0.0
        
        # Cursor lock to stabilize clicks
        self.cursor_locked = False
        self.lock_pos = (0, 0)
        self.lock_release_time = 0.0
        # Single vs double click state
        self.pending_single_click = False
        
        # Hold and drag state management
        self.is_holding = False
        self.hold_start_time = 0
        self.hold_gesture_detected = False
        self.drag_start_pos = None
        self.is_dragging = False
        self.last_drag_pos = None
        
        # Mode and settings
        self.mode = mode
        self.sensitivity = sensitivity
        self.voice_enabled = voice_enabled
        
        global CLICK_THRESHOLD, SMOOTHING_FACTOR
        CLICK_THRESHOLD = click_threshold
        SMOOTHING_FACTOR = sensitivity
        
        self.voice_engine = None
        if self.mode == 'medical' and self.voice_enabled:
            try:
                import pyttsx3
                self.voice_engine = pyttsx3.init()
                self.voice_engine.setProperty('rate', 150)
            except Exception as e:
                print(f"Voice engine initialization failed: {e}")
        
        pyautogui.FAILSAFE = False
        pyautogui.PAUSE = 0
        # Visual feedback state
        self.last_click_label = ""
    
    @staticmethod
    def calculate_distance(point1, point2):
        return math.sqrt((point1[0] - point2[0])**2 + (point1[1] - point2[1])**2)
    
    def smooth_coordinates(self, x, y):
        if self.is_first_frame:
            self.prev_x = x
            self.prev_y = y
            self.is_first_frame = False
            return x, y

        self.position_history.append((x, y))
        xs = [p[0] for p in self.position_history]
        ys = [p[1] for p in self.position_history]
        median_x = int(statistics.median(xs))
        median_y = int(statistics.median(ys))

        smooth_x = int(SMOOTHING_FACTOR * self.prev_x + (1 - SMOOTHING_FACTOR) * median_x)
        smooth_y = int(SMOOTHING_FACTOR * self.prev_y + (1 - SMOOTHING_FACTOR) * median_y)

        if math.hypot(smooth_x - self.prev_x, smooth_y - self.prev_y) < DEADZONE_PIXELS:
            return self.prev_x, self.prev_y

        self.prev_x = smooth_x
        self.prev_y = smooth_y
        return smooth_x, smooth_y

    def compute_line_cursor_from_fingers(self, segments, frame_width, frame_height):
        """Compute stable cursor as median of pairwise intersections of MCP→tip lines."""
        if not segments or len(segments) < 2:
            return None
        intersections = []
        for i in range(len(segments)):
            (x1, y1), (x2, y2) = segments[i]
            v1x, v1y = x2 - x1, y2 - y1
            if abs(v1x) + abs(v1y) < 1e-6:
                continue
            for j in range(i + 1, len(segments)):
                (x3, y3), (x4, y4) = segments[j]
                v2x, v2y = x4 - x3, y4 - y3
                if abs(v2x) + abs(v2y) < 1e-6:
                    continue
                det = v1x * v2y - v1y * v2x
                if abs(det) < 1e-6:
                    continue
                dx, dy = x3 - x1, y3 - y1
                t = (dx * v2y - dy * v2x) / det
                xi = int(x1 + t * v1x)
                yi = int(y1 + t * v1y)
                xi = max(0, min(frame_width - 1, xi))
                yi = max(0, min(frame_height - 1, yi))
                intersections.append((xi, yi))
        if not intersections:
            return None
        xs = [p[0] for p in intersections]
        ys = [p[1] for p in intersections]
        return int(statistics.median(xs)), int(statistics.median(ys))
    
    def detect_gestures(self, landmarks, frame_width, frame_height):
        # Landmarks we need
        index_tip = landmarks[8]
        middle_tip = landmarks[12]
        ring_tip = landmarks[16]
        thumb_tip = landmarks[4]
        # PIP joints for extension detection
        index_pip = landmarks[6]
        middle_pip = landmarks[10]
        ring_pip = landmarks[14]
        pinky_tip = landmarks[20]
        pinky_pip = landmarks[18]
        # MCP joints (palm area bases)
        index_mcp = landmarks[5]
        middle_mcp = landmarks[9]
        ring_mcp = landmarks[13]

        # Pixels for tips (used for click distance and optional display)
        index_x = int(index_tip.x * frame_width)
        index_y = int(index_tip.y * frame_height)
        thumb_x = int(thumb_tip.x * frame_width)
        thumb_y = int(thumb_tip.y * frame_height)

        # Pixels for MCP bases
        ixm, iym = int(index_mcp.x * frame_width), int(index_mcp.y * frame_height)
        mxm, mym = int(middle_mcp.x * frame_width), int(middle_mcp.y * frame_height)
        rxm, rym = int(ring_mcp.x * frame_width), int(ring_mcp.y * frame_height)

        # Compute a single target point to the LEFT of the hand (converge point)
        min_x = min(ixm, mxm, rxm)
        max_x = max(ixm, mxm, rxm)
        hand_w = max(20, max_x - min_x)
        target_x = max(0, min_x - int(LEFT_OFFSET_FACTOR * hand_w))
        target_y = int((iym + mym + rym) / 3)
        converge_point = (target_x, target_y)

        # Build three lines converging to the same point
        segments = [
            ((ixm, iym), converge_point),
            ((mxm, mym), converge_point),
            ((rxm, rym), converge_point),
        ]

        # Cursor equals converge point (then smoothed/mapped to screen later)
        line_cursor = converge_point

        gesture_state = {
            'thumb_index_distance': self.calculate_distance((thumb_x, thumb_y), (index_x, index_y)),
            'index_pos': (index_x, index_y),
            'thumb_pos': (thumb_x, thumb_y),
            'ring_pos': (int(ring_tip.x * frame_width), int(ring_tip.y * frame_height)),
            'line_segments': segments,
            'line_cursor': line_cursor,
            # Finger extension booleans for scroll gestures [thumb,index,middle,ring,pinky]
            'fingers_extended': [
                False,  # we don't need thumb for this simple scroll
                index_tip.y < index_pip.y,
                middle_tip.y < middle_pip.y,
                ring_tip.y < ring_pip.y,
                pinky_tip.y < pinky_pip.y,
            ],
        }
        self.gesture_history.append(gesture_state)
        return gesture_state
    
    def handle_cursor_movement(self, gesture_state, frame_width, frame_height):
        # Prefer line-based cursor (no idle gating)
        ix, iy = gesture_state['index_pos']
        cx, cy = gesture_state.get('line_cursor', (ix, iy))

        screen_x = int(self.screen_width / frame_width * cx)
        screen_y = int(self.screen_height / frame_height * cy)

        # Don't lock cursor if we're in hold/drag mode to allow smooth dragging
        if self.cursor_locked and not (self.is_holding or self.is_dragging):
            if (not self.is_touching) and (time.time() > self.lock_release_time):
                self.cursor_locked = False
            else:
                pyautogui.moveTo(self.lock_pos[0], self.lock_pos[1], duration=0)
                return self.lock_pos[0], self.lock_pos[1]

        smooth_x, smooth_y = self.smooth_coordinates(screen_x, screen_y)
        
        # Move cursor normally, even during drag operations
        pyautogui.moveTo(smooth_x, smooth_y, duration=0)
        return smooth_x, smooth_y
    
    def handle_click_gesture(self, gesture_state):
        current_time = time.time()
        distance = gesture_state['thumb_index_distance']

        # If a single click is pending and no second touch happened in time, fire it
        if self.pending_single_click and (not self.is_touching) and (current_time - self.last_click_time >= DOUBLE_TAP_TIME):
            if current_time - self.last_gesture_time > GESTURE_COOLDOWN:
                self.last_gesture_time = current_time
                pyautogui.click()
                self.last_click_label = "Click"
                self.click_visual_until = current_time + 0.35
                self.is_clicking = True
                self.lock_release_time = current_time + CLICK_LOCK_AFTER
            self.pending_single_click = False
            return "single_click"

        # Touch edge detection
        if distance < CLICK_THRESHOLD and not self.is_touching:
            self.is_touching = True
            try:
                self.lock_pos = pyautogui.position()
            except Exception:
                self.lock_pos = (self.prev_x, self.prev_y)
            self.cursor_locked = True

            # If a single click was pending and we got a second touch within window => double-click
            if self.pending_single_click and (current_time - self.last_click_time <= DOUBLE_TAP_TIME):
                if current_time - self.last_gesture_time > GESTURE_COOLDOWN:
                    self.last_gesture_time = current_time
                    pyautogui.doubleClick()
                    self.last_click_label = "Double Click"
                    self.click_visual_until = current_time + 0.45
                    self.is_clicking = True
                    self.lock_release_time = current_time + CLICK_LOCK_AFTER
                self.pending_single_click = False
                return "double_click"

            # Otherwise, start a pending single click and wait to see if a second touch arrives
            self.pending_single_click = True
            self.last_click_time = current_time
            return None

        elif distance > CLICK_THRESHOLD + 8:
            self.is_touching = False
            self.is_clicking = False
            if time.time() > self.lock_release_time:
                self.cursor_locked = False
        return None

    def handle_scroll_gesture(self, gesture_state):
        """Perform scroll based on finger pattern:
        - [0,1,0,0,0] (only index extended) => scroll up
        - [0,1,1,0,0] (index + middle extended) => scroll down
        Debounced by SCROLL_COOLDOWN.
        """
        now = time.time()
        if now - self.last_scroll_time < SCROLL_COOLDOWN:
            return None

        fingers = gesture_state.get('fingers_extended') or [False, False, False, False, False]
        # Zero out thumb if present
        pattern = [0, 1 if fingers[1] else 0, 1 if fingers[2] else 0, 1 if fingers[3] else 0, 1 if fingers[4] else 0]

        # Only index extended => scroll up
        if pattern == [0,1,0,0,0]:
            pyautogui.scroll(SCROLL_STEP)
            self.last_scroll_time = now
            self.last_click_label = "Scroll Up"
            self.click_visual_until = now + 0.3
            return "scroll_up"

        # Index + middle extended => scroll down
        if pattern == [0,1,1,0,0]:
            pyautogui.scroll(-SCROLL_STEP)
            self.last_scroll_time = now
            self.last_click_label = "Scroll Down"
            self.click_visual_until = now + 0.3
            return "scroll_down"

        return None
    
    def handle_hold_and_drag_gesture(self, gesture_state, current_cursor_pos):
        """Handle hold gesture (ring finger extended + thumb-index close) and drag functionality."""
        current_time = time.time()
        distance = gesture_state['thumb_index_distance']
        fingers = gesture_state.get('fingers_extended', [False, False, False, False, False])
        ring_extended = fingers[3]  # Ring finger extended
        
        # Hold gesture: Ring finger extended + thumb-index close
        hold_gesture_active = ring_extended and distance < HOLD_THRESHOLD
        
        if hold_gesture_active and not self.hold_gesture_detected:
            # Start detecting hold gesture
            self.hold_gesture_detected = True
            self.hold_start_time = current_time
            self.drag_start_pos = current_cursor_pos
            self.last_drag_pos = current_cursor_pos
            return None
        
        elif hold_gesture_active and self.hold_gesture_detected:
            # Continue hold gesture - check if minimum time has passed
            if current_time - self.hold_start_time >= HOLD_MIN_TIME and not self.is_holding:
                # Start holding
                self.is_holding = True
                pyautogui.mouseDown()
                self.last_click_label = "Hold Start"
                self.click_visual_until = current_time + 0.5
                if self.voice_engine and self.mode == 'medical':
                    self.speak("Hold activated")
                return "hold_start"
            
            elif self.is_holding:
                # Already holding - handle dragging
                if self.drag_start_pos:
                    drag_distance = self.calculate_distance(current_cursor_pos, self.drag_start_pos)
                    if drag_distance > DRAG_MIN_DISTANCE and not self.is_dragging:
                        # Start dragging
                        self.is_dragging = True
                        self.last_click_label = "Drag Start"
                        self.click_visual_until = current_time + 0.3
                        return "drag_start"
                    
                    elif self.is_dragging:
                        # Continue dragging
                        move_distance = self.calculate_distance(current_cursor_pos, self.last_drag_pos)
                        if move_distance > 3:  # Only update for significant movement
                            self.last_drag_pos = current_cursor_pos
                            self.last_click_label = "Dragging"
                            self.click_visual_until = current_time + 0.1
                            return "dragging"
        
        elif not hold_gesture_active and (self.hold_gesture_detected or self.is_holding):
            # Release hold gesture
            if self.is_holding:
                pyautogui.mouseUp()
                if self.is_dragging:
                    self.last_click_label = "Drag End"
                    if self.voice_engine and self.mode == 'medical':
                        self.speak("Drag completed")
                else:
                    self.last_click_label = "Hold End"
                    if self.voice_engine and self.mode == 'medical':
                        self.speak("Hold released")
                self.click_visual_until = current_time + 0.4
            
            # Reset all hold/drag states
            self.is_holding = False
            self.hold_gesture_detected = False
            self.is_dragging = False
            self.drag_start_pos = None
            self.last_drag_pos = None
            self.hold_start_time = 0
            
            return "hold_end"
        
        return None
    
    def draw_ui_elements(self, frame, gesture_state, smooth_pos):
        ix, iy = gesture_state['index_pos']
        tx, ty = gesture_state['thumb_pos']
        rx, ry = gesture_state.get('ring_pos', (0, 0))

        # Draw three control lines in fixed colors: index=red, middle=violet, ring=yellow
        segs = gesture_state.get('line_segments', [])
        colors = [(0, 0, 255), (255, 0, 255), (0, 255, 255)]  # BGR: red, violet, yellow
        for k, (p0, p1) in enumerate(segs[:3]):
            cv2.line(frame, p0, p1, colors[k], 3)

        # Click detection visuals around index finger
        dist = gesture_state.get('thumb_index_distance', 9999)
        # Always show a big ring around the index fingertip to indicate click range
        cv2.circle(frame, (ix, iy), CLICK_THRESHOLD, (0, 200, 255), 2)
        # Draw the helper line between thumb and index
        cv2.line(frame, (tx, ty), (ix, iy), (255, 255, 0), 2)
        # If inside threshold, highlight the ring and fingertip
        if dist <= CLICK_THRESHOLD:
            cv2.circle(frame, (ix, iy), CLICK_THRESHOLD + 6, (0, 255, 0), 2)
            cv2.circle(frame, (ix, iy), 8, (0, 255, 0), cv2.FILLED)

        # Hold/Drag gesture visuals
        fingers = gesture_state.get('fingers_extended', [False, False, False, False, False])
        if fingers[3]:  # Ring finger extended
            # Draw ring finger indicator
            cv2.circle(frame, (rx, ry), 8, (255, 0, 255), cv2.FILLED)  # Magenta dot
            cv2.circle(frame, (rx, ry), 15, (255, 0, 255), 2)  # Magenta ring
            
            # If hold gesture is active, show additional feedback
            if dist < HOLD_THRESHOLD:
                cv2.putText(frame, "HOLD GESTURE", (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 255), 2)
                
                if self.is_holding:
                    cv2.circle(frame, (ix, iy), 25, (0, 255, 255), 3)  # Yellow hold indicator
                    if self.is_dragging:
                        cv2.putText(frame, "DRAGGING", (10, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)

        # Mark the converge point clearly (black dot with green ring)
        cur = gesture_state.get('line_cursor', (ix, iy))
        cv2.circle(frame, cur, 6, (0, 0, 0), cv2.FILLED)
        cv2.circle(frame, cur, 12, (0, 255, 0), 2)

        # Transient on-screen feedback for clicks and actions
        if time.time() < getattr(self, 'click_visual_until', 0):
            label = getattr(self, 'last_click_label', '')
            if label:
                if "Hold" in label or "Drag" in label:
                    color = (255, 0, 255)  # Magenta for hold/drag actions
                elif "Scroll" in label:
                    color = (0, 0, 255)    # Red for scroll actions
                else:
                    color = (0, 255, 0)    # Green for click actions
                cv2.putText(frame, label, (10, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 2)
    
    def speak(self, text):
        if self.voice_engine and self.mode == 'medical':
            try:
                self.voice_engine.say(text)
                self.voice_engine.runAndWait()
            except Exception as e:
                print(f"Voice error: {e}")
    
    def run(self):
        print(f"Hand Cursor Controller (test1) Started in {self.mode} mode!")
        print("Gestures:")
        print("- Cursor from finger-line intersection (MCP→tip)")
        print("- Thumb+Index touch: Click")
        print("- Thumb+Index double touch: Double Click")
        print("- Ring finger extended + Thumb+Index close: Hold/Drag")
        print("- Index finger only: Scroll Up")
        print("- Index+Middle fingers: Scroll Down")
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
            frame = cv2.flip(frame, 1)
            frame_height, frame_width, _ = frame.shape
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            output = self.hand_detector.process(rgb_frame)
            if output.multi_hand_landmarks:
                for hand in output.multi_hand_landmarks:
                    self.drawing_utils.draw_landmarks(
                        frame,
                        hand,
                        self.hands_module.HAND_CONNECTIONS,
                        self.drawing_styles.get_default_hand_landmarks_style(),
                        self.drawing_styles.get_default_hand_connections_style(),
                    )
                    gesture_state = self.detect_gestures(hand.landmark, frame_width, frame_height)
                    smooth_pos = self.handle_cursor_movement(gesture_state, frame_width, frame_height)
                    self.handle_click_gesture(gesture_state)
                    self.handle_scroll_gesture(gesture_state)
                    self.handle_hold_and_drag_gesture(gesture_state, smooth_pos)
                    self.draw_ui_elements(frame, gesture_state, smooth_pos)
            else:
                # Safety: Release mouse button if hand is lost during hold
                if self.is_holding:
                    pyautogui.mouseUp()
                    self.is_holding = False
                    self.hold_gesture_detected = False
                    self.is_dragging = False
                    self.drag_start_pos = None
                    self.last_drag_pos = None
                    self.last_click_label = "Hold Released (Hand Lost)"
                    self.click_visual_until = time.time() + 0.5
                    if self.voice_engine and self.mode == 'medical':
                        self.speak("Hold released due to hand tracking loss")
            cv2.imshow('Hand Cursor Controller (test1)', frame)
            key = cv2.waitKey(1) & 0xFF
            if key == 27:
                break
        self.cleanup()
    
    def cleanup(self):
        # Safety: Ensure mouse button is released
        if self.is_holding:
            pyautogui.mouseUp()
            print("Released held mouse button during cleanup")
        
        self.cap.release()
        cv2.destroyAllWindows()
        print("Hand Cursor Controller (test1) stopped.")
