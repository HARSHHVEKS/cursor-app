"""The orchestrator: wires the modules together and runs the main loop.

Each frame:  capture -> track -> map -> smooth -> move  (+ pinch -> click).
Every step lives in its own module; this file just connects them and owns the
loop, the preview, and clean shutdown. That separation is the whole point — it's
what the old tangled single-loop version lacked.
"""

import time

import cv2

from . import overlay
from .camera import Camera
from .config import DEFAULT_MODEL_PATH, load_config
from .gestures import PinchDetector, PinchEvent
from .mapping import CoordinateMapper
from .mouse import VirtualMouse
from .smoothing import OneEuroFilter2D
from .tracker import HandTracker

_WINDOW = "HandCursor"


class HandCursorApp:
    def __init__(self, config=None, model_path=None):
        cfg = config or load_config()
        self.cfg = cfg

        cam = cfg["camera"]
        self.cam = Camera(index=cam["index"], width=cam["width"], height=cam["height"])

        tk = cfg["tracker"]
        self.tracker = HandTracker(
            model_path=str(model_path or DEFAULT_MODEL_PATH),
            num_hands=tk["num_hands"],
            min_hand_detection_confidence=tk["min_detection_confidence"],
            min_hand_presence_confidence=tk["min_presence_confidence"],
            min_tracking_confidence=tk["min_tracking_confidence"],
        )

        scr = cfg["screen"]
        self.mouse = VirtualMouse(scr["width"], scr["height"])
        self.mapper = CoordinateMapper(scr["width"], scr["height"], cfg["mapping"]["margin"])

        sm = cfg["smoothing"]
        self.smoother = OneEuroFilter2D(
            freq=30.0, min_cutoff=sm["min_cutoff"], beta=sm["beta"], d_cutoff=sm["d_cutoff"]
        )

        pn = cfg["pinch"]
        self.pinch = PinchDetector(pn["press_ratio"], pn["release_ratio"], pn["debounce_frames"])

        self.show_preview = bool(cfg["preview"])

    def run(self):
        prev = time.time()
        fps = 0.0
        try:
            while True:
                frame = self.cam.read()
                if frame is None:
                    break
                frame = cv2.flip(frame, 1)  # mirror so motion feels natural

                hand = self.tracker.process(frame)
                now = time.time()

                if hand is not None:
                    tip = hand[8]  # index fingertip drives the cursor
                    sx, sy = self.mapper.map(tip.x, tip.y)
                    sx, sy = self.smoother(sx, sy, now)
                    self.mouse.move_to(sx, sy)

                    event = self.pinch.update(hand)
                    if event == PinchEvent.PRESS:
                        self.mouse.press()
                    elif event == PinchEvent.RELEASE:
                        self.mouse.release()
                else:
                    # Hand lost: never leave a button stuck, and forget stale
                    # smoothing state so re-acquiring doesn't lurch.
                    self.mouse.release()
                    self.pinch.reset()
                    self.smoother.reset()

                dt = now - prev
                prev = now
                if dt > 0:
                    inst = 1.0 / dt
                    fps = 0.9 * fps + 0.1 * inst if fps else inst

                if self.show_preview:
                    overlay.draw(frame, hand,
                                 f"FPS: {fps:4.1f}   [q] quit   [h] hide preview",
                                 self.pinch.pinched)
                    cv2.imshow(_WINDOW, frame)
                    key = cv2.waitKey(1) & 0xFF
                    if key == ord("q"):
                        break
                    if key == ord("h"):
                        self.show_preview = False
                        cv2.destroyWindow(_WINDOW)
        except KeyboardInterrupt:
            pass
        finally:
            self.close()

    def close(self):
        self.cam.release()
        self.mouse.close()
        cv2.destroyAllWindows()
