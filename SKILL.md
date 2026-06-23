---
name: drawio-diagrams
description: Use when the user asks for editable diagrams.net/draw.io files, flowcharts, swimlane diagrams, architecture diagrams, data pipelines, equipment-control diagrams, simplified PID/P&ID-style diagrams, `.drawio` files, or diagrams they can later modify in draw.io/diagrams.net.
---

# Draw.io Diagrams

## Overview

Use this skill to produce editable `.drawio` files, not only static PNG/PDF/SVG images. Prefer `.drawio` as the source of truth when the user wants to revise nodes, move shapes, change labels, or continue editing in diagrams.net/draw.io Desktop.

The skill supports:
- Flowcharts and swimlane-style process diagrams.
- Simplified PID/P&ID-style control diagrams with pumps, valves, instruments, process lines, and dashed signal lines.
- Optional Mermaid companion files for lightweight text editing when the user wants one; Mermaid is manually translated into the JSON spec, not parsed by a bundled converter.
- Optional PNG/PDF/SVG previews when local export tools are available.

## Workflow

1. Extract the process model.
   - From documents: extract relevant paragraphs/tables first.
   - From Mermaid text: manually translate the graph into the JSON spec and preserve node IDs and edge labels when possible.
   - From free text: identify equipment, states, decisions, actions, thresholds, and branch ownership.

2. Build a small JSON diagram spec.
   - Use `scripts/generate_drawio.py --example flowchart` or `--example pid` to inspect the expected schema.
   - For fuller starting points, copy from `examples/flowchart.json`, `examples/pid.json`, `examples/architecture.json`, or `examples/pipeline.json`.
   - Keep node IDs stable and meaningful: `DW_LOW`, `A_PUMP_START`, `XV_21_NORTH`.
   - Use explicit `x`, `y`, `width`, and `height`. Do not rely on auto layout for engineering diagrams.
   - For complex routes, use `edges[].points` and optional `entryX/entryY/exitX/exitY` anchors to preserve connector routing.

3. Generate the editable `.drawio`.
   - Run: `python scripts/generate_drawio.py spec.json output.drawio`
   - The output is an uncompressed `<mxfile>` with editable cells.
   - Also provide `.mmd` if the user wants a text-editable companion.

4. Verify the output.
   - Parse the `.drawio` as XML and check it has `<mxfile>`, `<diagram>`, `<mxGraphModel>`, root cells `0` and `1`, and nonzero vertex/edge cells.
   - For packaged examples, run `python3 scripts/test_examples.py`.
   - Open or render a preview when possible.
   - If draw.io Desktop CLI exists, export preview files with:
     `drawio --export --format png --output output.png output.drawio`

5. Deliver the editable source first.
   - Return `.drawio` as the primary deliverable.
   - Return `.mmd`, `.png`, `.pdf`, or `.svg` as supporting files only when useful.

## Design Rules

- Use `.drawio` for editability. PNG/PDF/SVG are previews or print exports.
- Use uncompressed XML. It is easier for agents and humans to inspect, diff, and patch.
- Keep labels short inside shapes. Put long operational notes in companion Markdown or in side note boxes.
- For flowcharts:
  - Terminator: rounded rectangle.
  - Process/action: rectangle.
  - Decision: diamond.
  - Branches: group or swimlane containers.
- For simplified PID/P&ID:
  - Process flow: solid connector.
  - Control/signal flow: dashed connector.
  - Pump: ellipse or triangle-in-circle symbol.
  - Valve: bow-tie symbol or compact valve box.
  - Instrument: circle with tag, e.g. `LT-21`.
  - Use explicit tags when available; otherwise use conservative provisional tags.

## Resources

- `scripts/generate_drawio.py`: generate editable `.drawio` XML from a JSON spec.
- `references/drawio-xml-patterns.md`: schema, style, and validation notes.
- `examples/`: ready-to-run JSON specs for common diagram types.
- `scripts/test_examples.py`: generate and validate every bundled example.

Read the reference file when building a custom generator, debugging malformed `.drawio`, or adding new diagram types.
