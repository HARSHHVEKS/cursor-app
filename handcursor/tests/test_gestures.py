import pytest

from handcursor.gestures import PinchDetector, PinchEvent


class Pt:
    def __init__(self, x, y):
        self.x = x
        self.y = y


def make_landmarks(pinch_dist, scale=0.2):
    """21 landmarks with the 4 the detector uses set to give a known ratio.

    ratio = distance(thumb#4, index#8) / distance(wrist#0, index_mcp#5)
          = pinch_dist / scale
    """
    lm = [Pt(0.0, 0.0) for _ in range(21)]
    lm[0] = Pt(0.0, 0.0)                       # wrist
    lm[5] = Pt(scale, 0.0)                     # index knuckle -> scale
    lm[4] = Pt(0.5, 0.5)                       # thumb tip
    lm[8] = Pt(0.5 + pinch_dist, 0.5)          # index tip -> pinch_dist away
    return lm


def test_ratio_is_scale_invariant():
    d = PinchDetector()
    # Same gesture, hand twice as close to the camera: ratio must match.
    r1 = d.ratio(make_landmarks(0.02, scale=0.2))
    r2 = d.ratio(make_landmarks(0.04, scale=0.4))
    assert abs(r1 - r2) < 1e-9


def test_press_fires_after_debounce():
    d = PinchDetector(press_ratio=0.35, release_ratio=0.55, debounce_frames=2)
    tight = make_landmarks(0.03, 0.2)  # ratio 0.15 < press
    assert d.update(tight) == PinchEvent.NONE    # frame 1: debouncing
    assert d.update(tight) == PinchEvent.PRESS   # frame 2: fires
    assert d.update(tight) == PinchEvent.NONE    # already pressed
    assert d.pinched is True


def test_release_fires_after_debounce():
    d = PinchDetector(press_ratio=0.35, release_ratio=0.55, debounce_frames=2)
    tight = make_landmarks(0.03, 0.2)
    loose = make_landmarks(0.20, 0.2)  # ratio 1.0 > release
    d.update(tight)
    d.update(tight)  # now pressed
    assert d.pinched is True
    assert d.update(loose) == PinchEvent.NONE
    assert d.update(loose) == PinchEvent.RELEASE
    assert d.pinched is False


def test_hysteresis_ignores_mid_zone():
    d = PinchDetector(press_ratio=0.35, release_ratio=0.55, debounce_frames=1)
    mid = make_landmarks(0.09, 0.2)  # ratio 0.45, between the thresholds
    assert d.update(mid) == PinchEvent.NONE
    assert d.pinched is False


def test_debounce_rejects_single_frame_glitch():
    d = PinchDetector(press_ratio=0.35, release_ratio=0.55, debounce_frames=3)
    tight = make_landmarks(0.03, 0.2)
    loose = make_landmarks(0.20, 0.2)
    assert d.update(tight) == PinchEvent.NONE  # 1
    assert d.update(tight) == PinchEvent.NONE  # 2
    assert d.update(loose) == PinchEvent.NONE  # glitch resets the counter
    assert d.pinched is False


def test_press_ratio_must_be_below_release():
    with pytest.raises(ValueError):
        PinchDetector(press_ratio=0.6, release_ratio=0.5)
