# drawio-diagrams skill

Create editable diagrams.net / draw.io `.drawio` files from a small JSON diagram spec.

This is an agent skill for producing editable diagrams, not a fork of the
official diagrams.net / draw.io application. The generated files are ordinary
uncompressed `.drawio` XML files that can be opened and edited in diagrams.net
or draw.io Desktop.

## What It Supports

- Flowcharts
- Swimlane-style grouped diagrams
- Architecture diagrams
- Data pipelines
- Equipment-control diagrams
- Simplified P&ID-style diagrams
- Solid process connectors and dashed signal connectors
- Explicit connector waypoints and entry/exit anchors for more stable routing

## Install

Install from this GitHub repository with the skills CLI:

```bash
npx skills add johnathonstarkwill-jpg/drawio-diagrams-skill
```

For Codex:

```bash
npx skills add johnathonstarkwill-jpg/drawio-diagrams-skill -a codex
```

Repository:

```text
https://github.com/johnathonstarkwill-jpg/drawio-diagrams-skill
```

If you fork this skill into a subdirectory of another repository, install with
the full GitHub tree URL:

```bash
npx skills add https://github.com/<owner>/<repo>/tree/main/drawio-diagrams
```

## Use In An Agent

Ask the agent to use the skill, for example:

```text
Use the drawio-diagrams skill to create an editable draw.io flowchart for this process...
```

The skill will normally produce:

- a `.drawio` file as the editable source
- optionally a `.mmd` companion file when Mermaid text is useful
- optionally PNG/SVG/PDF previews when a local draw.io CLI is available

## Use The Scripts Directly

Requires Python 3.9+.

Generate from a JSON spec:

```bash
python3 scripts/generate_drawio.py examples/flowchart.json out/flowchart.drawio
python3 scripts/validate_drawio.py out/flowchart.drawio
```

Print bundled example specs:

```bash
python3 scripts/generate_drawio.py --example flowchart
python3 scripts/generate_drawio.py --example pid
python3 scripts/generate_drawio.py --example architecture
python3 scripts/generate_drawio.py --example pipeline
```

Run all bundled checks:

```bash
python3 scripts/test_examples.py
```

On Windows PowerShell, use `py`:

```powershell
py scripts/generate_drawio.py examples/flowchart.json out/flowchart.drawio
py scripts/validate_drawio.py out/flowchart.drawio
```

## JSON Spec

Minimal example:

```json
{
  "title": "Example",
  "pageWidth": 900,
  "pageHeight": 700,
  "nodes": [
    {
      "id": "start",
      "label": "Start",
      "shape": "terminator",
      "x": 340,
      "y": 60,
      "width": 180,
      "height": 60
    },
    {
      "id": "next",
      "label": "Next step",
      "shape": "process",
      "x": 340,
      "y": 180,
      "width": 180,
      "height": 70
    }
  ],
  "edges": [
    {
      "id": "e1",
      "source": "start",
      "target": "next"
    }
  ]
}
```

Common fields:

- `groups`: container rectangles with `id`, `label`, `x`, `y`, `width`, `height`
- `nodes[].shape`: `terminator`, `process`, `decision`, `note`, `instrument`, `pump`, `valve`, `database`, `cloud`, `document`, `store`, `offpage`
- `nodes[].parent`: group id; write coordinates as absolute page coordinates
- `edges[].style`: `process`, `signal`, `line`, or a raw draw.io style string
- `edges[].points`: optional waypoint list, for example `[{"x": 300, "y": 120}]`
- `edges[].entryX`, `entryY`, `exitX`, `exitY`: optional draw.io connector anchors

Labels may contain either real newlines or `\n`; the generator converts them to
draw.io `<br>` line breaks.

## Examples

Bundled JSON examples:

- `examples/flowchart.json`
- `examples/pid.json`
- `examples/architecture.json`
- `examples/pipeline.json`

Generate all examples:

```bash
mkdir -p out
for f in examples/*.json; do
  name="$(basename "$f" .json)"
  python3 scripts/generate_drawio.py "$f" "out/$name.drawio"
  python3 scripts/validate_drawio.py "out/$name.drawio"
done
```

## Validation

The generator validates:

- required node/group geometry
- numeric and finite coordinates
- positive width and height
- globally unique cell ids
- existing parents
- existing edge sources and targets
- valid waypoint and anchor coordinates

The XML validator checks:

- `.drawio` XML structure
- root cells `0` and `1`
- vertex geometry and positive sizes
- duplicate ids
- unknown parents
- edge geometry
- literal `\n` that should have been converted to `<br>`

The validator uses `defusedxml` when installed and falls back to the Python
standard library for trusted local outputs.

## Limitations

- This is a pragmatic JSON-to-drawio generator, not a full diagrams.net renderer.
- Mermaid text is manually translated by the agent into the JSON spec; there is
  no bundled Mermaid parser.
- P&ID support is simplified. For formal engineering drawings, use the output as
  an editable draft and review symbols/standards in a CAD or engineering tool.
- Complex diagrams may still need explicit `edges[].points` to preserve a clean route.

## License

MIT. See [LICENSE](LICENSE).
