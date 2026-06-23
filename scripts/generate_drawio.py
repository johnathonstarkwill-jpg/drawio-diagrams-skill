#!/usr/bin/env python3
"""Generate an editable diagrams.net/draw.io file from a JSON spec."""

from __future__ import annotations

import argparse
import json
import math
import sys
import uuid
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET


SKILL_DIR = Path(__file__).resolve().parents[1]
EXAMPLES_DIR = SKILL_DIR / "examples"

STYLE_MAP = {
    "terminator": "rounded=1;whiteSpace=wrap;html=1;arcSize=50;fillColor=#eef2ff;strokeColor=#818cf8;fontColor=#0f172a;",
    "process": "rounded=1;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#94a3b8;fontColor=#0f172a;",
    "decision": "rhombus;whiteSpace=wrap;html=1;fillColor=#fff7ed;strokeColor=#fb923c;fontColor=#0f172a;",
    "note": "rounded=1;whiteSpace=wrap;html=1;fillColor=#f8fafc;strokeColor=#cbd5e1;fontColor=#475569;",
    "group": "rounded=1;whiteSpace=wrap;html=1;container=1;recursiveResize=0;collapsible=0;fillColor=#f8fafc;strokeColor=#cbd5e1;fontStyle=1;",
    "instrument": "ellipse;whiteSpace=wrap;html=1;aspect=fixed;fillColor=#ecfdf5;strokeColor=#0f766e;fontColor=#0f766e;fontStyle=1;",
    "pump": "ellipse;whiteSpace=wrap;html=1;aspect=fixed;fillColor=#fff7ed;strokeColor=#ea580c;fontColor=#9a3412;fontStyle=1;",
    "valve": "shape=process;whiteSpace=wrap;html=1;fillColor=#eff6ff;strokeColor=#2563eb;fontColor=#1d4ed8;fontStyle=1;",
    "database": "shape=cylinder3d;whiteSpace=wrap;html=1;boundedLbl=1;backgroundOutline=1;size=15;fillColor=#f0f9ff;strokeColor=#0284c7;fontColor=#0f172a;",
    "cloud": "ellipse;shape=cloud;whiteSpace=wrap;html=1;fillColor=#f0f9ff;strokeColor=#38bdf8;fontColor=#0f172a;",
    "document": "shape=document;whiteSpace=wrap;html=1;boundedLbl=1;fillColor=#ffffff;strokeColor=#64748b;fontColor=#0f172a;",
    "store": "shape=datastore;whiteSpace=wrap;html=1;fillColor=#f8fafc;strokeColor=#64748b;fontColor=#0f172a;",
    "offpage": "shape=offPageConnector;whiteSpace=wrap;html=1;fillColor=#fefce8;strokeColor=#ca8a04;fontColor=#713f12;",
}

EDGE_STYLE_MAP = {
    "process": "edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;endArrow=block;strokeColor=#334155;strokeWidth=2;",
    "signal": "edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;endArrow=block;strokeColor=#0f766e;strokeWidth=2;dashed=1;dashPattern=8 8;",
    "line": "edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;endArrow=none;strokeColor=#334155;strokeWidth=2;",
}


def finite_number(value: Any, field: str, item_id: str) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{item_id} {field} must be numeric") from exc
    if not math.isfinite(number):
        raise ValueError(f"{item_id} {field} must be finite")
    return number


def add_geometry(cell: ET.Element, attrs: dict[str, Any], edge: bool = False, offset: tuple[float, float] = (0, 0)) -> None:
    geometry_attrs = {"as": "geometry"}
    if edge:
        geometry_attrs["relative"] = "1"
        geometry = ET.SubElement(cell, "mxGeometry", geometry_attrs)
        points = attrs.get("points") or []
        if points:
            array = ET.SubElement(geometry, "Array", {"as": "points"})
            for point in points:
                ET.SubElement(array, "mxPoint", {"x": str(point["x"]), "y": str(point["y"])})
        for key, as_name in (("sourcePoint", "sourcePoint"), ("targetPoint", "targetPoint")):
            point = attrs.get(key)
            if point:
                ET.SubElement(geometry, "mxPoint", {"as": as_name, "x": str(point["x"]), "y": str(point["y"])})
        return
    else:
        for key in ("x", "y", "width", "height"):
            value = attrs.get(key)
            if value is None:
                raise ValueError(f"vertex {attrs.get('id')!r} missing {key}")
            value = finite_number(value, key, attrs.get("id", "vertex"))
            if key == "x":
                value = value - offset[0]
            elif key == "y":
                value = value - offset[1]
            geometry_attrs[key] = str(value)
    ET.SubElement(cell, "mxGeometry", geometry_attrs)


def style_for(shape_or_style: str | None, default: str) -> str:
    if not shape_or_style:
        return STYLE_MAP[default]
    return STYLE_MAP.get(shape_or_style, shape_or_style)


def edge_style_for(style: str | None) -> str:
    if not style:
        return EDGE_STYLE_MAP["process"]
    return EDGE_STYLE_MAP.get(style, style)


def append_anchor_style(base: str, item: dict[str, Any]) -> str:
    parts = []
    for key in ("exitX", "exitY", "entryX", "entryY"):
        if key in item:
            parts.append(f"{key}={item[key]};")
    for key in ("exitPerimeter", "entryPerimeter"):
        if key in item:
            parts.append(f"{key}={int(bool(item[key]))};")
    return base + "".join(parts)


def label_value(value: Any) -> str:
    return str(value or "").replace("\\n", "\n").replace("\n", "<br>")


def add_vertex(root: ET.Element, item: dict[str, Any], default_shape: str = "process", offset: tuple[float, float] = (0, 0)) -> None:
    cell = ET.SubElement(
        root,
        "mxCell",
        {
            "id": item["id"],
            "value": label_value(item.get("label", "")),
            "style": style_for(item.get("style") or item.get("shape"), default_shape),
            "vertex": "1",
            "parent": item.get("parent", "1"),
        },
    )
    add_geometry(cell, item, offset=offset)


def add_edge(root: ET.Element, item: dict[str, Any]) -> None:
    attrs = {
        "id": item.get("id") or f"edge-{uuid.uuid4().hex[:10]}",
        "value": label_value(item.get("label", "")),
        "style": append_anchor_style(edge_style_for(item.get("style")), item),
        "edge": "1",
        "parent": item.get("parent", "1"),
        "source": item["source"],
        "target": item["target"],
    }
    cell = ET.SubElement(root, "mxCell", attrs)
    add_geometry(cell, item, edge=True)


def validate_spec(spec: dict[str, Any]) -> None:
    cell_ids: set[str] = set()
    group_ids: set[str] = set()
    groups = spec.get("groups", [])
    nodes = spec.get("nodes", [])
    for collection, items in (("groups", groups), ("nodes", nodes)):
        for item in items:
            item_id = item.get("id")
            if not item_id:
                raise ValueError(f"{collection} item missing id")
            if item_id in cell_ids:
                raise ValueError(f"duplicate id: {item_id}")
            cell_ids.add(item_id)
            if collection == "groups":
                group_ids.add(item_id)
            for key in ("x", "y", "width", "height"):
                if key not in item:
                    raise ValueError(f"{item_id} missing {key}")
                number = finite_number(item[key], key, item_id)
                if key in {"width", "height"} and number <= 0:
                    raise ValueError(f"{item_id} {key} must be > 0")
            parent = item.get("parent")
            if parent and parent != "1" and parent not in group_ids:
                raise ValueError(f"{item_id} has unknown parent: {parent}")
    for edge in spec.get("edges", []):
        edge_id = edge.get("id")
        if edge_id:
            if edge_id in cell_ids:
                raise ValueError(f"duplicate id: {edge_id}")
            cell_ids.add(edge_id)
        for endpoint in ("source", "target"):
            if edge.get(endpoint) not in group_ids | {node["id"] for node in nodes}:
                raise ValueError(f"edge {edge.get('id')} has unknown {endpoint}: {edge.get(endpoint)}")
        parent = edge.get("parent")
        if parent and parent != "1" and parent not in group_ids:
            raise ValueError(f"edge {edge.get('id')} has unknown parent: {parent}")
        for point_key in ("sourcePoint", "targetPoint"):
            point = edge.get(point_key)
            if point and ("x" not in point or "y" not in point):
                raise ValueError(f"edge {edge.get('id')} {point_key} must include x and y")
            if point:
                finite_number(point["x"], f"{point_key}.x", edge.get("id", "edge"))
                finite_number(point["y"], f"{point_key}.y", edge.get("id", "edge"))
        for point in edge.get("points", []):
            if "x" not in point or "y" not in point:
                raise ValueError(f"edge {edge.get('id')} points entries must include x and y")
            finite_number(point["x"], "point.x", edge.get("id", "edge"))
            finite_number(point["y"], "point.y", edge.get("id", "edge"))


def build_drawio(spec: dict[str, Any]) -> ET.ElementTree:
    validate_spec(spec)
    mxfile = ET.Element(
        "mxfile",
        {
            "host": "app.diagrams.net",
            "modified": spec.get("modified", ""),
            "agent": "Codex drawio-diagrams skill",
            "version": "24.0.0",
            "type": "device",
        },
    )
    diagram = ET.SubElement(mxfile, "diagram", {"id": spec.get("id", "page-1"), "name": spec.get("title", "Page-1")})
    model = ET.SubElement(
        diagram,
        "mxGraphModel",
        {
            "dx": "1422",
            "dy": "794",
            "grid": "1",
            "gridSize": "10",
            "guides": "1",
            "tooltips": "1",
            "connect": "1",
            "arrows": "1",
            "fold": "1",
            "page": "1",
            "pageScale": "1",
            "pageWidth": str(spec.get("pageWidth", 1600)),
            "pageHeight": str(spec.get("pageHeight", 1200)),
            "math": "0",
            "shadow": "0",
        },
    )
    root = ET.SubElement(model, "root")
    ET.SubElement(root, "mxCell", {"id": "0"})
    ET.SubElement(root, "mxCell", {"id": "1", "parent": "0"})

    group_offsets = {
        group["id"]: (float(group["x"]), float(group["y"]))
        for group in spec.get("groups", [])
    }

    for group in spec.get("groups", []):
        group = {**group, "shape": group.get("shape", "group")}
        add_vertex(root, group, "group")
    for node in spec.get("nodes", []):
        add_vertex(root, node, "process", offset=group_offsets.get(node.get("parent"), (0, 0)))
    for edge in spec.get("edges", []):
        add_edge(root, edge)

    return ET.ElementTree(mxfile)


def write_xml(tree: ET.ElementTree, output: Path) -> None:
    ET.indent(tree, space="  ")
    output.parent.mkdir(parents=True, exist_ok=True)
    tree.write(output, encoding="utf-8", xml_declaration=True)


def example(kind: str) -> dict[str, Any]:
    example_path = EXAMPLES_DIR / f"{kind}.json"
    if example_path.exists():
        return json.loads(example_path.read_text(encoding="utf-8"))
    if kind == "pid":
        return {
            "title": "PID Example",
            "pageWidth": 1200,
            "pageHeight": 700,
            "nodes": [
                {"id": "tank", "label": "20#", "shape": "process", "x": 120, "y": 180, "width": 120, "height": 60},
                {"id": "valve", "label": "XV-21", "shape": "valve", "x": 330, "y": 185, "width": 80, "height": 50},
                {"id": "pump", "label": "P-201", "shape": "pump", "x": 500, "y": 175, "width": 80, "height": 80},
                {"id": "lt", "label": "LT-21", "shape": "instrument", "x": 330, "y": 70, "width": 70, "height": 70},
            ],
            "edges": [
                {"id": "flow1", "source": "tank", "target": "valve", "style": "process"},
                {"id": "flow2", "source": "valve", "target": "pump", "style": "process"},
                {"id": "sig1", "source": "lt", "target": "valve", "label": "open/close", "style": "signal"},
            ],
        }
    return {
        "title": "Flowchart Example",
        "pageWidth": 900,
        "pageHeight": 700,
        "nodes": [
            {"id": "start", "label": "Start", "shape": "terminator", "x": 340, "y": 60, "width": 180, "height": 60},
            {"id": "decision", "label": "Level <= 0.95m?", "shape": "decision", "x": 330, "y": 170, "width": 200, "height": 100},
            {"id": "open", "label": "Open gate", "shape": "process", "x": 340, "y": 330, "width": 180, "height": 70},
            {"id": "end", "label": "Return to monitoring", "shape": "terminator", "x": 310, "y": 480, "width": 240, "height": 60},
        ],
        "edges": [
            {"id": "e1", "source": "start", "target": "decision"},
            {"id": "e2", "source": "decision", "target": "open", "label": "yes"},
            {"id": "e3", "source": "open", "target": "end"},
        ],
    }


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", nargs="?", help="JSON spec path")
    parser.add_argument("output", nargs="?", help="Output .drawio path")
    parser.add_argument("--example", choices=["flowchart", "pid", "architecture", "pipeline"], help="Print an example JSON spec and exit")
    args = parser.parse_args(argv)

    if args.example:
        print(json.dumps(example(args.example), ensure_ascii=False, indent=2))
        return 0
    if not args.input or not args.output:
        parser.error("input and output are required unless --example is used")
    spec = json.loads(Path(args.input).read_text(encoding="utf-8"))
    tree = build_drawio(spec)
    write_xml(tree, Path(args.output))
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
