import pytest

from handcursor.mapping import CoordinateMapper


def test_center_maps_to_center():
    m = CoordinateMapper(1920, 1080, margin=0.0)
    assert m.map(0.5, 0.5) == (0.5 * 1919, 0.5 * 1079)


def test_active_region_edges_map_to_screen_edges():
    m = CoordinateMapper(1000, 1000, margin=0.2)
    assert m.map(0.2, 0.2) == (0.0, 0.0)
    assert m.map(0.8, 0.8) == (999.0, 999.0)


def test_outside_active_region_clamps():
    m = CoordinateMapper(1000, 1000, margin=0.2)
    assert m.map(-1.0, -1.0) == (0.0, 0.0)
    assert m.map(2.0, 2.0) == (999.0, 999.0)


def test_zero_margin_is_plain_scaling():
    m = CoordinateMapper(800, 600, margin=0.0)
    assert m.map(0.25, 0.75) == (0.25 * 799, 0.75 * 599)


def test_bad_margin_rejected():
    with pytest.raises(ValueError):
        CoordinateMapper(100, 100, margin=0.6)
