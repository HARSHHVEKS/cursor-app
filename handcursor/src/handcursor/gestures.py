"""Pinch detection: thumb + index tip coming together = a click / hold.

Two classic problems make naive pinch detection flicker:

1. **Scale** — the same pinch looks bigger when your hand is near the camera.
   Fix: divide the thumb-index distance by a hand-size reference (wrist -> index
   knuckle), giving a scale-invariant *ratio*.

2. **Chatter near the threshold** — a single threshold flickers press/release when
   the ratio hovers around it. Fix: **hysteresis** (a lower press threshold and a
   higher release threshold) plus **debounce** (a state must persist N frames
   before it counts). Together: no accidental clicks, no jitter.

Because pinch = "button held", a quick pinch-and-release is naturally a *click*,
and a sustained pinch while moving is a *drag* — one mechanism, both gestures.

Pure logic, no hardware — unit-tested in tests/test_gestures.py.
"""

import math
from enum import Enum


class PinchEvent(Enum):
    NONE = 0
    PRESS = 1
    RELEASE = 2


def _dist(a, b):
    return math.hypot(a.x - b.x, a.y - b.y)


class PinchDetector:
    # MediaPipe hand landmark indices.
    THUMB_TIP = 4
    INDEX_TIP = 8
    WRIST = 0
    INDEX_MCP = 5  # base knuckle of the index finger

    def __init__(self, press_ratio=0.35, release_ratio=0.55, debounce_frames=2):
        if press_ratio >= release_ratio:
            raise ValueError("press_ratio must be < release_ratio (hysteresis)")
        self.press_ratio = float(press_ratio)
        self.release_ratio = float(release_ratio)
        self.debounce_frames = max(1, int(debounce_frames))

        self.pinched = False
        self._candidate = None   # the state we're debouncing toward
        self._count = 0

    def ratio(self, landmarks):
        """Scale-invariant pinch tightness. Smaller = fingers closer together."""
        d_pinch = _dist(landmarks[self.THUMB_TIP], landmarks[self.INDEX_TIP])
        d_scale = _dist(landmarks[self.WRIST], landmarks[self.INDEX_MCP])
        if d_scale <= 1e-6:
            return float("inf")
        return d_pinch / d_scale

    def update(self, landmarks):
        """Feed one frame's landmarks; get back a PinchEvent."""
        r = self.ratio(landmarks)

        # Hysteresis: which state does this ratio *want*?
        if not self.pinched:
            target = r < self.press_ratio
        else:
            target = not (r > self.release_ratio)

        # No change requested -> clear any pending debounce.
        if target == self.pinched:
            self._candidate = None
            self._count = 0
            return PinchEvent.NONE

        # Debounce: the new state must hold for debounce_frames in a row.
        if self._candidate == target:
            self._count += 1
        else:
            self._candidate = target
            self._count = 1

        if self._count >= self.debounce_frames:
            self.pinched = target
            self._candidate = None
            self._count = 0
            return PinchEvent.PRESS if target else PinchEvent.RELEASE

        return PinchEvent.NONE

    def reset(self):
        self.pinched = False
        self._candidate = None
        self._count = 0
