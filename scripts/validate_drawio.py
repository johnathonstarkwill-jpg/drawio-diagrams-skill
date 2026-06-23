#!/usr/bin/env python3
"""Validate basic diagrams.net/draw.io XML structure."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

try:
    from defusedxml import ElementTree as ET
except ImportError:  # pragma: no cover - stdlib fallback for minimal Python installs.
    from xml.etree import ElementTree as ET


def validate(path: Path) -> tuple[int, int]:
    tree = ET.parse(path)
    root = tree.getroot()
    if root.tag != "mxfile":
        raise ValueError("root element must be <mxfile>")
    diagram = root.find("diagram")
    if diagram is None:
        raise ValueError("missing <diagram>")
    model = diagram.find("mxGraphModel")
    if model is None:
        raise ValueError("missing <mxGraphModel>")
    graph_root = model.find("root")
    if graph_root is None:
        raise ValueError("missing mxGraphModel/root")

    cells = graph_root.findall("mxCell")
    ids = [cell.get("id") for cell in cells]
    duplicates = sorted({cell_id for cell_id in ids if cell_id and ids.count(cell_id) > 1})
    if duplicates:
        raise ValueError(f"duplicate mxCell ids: {', '.join(duplicates)}")
    by_id = {cell.get("id"): cell for cell in cells}
    if "0" not in by_id:
        raise ValueError('missing mxCell id="0"')
    if by_id.get("1") is None or by_id["1"].get("parent") != "0":
        raise ValueError('missing mxCell id="1" parent="0"')

    vertices = [cell for cell in cells if cell.get("vertex") == "1"]
    edges = [cell for cell in cells if cell.get("edge") == "1"]
    if not vertices:
        raise ValueError("no vertex cells found")
    known_ids = set(by_id)
    for cell in cells:
        parent = cell.get("parent")
        if parent and parent not in known_ids:
            raise ValueError(f"cell {cell.get('id')} has unknown parent: {parent}")
        value = cell.get("value", "")
        if "\\n" in value:
            raise ValueError(f"cell {cell.get('id')} contains literal \\\\n; use <br> in draw.io XML")
    for cell in vertices:
        geom = cell.find("mxGeometry")
        if geom is None:
            raise ValueError(f"vertex {cell.get('id')} missing mxGeometry")
        if float(geom.get("width", "0")) <= 0 or float(geom.get("height", "0")) <= 0:
            raise ValueError(f"vertex {cell.get('id')} has nonpositive size")
    vertex_or_group_ids = {cell.get("id") for cell in vertices}
    for edge in edges:
        geom = edge.find("mxGeometry")
        if geom is None:
            raise ValueError(f"edge {edge.get('id')} missing mxGeometry")
        if geom.get("relative") != "1":
            raise ValueError(f"edge {edge.get('id')} mxGeometry must have relative=1")
        for key in ("source", "target"):
            if edge.get(key) not in vertex_or_group_ids:
                raise ValueError(f"edge {edge.get('id')} has unknown {key}: {edge.get(key)}")
    return len(vertices), len(edges)


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("drawio", help="Path to .drawio file")
    args = parser.parse_args(argv)
    vertices, edges = validate(Path(args.drawio))
    print(f"OK: {vertices} vertices, {edges} edges")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
