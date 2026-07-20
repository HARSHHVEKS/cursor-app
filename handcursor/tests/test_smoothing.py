import random

from handcursor.smoothing import OneEuroFilter, OneEuroFilter2D


def _variance(xs):
    m = sum(xs) / len(xs)
    return sum((x - m) ** 2 for x in xs) / len(xs)


def test_first_sample_passes_through():
    f = OneEuroFilter(freq=30)
    assert f(5.0, t=0.0) == 5.0


def test_constant_input_stays_constant():
    f = OneEuroFilter(freq=30, min_cutoff=1.0, beta=0.0)
    out = None
    for i in range(200):
        out = f(10.0, t=i / 30.0)
    assert abs(out - 10.0) < 1e-9


def test_reduces_noise_variance():
    random.seed(0)
    f = OneEuroFilter(freq=30, min_cutoff=1.0, beta=0.0)
    raw, filtered = [], []
    for i in range(300):
        x = 100.0 + random.uniform(-5, 5)
        raw.append(x)
        filtered.append(f(x, t=i / 30.0))
    # After warmup, the filtered signal must be visibly calmer than the raw one.
    assert _variance(filtered[50:]) < _variance(raw[50:])


def test_reset_clears_state():
    f = OneEuroFilter(freq=30)
    f(1.0, t=0.0)
    f(2.0, t=1 / 30.0)
    f.reset()
    assert f(99.0, t=0.0) == 99.0  # behaves like a fresh filter again


def test_2d_first_sample_passthrough():
    f = OneEuroFilter2D(freq=30)
    assert f(1.0, 2.0, t=0.0) == (1.0, 2.0)
