"""Entry point so the whole app runs with:  python -m handcursor"""

import argparse

from .app import HandCursorApp
from .config import load_config


def main():
    parser = argparse.ArgumentParser(
        prog="handcursor",
        description="Control the mouse cursor with hand/finger movements.",
    )
    parser.add_argument("-c", "--config", default=None,
                        help="Path to a config.yaml (defaults to the project's).")
    parser.add_argument("--no-preview", action="store_true",
                        help="Run headless (no window, lower CPU). Quit with Ctrl+C.")
    args = parser.parse_args()

    cfg = load_config(args.config)
    if args.no_preview:
        cfg["preview"] = False

    print("HandCursor: move your index finger to steer the cursor; pinch "
          "thumb+index to click/drag.")
    print("Quit with 'q' in the preview window (or Ctrl+C if headless).")

    HandCursorApp(config=cfg).run()


if __name__ == "__main__":
    main()
