"""The evdev/uinput virtual mouse — the only module that touches the real cursor.

On Wayland, userspace tools like pyautogui can't move the pointer. So we go one
level deeper and create a *virtual input device* in the kernel via /dev/uinput.
The compositor sees an ordinary mouse and moves the real cursor for us. Works on
Wayland AND X11. (This needs the one-time /dev/uinput permission from setup.)

We emit **relative** motion (EV_REL) because compositors treat a relative device
as a plain mouse with rock-solid support. To still get absolute, finger-follows
positioning, we remember where we last placed the cursor and emit the delta to
the next target. (Note: if you also grab the physical mouse, the two notions of
position can drift — fine for the MVP.)
"""

import time

from evdev import UInput, ecodes as e


def _clamp(v, lo, hi):
    return lo if v < lo else hi if v > hi else v


class VirtualMouse:
    def __init__(self, screen_width, screen_height):
        capabilities = {
            e.EV_KEY: [e.BTN_LEFT, e.BTN_RIGHT],
            e.EV_REL: [e.REL_X, e.REL_Y],
        }
        self.ui = UInput(capabilities, name="handcursor-virtual-mouse")
        # Give the compositor a moment to notice the new device, otherwise the
        # first few events can be dropped while it wires things up.
        time.sleep(0.3)

        self.sw = int(screen_width)
        self.sh = int(screen_height)
        # Our belief about where the cursor is; start at screen center.
        self.x = self.sw / 2.0
        self.y = self.sh / 2.0
        self._pressed = False

    def move_to(self, tx, ty):
        """Move the cursor toward an absolute screen pixel via a relative delta."""
        tx = _clamp(tx, 0, self.sw - 1)
        ty = _clamp(ty, 0, self.sh - 1)
        dx = int(round(tx - self.x))
        dy = int(round(ty - self.y))
        if dx or dy:
            self.ui.write(e.EV_REL, e.REL_X, dx)
            self.ui.write(e.EV_REL, e.REL_Y, dy)
            self.ui.syn()
            self.x += dx
            self.y += dy

    def press(self):
        if not self._pressed:
            self.ui.write(e.EV_KEY, e.BTN_LEFT, 1)
            self.ui.syn()
            self._pressed = True

    def release(self):
        if self._pressed:
            self.ui.write(e.EV_KEY, e.BTN_LEFT, 0)
            self.ui.syn()
            self._pressed = False

    def click(self):
        self.press()
        self.release()

    def close(self):
        self.release()
        self.ui.close()
