"""Optional debug preview window. Purely cosmetic — the app runs fine without it.

Kept separate so the hot path (capture -> track -> move) never depends on drawing.
Turn it off (config `preview: false`, or press 'h') for lower CPU.
"""

import cv2

# A minimal hand skeleton so the overlay reads as a hand, not a dot cloud.
_CONNECTIONS = [
    (0, 1), (1, 2), (2, 3), (3, 4),        # thumb
    (0, 5), (5, 6), (6, 7), (7, 8),        # index
    (5, 9), (9, 10), (10, 11), (11, 12),   # middle
    (9, 13), (13, 14), (14, 15), (15, 16),  # ring
    (13, 17), (17, 18), (18, 19), (19, 20),  # pinky
    (0, 17),                                # palm base
]


def draw(frame, landmarks=None, info=None, pinched=False):
    h, w = frame.shape[:2]

    if landmarks is not None:
        for a, b in _CONNECTIONS:
            pa = (int(landmarks[a].x * w), int(landmarks[a].y * h))
            pb = (int(landmarks[b].x * w), int(landmarks[b].y * h))
            cv2.line(frame, pa, pb, (180, 180, 180), 1)

        # Highlight the driving fingertip (index, #8). Red while pinched.
        tip = landmarks[8]
        color = (0, 0, 255) if pinched else (0, 255, 0)
        cv2.circle(frame, (int(tip.x * w), int(tip.y * h)), 10, color, -1)

    if info:
        cv2.putText(frame, info, (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

    return frame
