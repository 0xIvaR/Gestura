# Gestura

**Gestura** is an advanced touchless hand gesture control system that uses computer vision to control your cursor with natural hand movements. Built with OpenCV and MediaPipe, Gestura features a sophisticated line-based cursor tracking system, multiple operation modes, and comprehensive gesture support including clicks, double-clicks, scrolling, and drag-and-drop functionality.

---

## 🚀 Key Features

### Advanced Cursor Control
- **Line-Based Tracking**: Uses multiple finger lines (MCP→tip) to compute a stable, accurate cursor position
- **Smart Smoothing**: Median filter with configurable smoothing factor for jitter-free cursor movement
- **Dead Zone**: Ignores micro-movements under 4 pixels to prevent cursor drift
- **Cursor Lock**: Stabilizes cursor during click operations to prevent accidental drift

### Comprehensive Gesture Support
- **Single Click**: Touch thumb and index finger together
- **Double Click**: Quick double-touch within 0.5 seconds
- **Hold & Drag**: Ring finger extended + thumb-index close gesture for drag operations
- **Scroll Up**: Index finger only extended
- **Scroll Down**: Index and middle fingers extended together

### Three Operating Modes
1. **General Mode**: Standard cursor control for everyday use
2. **Medical Mode**: Sterile control with voice feedback for medical procedures
3. **Education Mode**: Presentation-friendly controls for teaching environments

### Intelligent Features
- **Hand Tracking**: Supports detection with MediaPipe (up to 2 hands)
- **Visual Feedback**: Color-coded finger lines and on-screen gesture labels
- **Voice Feedback**: Optional TTS announcements in Medical mode
- **Auto-Recovery**: Releases held mouse button if hand tracking is lost
- **Persistent Settings**: All configurations saved to `config.json`

---

## 🎯 Gesture Controls

### Cursor Movement
- **Control**: Natural hand movement in front of camera
- **Tracking**: Uses intersection of three finger lines (Index, Middle, Ring) converging to a point left of the hand
- **Visual**: Green ring marks the converge point (cursor position)
- **Smoothing**: Configurable smoothing factor (default: 0.7)

### Click Gestures

#### Single Click
- **Gesture**: Touch thumb tip to index fingertip
- **Threshold**: Distance < 25 pixels (default)
- **Visual**: Orange circle around index finger shows click range
- **Feedback**: Green "Click" label appears on screen

#### Double Click
- **Gesture**: Two quick thumb-index touches within 0.5 seconds
- **Timing**: DOUBLE_TAP_TIME = 0.5 seconds
- **Visual**: Green "Double Click" label appears on screen
- **Note**: Uses smart detection to distinguish from single clicks

### Hold & Drag
- **Gesture**: Ring finger extended + thumb-index close
- **Hold Threshold**: Distance < 30 pixels
- **Minimum Hold Time**: 0.3 seconds before activation
- **Drag Start**: Minimum 10 pixels movement
- **Visual**: Magenta indicators for ring finger, yellow ring for active hold
- **Feedback**: "Hold Start", "Dragging", "Drag End" labels
- **Voice**: Announces "Hold activated" and "Drag completed" in Medical mode

### Scroll Gestures

#### Scroll Up
- **Gesture**: Index finger only extended (other fingers closed)
- **Pattern**: [0,1,0,0,0] finger state
- **Amount**: 120 pixels per scroll
- **Cooldown**: 0.25 seconds between scrolls
- **Visual**: Red "Scroll Up" label

#### Scroll Down
- **Gesture**: Index and middle fingers extended (others closed)
- **Pattern**: [0,1,1,0,0] finger state
- **Amount**: -120 pixels per scroll
- **Cooldown**: 0.25 seconds between scrolls
- **Visual**: Red "Scroll Down" label

---

## ⚙️ Configuration & Thresholds

### Core Parameters

| Parameter | Default | Range | Description |
|-----------|---------|-------|-------------|
| `SMOOTHING_FACTOR` | 0.7 | 0.1 - 1.0 | Higher = more smoothing, less jitter |
| `CLICK_THRESHOLD` | 25 | 15 - 50 | Distance threshold for click detection (pixels) |
| `DOUBLE_TAP_TIME` | 0.5 | - | Time window for double-click detection (seconds) |
| `GESTURE_COOLDOWN` | 0.3 | - | Minimum time between gesture actions (seconds) |
| `DEADZONE_PIXELS` | 4 | - | Ignores movements smaller than this |
| `MEDIAN_WINDOW` | 5 | - | Number of points for median filter |
| `CLICK_LOCK_AFTER` | 0.15 | - | Extra cursor lock time after clicking (seconds) |

### Scroll Configuration

| Parameter | Default | Description |
|-----------|---------|-------------|
| `SCROLL_COOLDOWN` | 0.25 | Minimum time between scroll events (seconds) |
| `SCROLL_STEP` | 120 | Amount to scroll per gesture (positive=up, negative=down) |

### Hold & Drag Configuration

| Parameter | Default | Description |
|-----------|---------|-------------|
| `HOLD_THRESHOLD` | 30 | Distance threshold for hold gesture (pixels) |
| `HOLD_MIN_TIME` | 0.3 | Minimum time to maintain hold before activating (seconds) |
| `DRAG_MIN_DISTANCE` | 10 | Minimum cursor movement to start dragging (pixels) |

### Cursor Tracking Configuration

| Parameter | Default | Description |
|-----------|---------|-------------|
| `LEFT_OFFSET_FACTOR` | 1.1 | Horizontal offset multiplier for converge point |

### Camera Settings

| Setting | Value |
|---------|-------|
| Resolution | 1280 x 720 |
| Camera Index | 0 (default webcam) |

### MediaPipe Hand Detection

| Parameter | Value |
|-----------|-------|
| `static_image_mode` | False |
| `max_num_hands` | 2 |
| `min_detection_confidence` | 0.5 |
| `min_tracking_confidence` | 0.8 |

---

## 📋 Requirements

### System Requirements
- **Python**: 3.8 or higher
- **Camera**: Working webcam or external camera
- **OS**: Windows, macOS, or Linux (tested on Windows)
- **RAM**: 4GB minimum (8GB recommended)

### Python Dependencies

```
opencv-python      # Computer vision and camera handling
mediapipe          # Hand tracking and landmark detection
pyautogui          # System-level cursor control
pyttsx3            # Text-to-speech for Medical mode
speechrecognition  # Future voice command support
pytest             # Testing framework
pyinstaller        # Optional: for building executables
pydantic           # Data validation (for future features)
fastapi            # API framework (for future features)
```

---

## 🔧 Installation

### 1. Clone the Repository
```bash
git clone <repository-url>
cd Gestura
```

### 2. Create Virtual Environment (Recommended)

**Windows (PowerShell):**
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

**macOS/Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

---

## 🎮 Usage

### Launch the GUI Application

**Method 1:**
```bash
python -m src.main
```

**Method 2:**
```bash
python src/main.py
```

### GUI Controls

1. **Select Mode**: Choose between General, Medical, or Education mode
2. **Adjust Settings**:
   - **Gesture Sensitivity**: Slide from 0.1 (responsive) to 1.0 (smooth)
   - **Click Threshold**: Adjust from 15 (sensitive) to 50 (requires closer touch)
   - **Voice Feedback**: Toggle for Medical mode announcements
3. **Start Control**: Click "Start Gesture Control" to begin
4. **Stop Control**: Press ESC in the camera window or click "Stop Gesture Control"

### Configuration File

Settings are automatically saved to `config.json`:

```json
{
  "sensitivity": 0.7,
  "click_threshold": 25,
  "voice_enabled": true,
  "mode": "general"
}
```

---

## 🎨 Visual Feedback System

### Color-Coded Finger Lines
- **Red Line**: Index finger (MCP → converge point)
- **Violet Line**: Middle finger (MCP → converge point)
- **Yellow Line**: Ring finger (MCP → converge point)

### Cursor Indicators
- **Green Ring (12px)**: Marks the converge point (cursor position)
- **Black Dot (6px)**: Center of cursor position

### Click Visual Indicators
- **Orange Circle**: Shows click threshold range around index finger
- **Green Circle + Fill**: Appears when within click threshold
- **Cyan Line**: Connects thumb and index during click detection

### Hold & Drag Indicators
- **Magenta Dot + Ring**: Shows ring finger position when extended
- **Yellow Circle**: Appears around index finger during active hold
- **On-Screen Labels**:
  - Green: Click/Double-Click actions
  - Magenta: Hold/Drag actions
  - Red: Scroll actions

---

## 🏥 Operating Modes

### General Mode
- **Purpose**: Standard everyday cursor control
- **Features**: All gestures enabled, optimal performance
- **Best For**: Regular computer use, gaming, browsing

### Medical Mode
- **Purpose**: Sterile control for medical environments
- **Features**:
  - Voice feedback for all actions
  - Announces "Medical mode activated" on start
  - Speaks "Hold activated", "Drag completed", etc.
  - TTS rate: 150 WPM
- **Best For**: Surgical settings, medical imaging review, sterile environments

### Education Mode
- **Purpose**: Presentation and teaching scenarios
- **Features**: Enhanced presentation controls
- **Best For**: Lectures, remote teaching, demonstrations

---

## 🏗️ Project Structure

```
Gestura/
├─ src/
│  ├─ main.py           # Entry point - launches GUI
│  ├─ gui.py            # Tkinter GUI with settings management
│  ├─ controller.py     # Hand tracking and gesture recognition
│  ├─ inter.py          # Utility script
│  ├─ config.json       # Persistent settings (auto-created)
│  └─ __init__.py
├─ tests/               # Test implementations
│  ├─ test1/            # Basic prototype tests
│  ├─ test2/            # Enhanced features tests
│  ├─ test3-app/        # App integration tests
│  └─ test4/            # Advanced features tests
├─ assets/              # Experimental code and resources
│  ├─ exp1/
│  └─ exp2/
├─ App/                 # Future Electron app
│  └─ gestura-app/
├─ requirements.txt     # Python dependencies
├─ README.md           # This file
└─ .gitignore
```

---

## 🐛 Troubleshooting

### Camera Issues

**Problem**: "Failed to read from camera"
- **Solution 1**: Close other apps using the webcam (Zoom, Teams, etc.)
- **Solution 2**: Change camera index in `controller.py`: `cv2.VideoCapture(1)` or `(2)`
- **Solution 3**: Check camera permissions in system settings

### Cursor Performance

**Problem**: Cursor is jittery or jumps around
- **Solution**: Increase `sensitivity` slider (move toward 1.0)
- **Tip**: Higher values = smoother but slower response

**Problem**: Cursor moves too slowly
- **Solution**: Decrease `sensitivity` slider (move toward 0.1)
- **Tip**: Lower values = faster but potentially more jitter

### Gesture Detection

**Problem**: Clicks not detected
- **Solution 1**: Lower `click_threshold` (move slider left)
- **Solution 2**: Ensure good lighting conditions
- **Solution 3**: Keep hand 12-18 inches from camera
- **Solution 4**: Make sure fingers are clearly visible (no overlapping)

**Problem**: Accidental clicks
- **Solution**: Increase `click_threshold` (move slider right)
- **Tip**: Default 25 pixels works for most users

**Problem**: Drag operations not working
- **Solution 1**: Extend ring finger clearly while pinching thumb-index
- **Solution 2**: Hold the gesture for at least 0.3 seconds before moving
- **Solution 3**: Move at least 10 pixels before drag is recognized

### Voice Feedback

**Problem**: Voice not working in Medical mode
- **Solution 1**: Ensure `pyttsx3` is installed: `pip install pyttsx3`
- **Solution 2**: Windows: Check TTS engines in Control Panel
- **Solution 3**: macOS: Voice feedback should work by default
- **Solution 4**: Linux: Install `espeak`: `sudo apt-get install espeak`

### Application Issues

**Problem**: App freezes on start
- **Solution 1**: Update Python packages: `pip install --upgrade -r requirements.txt`
- **Solution 2**: Restart computer and camera
- **Solution 3**: Check Python version (3.8+ required)

**Problem**: High CPU usage
- **Solution**: Reduce camera resolution in `controller.py` (change from 1280x720 to 640x480)

---

## 🔬 Development

### Running Tests
```bash
pytest -q
```

### Code Style
- Readable variable names
- Early returns to avoid deep nesting
- Type hints where applicable
- Comprehensive comments for complex logic

### Contributing
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

---

## 📦 Building Executable

Package Gestura as a standalone application:

```bash
pyinstaller --noconfirm --onefile --windowed --name Gestura src/main.py
```

**Note**: You may need to manually include MediaPipe and OpenCV data files depending on your platform.

---

## 🔐 Safety Features

- **Auto-Release**: Automatically releases mouse button if hand tracking is lost during hold/drag
- **Failsafe**: PyAutoGUI failsafe disabled for smooth operation, but ESC key always exits
- **Cursor Lock**: Prevents accidental movement during clicks
- **Gesture Cooldown**: Prevents rapid-fire unintended actions
- **Dead Zone**: Eliminates micro-jitter movements

---

## 🗺️ Roadmap

- [ ] Voice command integration
- [ ] Custom gesture configuration
- [ ] Multi-hand gesture support
- [ ] Gesture recording and playback
- [ ] Electron desktop app
- [ ] Cross-platform optimization
- [ ] Gesture macro system
- [ ] Hand calibration wizard

---

## 📄 License

This project is available under the MIT License. See LICENSE file for details.

---

## 🙏 Acknowledgments

- **MediaPipe**: Google's hand tracking solution
- **OpenCV**: Computer vision framework
- **PyAutoGUI**: Cross-platform GUI automation

---

## 📞 Support

For issues, questions, or feature requests, please open an issue on the GitHub repository.

**Made with ❤️ by the Gestura Team**
