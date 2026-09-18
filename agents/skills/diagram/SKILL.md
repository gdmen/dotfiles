---
name: diagram
description: Generate visual diagrams (flowcharts, UML, ERD, architecture, org charts, cloud/infra, BPMN, wireframes, etc.) as draw.io links via Mermaid, CSV, or draw.io XML. Use when the user asks for a diagram or invokes /diagram.
---

# Draw.io Diagram Generation

When the user requests any visual diagram, use draw.io to create it.

## Supported Diagrams

Draw.io supports virtually any diagram type:
- **Standard**: Flowcharts, org charts, mind maps, timelines, Venn diagrams
- **Software**: UML (class, sequence, activity, use case), ERD, architecture diagrams
- **Cloud/Infrastructure**: AWS, Azure, GCP, Kubernetes, network topology
- **Engineering**: Electrical circuits, digital logic, P&ID, floor plans
- **Business**: BPMN, value streams, customer journeys, SWOT
- **UI/UX**: Wireframes, mockups, sitemaps
- **And more**: Infographics, data flows, decision trees, etc.

## Format Selection

| Format | Best For |
|--------|----------|
| **Mermaid** | Flowcharts, sequences, ERD, Gantt, state diagrams, class diagrams |
| **CSV** | Hierarchical data (org charts), bulk import from spreadsheets |
| **XML** | Complex layouts, precise positioning, custom styling, icons, shapes. **Default for codebase / system / ERD-style diagrams** (see Readability defaults) — Mermaid import drops colors and per-entity styling |

## URL Generation

Execute this Python code to generate the draw.io URL and output it as an HTML artifact:

```python
import json, zlib, base64
from urllib.parse import quote

# Set these variables:
diagram_type = "mermaid"  # "mermaid", "xml", or "csv"
diagram_code = """graph TD
    A[Start] --> B[End]"""

# Generate compressed URL
encoded = quote(diagram_code, safe='')
c = zlib.compressobj(9, zlib.DEFLATED, -15)
raw_deflate = c.compress(encoded.encode('utf-8')) + c.flush()
data = base64.b64encode(raw_deflate).decode()

payload = json.dumps({"type": diagram_type, "compressed": True, "data": data})
url = f"https://app.diagrams.net/?pv=0&grid=0#create={quote(payload, safe='')}"

# Output as HTML page
print(f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  body {{
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    display: flex;
    justify-content: center;
    align-items: center;
    min-height: 100vh;
    margin: 0;
    background: #f8f9fa;
  }}
  .card {{
    text-align: center;
    background: white;
    border-radius: 12px;
    padding: 40px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  }}
  .card h2 {{ margin: 0 0 8px; color: #1a1a1a; }}
  .card p {{ margin: 0 0 24px; color: #666; }}
  .btn {{
    display: inline-block;
    padding: 14px 32px;
    background: #4285f4;
    color: white;
    text-decoration: none;
    border-radius: 8px;
    font-size: 16px;
    font-weight: 500;
    transition: background 0.2s;
  }}
  .btn:hover {{ background: #3367d6; }}
</style>
</head>
<body>
  <div class="card">
    <h2>Diagram Ready</h2>
    <p>Click below to open your diagram in draw.io</p>
    <a class="btn" href="{url}" target="_blank" rel="noopener noreferrer">
      Open in draw.io
    </a>
  </div>
</body>
</html>""")
```

## Readability defaults (codebase, architecture, and ERD-style diagrams)

House defaults for any diagram of a system or codebase. Apply them unless asked for
something lighter.

### Level of detail

- **Read before drawing.** Read the project's docs and skim the owning files first; for a
  big repo, fan out Explore agents per area and draw from their summaries.
- **Use exact names from the code**: routes with method + path, handler / function names,
  event type strings, table and column names, version constants, numeric thresholds. Never
  paraphrase a name the reader might grep for.
- **One entity per component, rows for its steps.** A screen, a middleware chain, a
  processor, a pipeline, a table: each is one box whose header is the name and whose rows
  are `**key** description`.
- **Tables get real columns, one row per column**: type, enum values, and a short note
  when the meaning isn't obvious. A foreign key is described on its column row, bold
  column name then the FK note: **user_id**&nbsp; `FK -> users.id`. Indices, PK
  included, go in a separated section at the bottom of the block, PK first
  (`PK (user_id, problem_id)`, then secondary indices) — the template renders it below
  a hairline via `idx=[...]`.
- **Never draw an edge between two tables to indicate a foreign key.** FK
  relationships live in the column rows and the index section; edges are reserved for
  control flow and reads/writes.
- **Include scheduled/background work.** systemd timers, cron jobs, and queue workers
  are a layer of their own (check `deploy/`, unit files, crontabs): one entity per job
  with its schedule, what it runs, and edges to the tables it touches.
- **Edges carry cardinality and a label** (what triggers the transition, or which
  column/action is written).
- **Add a legend** for the colors and edge styles.

### Colors: one color per layer

Assign a layer to every entity and color by layer. Header gets the fill, body gets a paler
tint (`swimlaneFillColor`), stroke matches. Default palette (draw.io standard swatches):

| Layer | fill | stroke | body |
|---|---|---|---|
| Client / UI screens | `#dae8fc` | `#6c8ebf` | `#f4f8fe` |
| Server handlers / middleware | `#ffe6cc` | `#d79b00` | `#fff7ee` |
| Domain pipeline / generators | `#d5e8d4` | `#82b366` | `#f3f9f2` |
| Highlighted block (validation, funnel) | `#fff2cc` | `#d6b656` | `#fffbea` |
| Database tables | `#e1d5e7` | `#9673a6` | `#faf6fc` |
| Join / derived / external | `#f5f5f5` | `#666666` | `#ffffff` |

Edge styles, also by meaning:

| Edge | style |
|---|---|
| Control flow | solid, `strokeColor=#d79b00;strokeWidth=2` |
| Read / write to a table | dashed, `strokeColor=#9673a6;strokeWidth=1.5;dashed=1` |

Use ER arrowheads (`ERmandOne`, `ERzeroToOne`, `ERzeroToMany`, `ERoneToMany`) with
`startFill=0;endFill=0`, `edgeStyle=orthogonalEdgeStyle;rounded=1`, and
`labelBackgroundColor=#ffffff` on labels.

**No edge may intersect a box it doesn't connect — hard requirement.** draw.io's
automatic orthogonal router does not guarantee this, so never rely on it: give every
edge explicit waypoints (`<Array as="points">` of `mxPoint`s) routed through the
vertical corridors between columns and the horizontal gaps between stacked entities.
`erd_template.py`'s `route_edge` computes these from the pinned endpoints — declare
each edge with its exit/entry sides (`exitX/exitY`, `entryX/entryY`, also required so
edges sharing a target enter at different points) and let it route. Keep each column's
x at least ~60px past the previous column's widest entity so the corridors exist (the
template asserts this).

**Edge labels must not overlap.** draw.io places labels at the path midpoint,
which is exactly where corridor-sharing edges run in parallel. Pin every label
to its edge's first segment instead (edge geometry relative `x` near -1,
staggered per source entity) — exit pins are unique per box, so labels inherit
that separation. `erd_template.py`'s `label_x` does this.

### Layout

- **Columns by layer**, left to right in the direction of the flow: client → server →
  domain pipeline → tables (split tables over two columns if there are more than ~6).
- A bold column title above each column; entities stacked with ~36px gaps.
- Entity = `swimlane;childLayout=stackLayout;horizontal=1;startSize=30;resizeParent=1;
  rounded=1;arcSize=6;shadow=1;whiteSpace=wrap`, rows = `text;html=1;align=left;
  whiteSpace=wrap;fontSize=11`. Widen process blocks (~460px) more than tables (~340px)
  and grow row height for wrapped text.
- Generate the XML from a script, not by hand: copy `erd_template.py` from this skill's
  directory, fill in the entity/edge/column lists, and run it. It writes the `.drawio`
  XML and the HTML link page. Validate with `xml.dom.minidom.parse` before publishing.

### Delivering from the CLI

There is no artifact panel in the terminal: write the HTML to a gitignored scratch
directory (`.context/diagram.html` in Conductor workspaces), with the `.drawio` / `.mmd`
source and the generator script next to it, then `open` it so the browser shows the button. Tell the user the paths so they can
regenerate. Still never paste the URL into chat.

## XML Reference

For detailed guidance on edge routing, containers, layers, tags, metadata, dark mode
colors, style properties, and XML well-formedness, see:
https://github.com/jgraph/drawio-mcp/blob/main/shared/xml-reference.md

## Format Examples

### Mermaid
```
graph TD
    A[Start] --> B{Decision}
    B -->|Yes| C[Action]
    B -->|No| D[End]
```

### XML (draw.io native)
```xml
<mxGraphModel adaptiveColors="auto">
  <root>
    <mxCell id="0"/>
    <mxCell id="1" parent="0"/>
    <mxCell id="2" value="Box" style="rounded=1;fillColor=#d5e8d4;" vertex="1" parent="1">
      <mxGeometry x="100" y="100" width="120" height="60" as="geometry"/>
    </mxCell>
  </root>
</mxGraphModel>
```

### CSV (hierarchical data)
```
# label: %name%
# style: rounded=1;whiteSpace=wrap;html=1;
# connect: {"from":"manager","to":"name","invert":true}
# layout: auto
name,manager
CEO,
CTO,CEO
CFO,CEO
```

## Instructions

1. Determine the best format.
2. Generate the diagram code.
3. Execute the Python code to create the URL.
4. **Create an HTML artifact** from the script output — the clickable link for the user.

## CRITICAL: XML Well-Formedness

- **NEVER include XML comments (`<!-- -->`) in draw.io XML output.** They waste tokens and can cause parse errors.
- Escape special characters in attribute values (`&amp;`, `&lt;`, `&gt;`, `&quot;`).

## CRITICAL: URL Output Rules

**NEVER type, retype, or reproduce the generated URL in your chat response.** The URL
contains compressed base64 data; a single changed character breaks it.

1. Execute the Python script.
2. The script outputs a complete HTML page with the correct link embedded.
3. Present the HTML output as the artifact (the link inside is guaranteed correct).
4. In chat, just tell the user to click the button in the artifact.
