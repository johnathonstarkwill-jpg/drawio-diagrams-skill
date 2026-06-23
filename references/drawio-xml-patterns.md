# Draw.io XML Patterns

## File Shape

Use uncompressed diagrams.net XML:

```xml
<mxfile host="app.diagrams.net" type="device">
  <diagram name="Page-1">
    <mxGraphModel ...>
      <root>
        <mxCell id="0"/>
        <mxCell id="1" parent="0"/>
        ...
      </root>
    </mxGraphModel>
  </diagram>
</mxfile>
```

Every visible cell is an `mxCell` under parent `1` or a group cell. Vertices need `vertex="1"` and an `mxGeometry` child with `x`, `y`, `width`, and `height`. Edges need `edge="1"`, `source`, `target`, and a relative `mxGeometry`.

## Core Styles

Recommended style tokens:

- `terminator`: `rounded=1;whiteSpace=wrap;html=1;arcSize=50;`
- `process`: `rounded=1;whiteSpace=wrap;html=1;`
- `decision`: `rhombus;whiteSpace=wrap;html=1;`
- `group`: `rounded=1;whiteSpace=wrap;html=1;container=1;recursiveResize=0;collapsible=0;`
- `instrument`: `ellipse;whiteSpace=wrap;html=1;aspect=fixed;`
- `pump`: `ellipse;whiteSpace=wrap;html=1;aspect=fixed;`
- `valve`: use `shape=process` with a short `XV`/valve label unless a custom symbol library is available.

Connectors:

- Solid process line: `edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;endArrow=block;`
- Dashed signal line: add `dashed=1;dashPattern=8 8;`

## Validation Checklist

- XML parses without errors.
- Root contains `mxCell id="0"` and `mxCell id="1" parent="0"`.
- All node IDs are unique.
- Every edge source/target points to an existing vertex or group.
- Every vertex has nonzero width and height.
- Labels are escaped as XML text.
- Long labels are manually wrapped or moved into notes.

## JSON Spec Used By `generate_drawio.py`

Minimal shape:

```json
{
  "title": "Example",
  "nodes": [
    {"id": "start", "label": "Start", "shape": "terminator", "x": 120, "y": 80, "width": 160, "height": 60}
  ],
  "edges": [
    {"id": "e1", "source": "start", "target": "next", "label": "yes"}
  ]
}
```

Optional:

- `groups`: container rectangles with `id`, `label`, `x`, `y`, `width`, `height`, `style`.
- `nodes[].parent`: group ID. Write coordinates as absolute page coordinates; the generator converts child geometry to draw.io's parent-relative coordinates.
- `nodes[].shape`: `terminator`, `process`, `decision`, `note`, `instrument`, `pump`, `valve`, or `group`.
- `edges[].style`: `process`, `signal`, or a raw draw.io style string.

## Bundled Examples

Requires Python 3.9+ (`xml.etree.ElementTree.indent`). The validator uses
`defusedxml` when installed and falls back to the Python standard library for
trusted local outputs.

Run these from the skill directory on macOS/Linux:

```bash
python3 scripts/generate_drawio.py examples/flowchart.json out/flowchart.drawio
python3 scripts/generate_drawio.py examples/pid.json out/pid.drawio
python3 scripts/generate_drawio.py examples/architecture.json out/architecture.drawio
python3 scripts/generate_drawio.py examples/pipeline.json out/pipeline.drawio
```

The same specs can be printed with:

```bash
python3 scripts/generate_drawio.py --example flowchart
python3 scripts/generate_drawio.py --example pid
python3 scripts/generate_drawio.py --example architecture
python3 scripts/generate_drawio.py --example pipeline
```

On Windows PowerShell, use `py`:

```powershell
py scripts/generate_drawio.py examples/flowchart.json out/flowchart.drawio
py scripts/validate_drawio.py out/flowchart.drawio
```

Run all bundled example checks with:

```bash
python3 scripts/test_examples.py
```
