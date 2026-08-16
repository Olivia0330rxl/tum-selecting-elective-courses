#!/usr/bin/env python3
"""Build a self-contained offline weekly planner from normalized JSON."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from planner_core import PlannerValidationError, load_and_prepare


ROOT = Path(__file__).resolve().parents[1]
ASSET_DIR = ROOT / "assets" / "weekly-calendar"


def _safe_script_json(value: object) -> str:
    return (
        json.dumps(value, ensure_ascii=False, separators=(",", ":"))
        .replace("<", "\\u003c")
        .replace(">", "\\u003e")
        .replace("&", "\\u0026")
        .replace("\u2028", "\\u2028")
        .replace("\u2029", "\\u2029")
    )


def build(input_path: Path, output_path: Path) -> None:
    data = load_and_prepare(input_path)
    template = (ASSET_DIR / "template.html").read_text(encoding="utf-8")
    css = (ASSET_DIR / "style.css").read_text(encoding="utf-8")
    javascript = (ASSET_DIR / "app.js").read_text(encoding="utf-8")
    required = ("__PLANNER_STYLE__", "__PLANNER_DATA__", "__PLANNER_SCRIPT__")
    missing = [marker for marker in required if marker not in template]
    if missing:
        raise PlannerValidationError(f"Template is missing markers: {', '.join(missing)}")
    html = (
        template.replace("__PLANNER_STYLE__", css)
        .replace("__PLANNER_DATA__", _safe_script_json(data))
        .replace("__PLANNER_SCRIPT__", javascript)
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="normalized planner JSON")
    parser.add_argument("output", type=Path, help="output HTML path")
    args = parser.parse_args()
    try:
        build(args.input, args.output)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(args.output.resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
