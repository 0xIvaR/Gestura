
# HandGestureApp

Touchless cursor control using hand gestures with OpenCV and MediaPipe. Includes a polished Tkinter GUI with multiple modes (General, Medical, Education), adjustable sensitivity and click thresholds, and optional voice feedback.

## Features
- Smooth, low-latency cursor control by tracking the index finger
- Click and double-click via pinch gestures (thumb + index)
- Click-and-drag via pinch-and-hold for text selection
- Three modes:
  - General: default gestures for everyday use
  - Medical: voice confirmations and safer defaults
  - Education: presentation-friendly behavior (slide navigation placeholders)
- Adjustable sensitivity and click threshold
- Persistent settings saved in `config.json`

## Demo (Gestures)
- Move index finger: move cursor
- Pinch (thumb + index close): single click
- Quick double pinch: double click
- Partial pinch and hold: drag/select
- Press `ESC`: exit

## Requirements
- Python 3.8+
- A working webcam
- Windows/macOS/Linux (tested on Windows)

Python dependencies (see `requirements.txt`):
- opencv-python
- mediapipe
- pyautogui
- pyttsx3 (for Medical mode voice)
- SpeechRecognition (planned)
- pytest (tests)
- pyinstaller (optional packaging)

## Installation
1. Clone or download this repository.
2. (Recommended) Create and activate a virtual environment.
   - Windows (PowerShell):
     ```powershell
     python -m venv .venv
     .venv\Scripts\Activate.ps1
     ```
   - macOS/Linux:
     ```bash
     python3 -m venv .venv
     source .venv/bin/activate
     ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage
- GUI (recommended):
  ```bash
  python -m src.main
  ```
  or
  ```bash
  python src/main.py
  ```

- In the GUI:
  - Choose a mode: General, Medical, or Education
  - Adjust Gesture Sensitivity and Click Threshold
  - Toggle Voice Feedback (Medical mode)
  - Click "Start Gesture Control" to begin

Settings are saved to `config.json` in your current working directory (project root if you run from the repo root).

## Configuration
`src/gui.py` reads and writes `config.json` with keys:
- `sensitivity` (float 0.1–1.0)
- `click_threshold` (int, pixels; e.g., 20–40)
- `voice_enabled` (bool)
- `mode` ("general" | "medical" | "education")

`src/controller.py` applies these values to control smoothing and gesture thresholds.

## Building an executable (optional)
You can package the app using PyInstaller:
```bash
pyinstaller --noconfirm --onefile --windowed --name HandGestureApp src/main.py
```
Note: You may need to include MediaPipe/OpenCV data files depending on platform.

## Troubleshooting
- No camera feed / "Failed to read from camera":
  - Ensure your webcam is not used by another app
  - Try a different camera index in `cv2.VideoCapture(0)` (e.g., 1)
- Cursor jumps or is jittery:
  - Increase `sensitivity` (closer to 1.0 is smoother but slower to react)
- Clicks not detected:
  - Lower `click_threshold` or ensure good lighting and clear hand visibility
- Voice not working in Medical mode:
  - Ensure `pyttsx3` is installed; some platforms need extra TTS engines
- App freezes on start:
  - The controller runs in a background thread; ensure Python and packages are up to date

## Project Structure
```
HandGestureApp/
├─ src/
│  ├─ main.py            # Entry point; launches GUI
│  ├─ gui.py             # Tkinter GUI and settings management
│  ├─ controller.py      # OpenCV/MediaPipe logic and gesture handling
│  ├─ __init__.py
│  └─ config.json        # Saved settings (auto-created/updated when running from src/)
├─ requirements.txt
├─ README.md
└─ .gitignore
```

## Development
- Run tests (if any are added under `tests/`):
  ```bash
  pytest -q
  ```
- Code style: prefer readable names and early returns; avoid deep nesting

## License
Choose a license (e.g., MIT) and add a `LICENSE` file if you plan to share publicly.
