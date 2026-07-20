"""Buttery smoothing for the cursor path.

The star here is the **One Euro Filter** (Casiez et al., 2012). Plain smoothing
forces a bad trade-off: smooth enough to kill jitter = laggy on fast moves.
One Euro adapts: when the hand is still it filters HARD (no jitter), when the
hand moves fast it filters LIGHTLY (no lag). That adaptivity is what makes the
cursor feel like a real mouse instead of a floaty balloon.

Pure math, zero hardware — fully unit-testable (see tests/test_smoothing.py).
"""

import math


class _LowPass:
    """Exponential moving average with an alpha supplied per-sample."""

    def __init__(self):
        self._prev = None

    def __call__(self, value, alpha):
        if self._prev is None:
            self._prev = value
        else:
            self._prev = alpha * value + (1.0 - alpha) * self._prev
        return self._prev

    @property
    def last(self):
        return self._prev


def _alpha(cutoff, freq):
    """Smoothing factor for a given cutoff frequency and sampling rate."""
    tau = 1.0 / (2.0 * math.pi * cutoff)
    te = 1.0 / freq
    return 1.0 / (1.0 + tau / te)


class OneEuroFilter:
    """Adaptive low-pass filter for a single scalar stream.

    Params:
        freq:       expected sample rate (Hz). Auto-updated from timestamps.
        min_cutoff: baseline smoothing. Lower = smoother but laggier.
        beta:       speed coefficient. Higher = snappier on fast motion.
        d_cutoff:   cutoff for the internal speed estimate (rarely tuned).
    """

    def __init__(self, freq=30.0, min_cutoff=1.0, beta=0.0, d_cutoff=1.0):
        if freq <= 0:
            raise ValueError("freq must be > 0")
        self.freq = float(freq)
        self.min_cutoff = float(min_cutoff)
        self.beta = float(beta)
        self.d_cutoff = float(d_cutoff)

        self._freq0 = float(freq)
        self._x = _LowPass()
        self._dx = _LowPass()
        self._x_prev = None
        self._t_prev = None

    def __call__(self, x, t=None):
        # Update the sample rate from real timestamps when we can.
        if self._x_prev is not None and t is not None and self._t_prev is not None:
            dt = t - self._t_prev
            if dt > 0:
                self.freq = 1.0 / dt

        # Estimate speed (derivative) and smooth it.
        dx = 0.0 if self._x_prev is None else (x - self._x_prev) * self.freq
        edx = self._dx(dx, _alpha(self.d_cutoff, self.freq))

        # The adaptive part: faster motion -> higher cutoff -> less smoothing.
        cutoff = self.min_cutoff + self.beta * abs(edx)
        x_hat = self._x(x, _alpha(cutoff, self.freq))

        self._x_prev = x
        self._t_prev = t
        return x_hat

    def reset(self):
        self.freq = self._freq0
        self._x = _LowPass()
        self._dx = _LowPass()
        self._x_prev = None
        self._t_prev = None


class OneEuroFilter2D:
    """Two independent One Euro filters for an (x, y) point."""

    def __init__(self, freq=30.0, min_cutoff=1.0, beta=0.0, d_cutoff=1.0):
        self.fx = OneEuroFilter(freq, min_cutoff, beta, d_cutoff)
        self.fy = OneEuroFilter(freq, min_cutoff, beta, d_cutoff)

    def __call__(self, x, y, t=None):
        return self.fx(x, t), self.fy(y, t)

    def reset(self):
        self.fx.reset()
        self.fy.reset()
