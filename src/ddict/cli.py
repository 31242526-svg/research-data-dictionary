"""CLI: ddict participants.csv -o dictionary.md --json dictionary.json."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from ddict.core import profile_file


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ddict",
        description="Build a data dictionary (Markdown or JSON) from a CSV file.",
    )
    parser.add_argument("source", type=Path, help="input CSV")
    parser.add_argument("-o", "--output", type=Path, default=None, help="Markdown output file")
    parser.add_argument("--json", type=Path, default=None, help="JSON output file")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if not args.source.exists():
        print(f"error: no such file: {args.source}", file=sys.stderr)
        return 2

    profile = profile_file(args.source)
    markdown = profile.to_markdown()

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(markdown, encoding="utf-8")
        print(f"{args.output} written: {profile.rows} rows, {profile.columns} columns")
    else:
        print(markdown, end="")

    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(profile.to_json() + "\n", encoding="utf-8")
        print(f"{args.json} written")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
