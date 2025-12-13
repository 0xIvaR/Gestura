from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from threading import Thread, Lock
from typing import Optional

# Local controller
import controller as ctrl
from controller import HandCursorController

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class Settings(BaseModel):
    mode: str                  # "Study" | "General"
    smoothness: int            # 0..100 maps to smoothing factor
    sensitivity: int           # 0..100 maps to click threshold
    liveCameraPreview: bool


state = {
    "mode": "General",
    "smoothness": 50,
    "sensitivity": 30,
    "liveCameraPreview": False,
}

lock = Lock()
worker: Optional[Thread] = None
controller: Optional[HandCursorController] = None
running = False


def map_mode(ui_mode: str) -> str:
    return "education" if ui_mode.lower() == "study" else "general"


def map_smoothness(v: int) -> float:
    v = max(0, min(100, v))
    return round(0.1 + (v / 100) * 0.85, 2)  # ~0.10 .. 0.95


def map_click_threshold(v: int) -> int:
    v = max(0, min(100, v))
    return int(15 + (v / 100) * 35)  # 15 .. 50


def _run():
    assert controller is not None
    controller.run()


@app.post("/update-settings")
def update_settings(s: Settings):
    with lock:
        state.update(s.model_dump())
        ctrl.SMOOTHING_FACTOR = map_smoothness(state["smoothness"])
        ctrl.CLICK_THRESHOLD = map_click_threshold(state["sensitivity"])
        if controller:
            controller.mode = map_mode(state["mode"])
            controller.sensitivity = ctrl.SMOOTHING_FACTOR
    return {"ok": True}


@app.post("/start-gesture-control")
def start_gesture_control():
    global controller, worker, running
    with lock:
        if running:
            return {"ok": True}
        smooth = map_smoothness(state["smoothness"])
        click_th = map_click_threshold(state["sensitivity"])
        ctrl.SMOOTHING_FACTOR = smooth
        ctrl.CLICK_THRESHOLD = click_th
        controller = HandCursorController(
            mode=map_mode(state["mode"]),
            sensitivity=smooth,
            click_threshold=click_th,
            voice_enabled=False,
        )
        worker = Thread(target=_run, daemon=True)
        worker.start()
        running = True
    return {"ok": True}


@app.post("/stop-gesture-control")
def stop_gesture_control():
    global controller, worker, running
    with lock:
        if not running:
            return {"ok": True}
        if controller:
            try:
                controller.cleanup()
            except Exception:
                pass
        running = False
    if worker:
        worker.join(timeout=1.0)
    with lock:
        controller = None
        worker = None
    return {"ok": True}


@app.get("/status")
def status():
    with lock:
        cam = bool(controller and getattr(controller, "cap", None) and controller.cap.isOpened())
    return {"cameraConnected": cam}


@app.on_event("shutdown")
def _shutdown():
    try:
        stop_gesture_control()
    except Exception:
        pass


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="127.0.0.1", port=8000, reload=False)


