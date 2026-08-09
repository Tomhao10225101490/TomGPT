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
    parser.add_argument(
        "--password",
        default=None,
        help="Shared access password (or set TOMGPT_PASSWORD / G4F_API_KEY)",
    )
    parser.add_argument(
        "--rate-limit",
        default=None,
        help='Chat rate limit as requests/seconds, e.g. "20/60" (or TOMGPT_RATE_LIMIT)',
    )
    parser.add_argument(
        "--rate-limit-global",
        default=None,
        help='Global rate limit as requests/seconds, e.g. "180/60"',
    )
    parser.add_argument(
        "--trust-proxy",
        action="store_true",
        help="Trust X-Forwarded-For for client IP (only behind a trusted reverse proxy)",
    )
    args = parser.parse_args()

    from g4f.config import AppConfig
    from g4f.gui import run_gui
    from g4f.tomgpt_security import is_loopback_host

    AppConfig.load_from_env()
    AppConfig.set_config(
        access_password=args.password,
        rate_limit=args.rate_limit,
        rate_limit_global=args.rate_limit_global,
        trust_proxy=True if args.trust_proxy else None,
    )

    password = AppConfig.resolved_access_password()
    if password and not AppConfig.g4f_api_key:
        AppConfig.g4f_api_key = password
    if not is_loopback_host(args.host) and not password:
        print(
            "ERROR: Binding to a non-loopback host requires an access password.\n"
            "Set --password, TOMGPT_PASSWORD, or G4F_API_KEY before going public.\n"
            "Example:\n"
            "  TOMGPT_PASSWORD='your-strong-password' "
            f"python start_tomgpt.py --host {args.host} --port {args.port} --trust-proxy",
            file=sys.stderr,
        )
        sys.exit(2)

    run_gui(host=args.host, port=args.port, debug=args.debug)


if __name__ == "__main__":
    main()
