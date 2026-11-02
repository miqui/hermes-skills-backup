---
name: drawio-workflow-diagrams
description: "Use when a README needs a workflow diagram plus PNG render."
version: 1.0.0
license: MIT
metadata:
  hermes:
    tags: [drawio, diagrams, documentation, readme, workflow]
---

# Drawio workflow diagrams + PNG export for READMEs

## Deliverable set (all four, every time)

1. `docs/<name>.drawio` — editable source of truth, committed.
2. `docs/<name>.png` — rendered FROM that file (never a hand-drawn substitute or a parallel-format redraw).
3. README embed with a caption pointing to the editable source.
4. Visual verification of the PNG before presenting it.

## Procedure

### 1. Author the .drawio XML
Generate it from a script or write it directly: `mxfile > diagram > mxGraphModel > root`, nodes as `mxCell vertex="1"` with `mxGeometry`, edges as `mxCell edge="1" source= target=`. Keep a NODES/EDGES table in the generator so the diagram stays regenerable.

**Always set explicit anchors and waypoints for any non-trivial layout** — add `exitX/exitY/entryX/entryY` (fractions 0-1 of the node box) to edge styles and explicit `<Array as="points">` waypoints. Drawio's auto-routing runs edges straight through node boxes and drops labels on top of node text; explicit routing is the only thing that prevents it. Use `labelBackgroundColor=#ffffff` so edge labels stay readable where they cross lines.

### 2. Validate the XML
`python3 -c "import xml.dom.minidom; xml.dom.minidom.parse('<file>')"` before rendering.

### 3. Render the PNG via the headless exporter (no drawio app or CLI needed)

```bash
docker images | grep drawio-export   # rlespinasse/drawio-export — check before pulling (~2GB image)
docker run --rm -v "$PWD":/data -w /data rlespinasse/drawio-export -f png -o . --output-mode relative docs
```

- Run from the REPO ROOT — the mount is `$PWD`, and the exporter errors with `path 'docs' must exist` if you run it from elsewhere.
- Output is named `<file>-<diagram-page-name>.png`; rename to `docs/<name>.png` immediately.

### 4. Verify the render

```bash
sips -g pixelWidth -g pixelHeight docs/<name>.png   # expect real dimensions, file > ~10KB
```

Then LOOK at it (vision tool) checking specifically: labels clear of node text, no arrows piercing boxes, nothing clipped. Iterate the anchors/waypoints and re-render until clean — expect one routing-fix round on any diagram with branches.

### 5. Embed in README

```markdown
![Workflow](docs/<name>.png)
*Rendered from docs/<name>.drawio — open in draw.io to edit.*
```

Keep any pre-existing ASCII diagram as a terminal fallback; add the image section without restructuring the README.

## Pitfalls

- If the docker export fails after real attempts with different flags, STOP and report the error — never substitute a hand-drawn PNG and present it as the render of the .drawio file.
- A .drawio with default auto-routing looks fine in the XML but renders with overlapping labels — judge the PNG, never the XML.
