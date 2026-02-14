"""
Main application entrypoint.

Routes commands to index/search/gui flows and supports optional config override.
"""

import argparse
import sys

import cli
import gui
import process
from utils.config import set_config_file


def build_parser() -> argparse.ArgumentParser:
    """Create CLI parser for the unified entrypoint."""
    parser = argparse.ArgumentParser(
        description="POCR2 unified entrypoint for indexing, searching, and GUI."
    )
    parser.add_argument(
        "command",
        nargs="?",
        choices=("index", "search"),
        help="Run in command mode: 'index' (OCR processing) or 'search' (query mode).",
    )
    parser.add_argument(
        "--gui",
        action="store_true",
        help="Launch the graphical interface.",
    )
    parser.add_argument(
        "--config",
        type=str,
        help="Optional path to a custom config.toml file.",
    )
    return parser


def main() -> int:
    """Parse arguments and dispatch to selected application mode."""
    parser = build_parser()
    args = parser.parse_args()

    if args.gui and args.command:
        parser.error("--gui cannot be used together with a command.")

    if not args.gui and not args.command:
        parser.print_help()
        return 2

    if args.config:
        set_config_file(args.config)

    if args.gui:
        gui.main()
        return 0

    if args.command == "index":
        process.main(config_path=args.config)
        return 0

    cli.main()
    return 0


if __name__ == "__main__":
    sys.exit(main())
