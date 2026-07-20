"""Configuration loading. All tunables live in config.yaml; this merges them
over sensible defaults so a missing file (or a partial one) still works.
"""

import copy
from pathlib import Path

try:
    import yaml
except ImportError:  # pyyaml not installed -> defaults only
    yaml = None

# <project root>/  (this file is at <root>/src/handcursor/config.py)
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "config.yaml"
DEFAULT_MODEL_PATH = PROJECT_ROOT / "models" / "hand_landmarker.task"

DEFAULTS = {
    "camera": {"index": 0, "width": 640, "height": 480},
    "screen": {"width": 1920, "height": 1080},
    "mapping": {"margin": 0.15},
    "smoothing": {"min_cutoff": 1.5, "beta": 0.02, "d_cutoff": 1.0},
    "pinch": {"press_ratio": 0.35, "release_ratio": 0.55, "debounce_frames": 2},
    "tracker": {
        "num_hands": 1,
        "min_detection_confidence": 0.6,
        "min_presence_confidence": 0.6,
        "min_tracking_confidence": 0.6,
    },
    "preview": True,
}


def _deep_merge(base, override):
    out = copy.deepcopy(base)
    for k, v in (override or {}).items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _deep_merge(out[k], v)
        else:
            out[k] = v
    return out


def load_config(path=None):
    """Return the merged config dict (defaults <- config.yaml <- given path)."""
    path = Path(path) if path else DEFAULT_CONFIG_PATH
    user = {}
    if path.exists() and yaml is not None:
        with open(path) as f:
            user = yaml.safe_load(f) or {}
    return _deep_merge(DEFAULTS, user)
