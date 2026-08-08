#!/usr/bin/env python3
"""Start the TomGPT web UI (gpt4free GUI, branded)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main() -> None:
    parser = argparse.ArgumentParser(description="Start TomGPT web UI")
    parser.add_argument("--host", default="127.0.0.1", help="Bind host")
    parser.add_argument("--port", type=int, default=8080, help="Bind port")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    args = parser.parse_args()

    from g4f.gui import run_gui

    run_gui(host=args.host, port=args.port, debug=args.debug)


if __name__ == "__main__":
    main()
