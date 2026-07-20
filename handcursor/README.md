# HandCursor

Control your mouse cursor with hand and finger movements, using a webcam. Move
your index finger to steer the pointer; pinch thumb + index to click or drag.

Built on **MediaPipe** hand tracking and a kernel-level **evdev/uinput** virtual
mouse, so it works on **Wayland and X11**. Designed to be smooth (One Euro
Filter) and low-CPU, with a clean, modular, testable architecture.

## Requirements

- Linux, Python **3.12** (MediaPipe doesn't support newer yet).
- A webcam.
- One-time `/dev/uinput` write permission (so we can create a virtual mouse).

## Setup

```bash
cd handcursor
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e .          # installs deps + the `handcursor` command (editable)
```

Grant uinput permission once (if you haven't already):

```bash
sudo modprobe uinput
echo 'KERNEL=="uinput", SUBSYSTEM=="misc", OPTIONS+="static_node=uinput", GROUP="input", MODE="0660"' \
  | sudo tee /etc/udev/rules.d/99-uinput.rules
sudo udevadm control --reload-rules && sudo udevadm trigger /dev/uinput
# make sure you're in the `input` group, then re-login:
sudo usermod -aG input "$USER"
```

## Run

```bash
python -m handcursor            # with the debug preview window
python -m handcursor --no-preview   # headless, lower CPU (quit with Ctrl+C)
```

In the preview window: **`q`** quits, **`h`** hides the preview.

> **Set your screen resolution** in `config.yaml` (`screen.width/height`) to your
> real monitor size, or the cursor won't reach the edges. Find it with `xrandr`
> or `wlr-randr`.

## Configuration

All tunables live in [`config.yaml`](config.yaml) — camera, screen size, mapping
margin, smoothing strength, pinch thresholds, tracker confidences, preview on/off.
Anything you omit falls back to the defaults in `src/handcursor/config.py`.

## Architecture

Each module does one job and the pure-logic ones are testable with no hardware:

```
src/handcursor/
├── camera.py     webcam capture only
├── tracker.py    MediaPipe hand landmarks only
├── mapping.py    normalized coords -> screen pixels   (pure, tested)
├── smoothing.py  One Euro Filter                       (pure, tested)
├── gestures.py   pinch state machine (hysteresis)      (pure, tested)
├── mouse.py      evdev/uinput virtual mouse
├── overlay.py    optional debug preview
├── config.py     config loading
├── app.py        orchestrator: wires it all + main loop
└── __main__.py   `python -m handcursor`
```

Loop: **capture → track → map → smooth → move** (+ pinch → click).

## Tests

```bash
pip install -e ".[dev]"
pytest
```

Covers the pure-logic core (smoothing, mapping, gestures).

## Roadmap

Phase 1 (this) is a smooth, low-CPU MVP. Phase 2 aims at a genuinely usable tool:
ML gesture recognition to kill false clicks, Kalman/predictive smoothing, hand-
rotation robustness, adaptive sensitivity, and ergonomics — each slotting into
the module it belongs to. The clean boundaries here are what make that possible.
