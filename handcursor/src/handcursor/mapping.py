"""Turn a normalized hand position into a screen pixel.

MediaPipe gives coordinates in 0..1 across the *camera frame*. If we mapped
those straight to the screen, you'd have to stretch your arm to the very edge of
the camera's view to reach the screen corners, and the tiniest hand tremor at
the edges would fling the cursor off-screen.

The fix is an **active region**: we trim a margin off every side of the frame and
map only the comfortable middle box to the full screen. Small hand movements in
a relaxed area cover the whole display. Anything past the box clamps to the edge.

Pure math, no hardware — unit-tested in tests/test_mapping.py.
"""


def _clamp(v, lo, hi):
    return lo if v < lo else hi if v > hi else v


class CoordinateMapper:
    def __init__(self, screen_width, screen_height, margin=0.15):
        if not (0.0 <= margin < 0.5):
            raise ValueError("margin must be in [0.0, 0.5)")
        self.sw = int(screen_width)
        self.sh = int(screen_height)
        self.margin = float(margin)

    def map(self, nx, ny):
        """(nx, ny) normalized 0..1 -> (x, y) in screen pixels."""
        span = 1.0 - 2.0 * self.margin
        rx = _clamp((nx - self.margin) / span, 0.0, 1.0)
        ry = _clamp((ny - self.margin) / span, 0.0, 1.0)
        return rx * (self.sw - 1), ry * (self.sh - 1)
