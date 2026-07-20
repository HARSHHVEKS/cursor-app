import time
from pathlib import Path

import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

# Default model lives at <project root>/models/hand_landmarker.task
DEFAULT_MODEL_PATH = Path(__file__).resolve().parents[2] / "models" / "hand_landmarker.task"


class HandTracker:
    def __init__(self, model_path=None, num_hands=1,
                 min_hand_detection_confidence=0.6,
                 min_hand_presence_confidence=0.6,
                 min_tracking_confidence=0.6):
        # Point the detector at the model file we downloaded.
        model_path = str(model_path or DEFAULT_MODEL_PATH)
        base_options = python.BaseOptions(model_asset_path=model_path)
        options = vision.HandLandmarkerOptions(
            base_options=base_options,
            running_mode=vision.RunningMode.VIDEO,   # a stream of frames, not one photo
            num_hands=num_hands,                     # one hand -> less work
            min_hand_detection_confidence=min_hand_detection_confidence,
            min_hand_presence_confidence=min_hand_presence_confidence,
            min_tracking_confidence=min_tracking_confidence,
        )
        self.detector = vision.HandLandmarker.create_from_options(options)

        # VIDEO mode needs an ever-increasing clock (in ms) so it can track the
        # hand across frames. We manage it here so callers don't have to.
        self._t0 = time.time()
        self._last_ms = -1

    def process(self, frame):
        # BGR (OpenCV) -> RGB, then wrap it in MediaPipe's own Image type.
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)

        # A timestamp that always moves forward (the guard prevents duplicates).
        ms = int((time.time() - self._t0) * 1000)
        if ms <= self._last_ms:
            ms = self._last_ms + 1
        self._last_ms = ms

        result = self.detector.detect_for_video(mp_image, ms)

        # No hand this frame? Same "return None" pattern as camera.read().
        if not result.hand_landmarks:
            return None

        # result.hand_landmarks[0] is a LIST of 21 landmarks (each has .x, .y, .z).
        return result.hand_landmarks[0]


if __name__ == "__main__":
    from camera import Camera

    cam = Camera()
    tracker = HandTracker()
    prev = time.time()

    while True:
        frame = cam.read()
        if frame is None:
            break

        frame = cv2.flip(frame, 1)   # mirror so movement feels natural

        hand = tracker.process(frame)
        if hand is not None:
            tip = hand[8]                              # index fingertip (normalized 0..1)
            h, w = frame.shape[:2]                     # frame size in pixels
            x, y = int(tip.x * w), int(tip.y * h)      # normalized -> pixels
            cv2.circle(frame, (x, y), 10, (0, 255, 0), -1)   # green dot on the tip

        now = time.time()
        fps = 1.0 / (now - prev)
        prev = now
        cv2.putText(frame, f"FPS: {fps:.1f}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 2)

        cv2.imshow("HandCursor - hand tracking", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cam.release()
    cv2.destroyAllWindows()
