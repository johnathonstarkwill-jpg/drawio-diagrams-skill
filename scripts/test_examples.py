#!/usr/bin/env python3
"""Generate and validate all bundled examples."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

try:
    from defusedxml import ElementTree as ET
except ImportError:  # pragma: no cover - stdlib fallback for trusted local outputs.
    from xml.etree import ElementTree as ET


SKILL_DIR = Path(__file__).resolve().parents[1]
EXAMPLES_DIR = SKILL_DIR / "examples"
GENERATE = SKILL_DIR / "scripts" / "generate_drawio.py"
VALIDATE = SKILL_DIR / "scripts" / "validate_drawio.py"


def run(args: list[str]) -> None:
    subprocess.run(args, check=True)


def assert_no_literal_newline(path: Path) -> None:
    root = ET.parse(path).getroot()
    for cell in root.findall(".//mxCell"):
        value = cell.get("value", "")
        if "\\n" in value:
            raise AssertionError(f"{path.name}: cell {cell.get('id')} contains literal \\\\n")


def main() -> int:
    examples = sorted(EXAMPLES_DIR.glob("*.json"))
    if not examples:
        raise SystemExit("no examples found")
    with tempfile.TemporaryDirectory() as tmp:
        out_dir = Path(tmp)
        for example in examples:
            name = example.stem
            out = out_dir / f"{name}.drawio"
            run([sys.executable, str(GENERATE), str(example), str(out)])
            run([sys.executable, str(VALIDATE), str(out)])
            assert_no_literal_newline(out)

            printed = subprocess.check_output([sys.executable, str(GENERATE), "--example", name], text=True)
            json.loads(printed)
            print(f"{name}: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
