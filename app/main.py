"""CLI entry point."""

from __future__ import annotations

import sys


def main() -> int:
    try:
        from app.ui.app import run
    except ImportError as exc:
        print(
            "Failed to import the GUI. Did you `pip install -e .` first?\n",
            f"Error: {exc}",
            file=sys.stderr,
        )
        return 1
    run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
