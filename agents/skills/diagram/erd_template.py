"""Generate a colored, ERD-style draw.io diagram (native XML) plus the HTML link page.

Copy this file next to your diagram source, edit the ENTITIES / COLS / edges sections,
then run it. See SKILL.md "Readability defaults" for the conventions it encodes.

Edges are routed with explicit waypoints through the corridors between columns and the
gaps between stacked entities, so no edge ever crosses a box it doesn't connect.
"""
import json, zlib, base64, os, sys
OUT_DIR = sys.argv[1] if len(sys.argv) > 1 else ".context"
os.makedirs(OUT_DIR, exist_ok=True)
from urllib.parse import quote
from xml.sax.saxutils import escape

# layer -> (header fill, stroke, body fill)
LAYERS = {
    "client": ("#dae8fc", "#6c8ebf", "#f4f8fe"),
    "server": ("#ffe6cc", "#d79b00", "#fff7ee"),
    "pipeline": ("#d5e8d4", "#82b366", "#f3f9f2"),
    "funnel": ("#fff2cc", "#d6b656", "#fffbea"),
    "table": ("#e1d5e7", "#9673a6", "#faf6fc"),
    "join": ("#f5f5f5", "#666666", "#ffffff"),
}

E = {}  # name -> dict
def ent(name, layer, rows, w=460, idx=None):
    E[name] = dict(name=name, layer=layer, rows=rows, w=w, idx=idx or [])

# --- Entities: ent(NAME, layer, [(key, description), ...], width, idx=[...]) -------
# One entity per component. A pipeline is ONE entity with a row per stage (include the
# reject reason on each stage). Use exact names from the code.
# Tables: one row per column; FKs inline on the column row ("FK -> users.id"); indices
# (PK first) in idx=[...], rendered in a separated section at the bottom. Never draw an
# edge between two tables to indicate a FK.
ent("CLIENT_SCREEN", "client", [
    ("GET /api/v1/thing/:id", "-> {a, b, c}"),
    ("some_event", "POST /events {value}; what the server does with it"),
])
ent("REQUEST_HANDLER", "server", [
    ("entry", "POST /events -> handler -> processEvent"),
    ("on some_event", "what happens, which table is written"),
])
ent("VALIDATION_FUNNEL", "funnel", [
    ("[0] normalize", "what it does"),
    ("[1] lex", "reject: lexer"),
    ("[2] insert", "id = hash(expression); existing -> collision"),
])
TW = 340
ent("THINGS", "table", [
    ("id", "BIGINT UNSIGNED"), ("status", "active | reported"), ("created_at", "TIMESTAMP"),
], TW, idx=["PK (id)", "idx_things_status (status, created_at)"])
ent("USER_THING", "join", [
    ("user_id", "FK -> users.id"), ("thing_id", "FK -> things.id"),
], TW, idx=["PK (user_id, thing_id)"])

# columns: x, title, entity order. Keep each column's x at least ~60px past the previous
# column's widest entity so the routing corridors exist (asserted below).
COLS = [
    (40,   "CLIENT", ["CLIENT_SCREEN"]),
    (600,  "API SERVER", ["REQUEST_HANDLER"]),
    (1160, "PIPELINE", ["VALIDATION_FUNNEL"]),
    (1720, "DATABASE TABLES", ["THINGS", "USER_THING"]),
]

HDR = 30
def row_h(key, desc, w):
    n = len(key) + len(desc) + 3
    per_line = w / 6.2
    lines = max(1, int(n / per_line) + (1 if n % per_line else 0))
    return 22 * lines + 4

cells = []
cid = [2]
def nid():
    cid[0] += 1
    return f"c{cid[0]}"

pos = {}
for x, title, names in COLS:
    y = 40
    if title:
        cells.append(f'<mxCell id="{nid()}" value="{escape(title)}" style="text;html=1;fontSize=16;fontStyle=1;align=left;verticalAlign=middle;strokeColor=none;fillColor=none;" vertex="1" parent="1"><mxGeometry x="{x}" y="{y}" width="520" height="30" as="geometry"/></mxCell>')
    y += 50
    for name in names:
        e = E[name]
        hf, st, bf = LAYERS[e["layer"]]
        w = e["w"]
        heights = [row_h(k, d, w) for k, d in e["rows"]]
        idx_heights = [row_h(s, "", w) for s in e["idx"]]
        h = HDR + sum(heights) + (8 + sum(idx_heights) if e["idx"] else 0)
        eid = f"e_{name}"
        pos[name] = (x, y, w, h)
        style = (f"swimlane;html=1;fontStyle=1;fontSize=13;childLayout=stackLayout;horizontal=1;startSize={HDR};"
                 f"horizontalStack=0;resizeParent=1;resizeParentMax=0;resizeLast=0;collapsible=0;marginBottom=0;"
                 f"whiteSpace=wrap;fillColor={hf};strokeColor={st};swimlaneFillColor={bf};rounded=1;arcSize=6;shadow=1;")
        cells.append(f'<mxCell id="{eid}" value="{escape(name)}" style="{style}" vertex="1" parent="1"><mxGeometry x="{x}" y="{y}" width="{w}" height="{h}" as="geometry"/></mxCell>')
        ry = HDR
        for (k, d), rh in zip(e["rows"], heights):
            txt = f"<b>{escape(k)}</b>" + (f"&nbsp; {escape(d)}" if d else "")
            rstyle = (f"text;html=1;strokeColor=none;fillColor=none;align=left;verticalAlign=middle;spacingLeft=6;spacingRight=6;"
                      f"whiteSpace=wrap;overflow=hidden;fontSize=11;")
            cells.append(f'<mxCell id="{nid()}" value="{escape(txt)}" style="{rstyle}" vertex="1" parent="{eid}"><mxGeometry y="{ry}" width="{w}" height="{rh}" as="geometry"/></mxCell>')
            ry += rh
        if e["idx"]:  # index section: hairline, then PK + secondary indices
            cells.append(f'<mxCell id="{nid()}" style="line;strokeWidth=1;html=1;fillColor=none;strokeColor={st};" vertex="1" parent="{eid}"><mxGeometry y="{ry}" width="{w}" height="8" as="geometry"/></mxCell>')
            ry += 8
            for s, rh in zip(e["idx"], idx_heights):
                istyle = ("text;html=1;strokeColor=none;fillColor=none;align=left;verticalAlign=middle;spacingLeft=6;spacingRight=6;"
                          "whiteSpace=wrap;overflow=hidden;fontSize=11;fontStyle=2;fontColor=#666666;")
                cells.append(f'<mxCell id="{nid()}" value="{escape(s)}" style="{istyle}" vertex="1" parent="{eid}"><mxGeometry y="{ry}" width="{w}" height="{rh}" as="geometry"/></mxCell>')
                ry += rh
        y += h + 36

# --- Waypoint router: corridors between columns + gaps between stacked entities -----
ncols = len(COLS)
col_of = {}
for i, (_, _, names) in enumerate(COLS):
    for n in names:
        col_of[n] = i
col_left = [c[0] for c in COLS]
col_right = [max(pos[n][0] + pos[n][2] for n in names) for _, _, names in COLS]

def corridor_x(i):
    """Center of the free vertical corridor to the right of column i (-1 = left of col 0)."""
    if i < 0:
        return col_left[0] - 50
    if i >= ncols - 1:
        return col_right[ncols - 1] + 50
    left, right = col_right[i], col_left[i + 1]
    assert right - left >= 40, f"corridor {i} is {right-left}px; widen the column spacing"
    return (left + right) / 2

def col_bands(i):
    """Free horizontal y values in column i: above, between, and below its entities."""
    boxes = sorted((pos[n][1], pos[n][1] + pos[n][3]) for n in COLS[i][2])
    ys = [boxes[0][0] - 18]
    for (_, b1), (t2, _) in zip(boxes, boxes[1:]):
        ys.append((b1 + t2) / 2)
    ys.append(boxes[-1][1] + 18)
    return ys

_use = {}
def _off(key, step=10):
    """Small per-corridor/per-band offset so parallel edges don't overlap."""
    k = _use.get(key, 0)
    _use[key] = k + 1
    return ((k % 5) - 2) * step

def _side(p):
    x, y = p
    if x == 0: return "L"
    if x == 1: return "R"
    return "T" if y == 0 else "B"

def _abs(name, p):
    x, y, w, h = pos[name]
    return (x + p[0] * w, y + p[1] * h)

def _clear_between(i, ytop, ybot, skip):
    for n in COLS[i][2]:
        if n in skip:
            continue
        t, b = pos[n][1], pos[n][1] + pos[n][3]
        if t < ybot and b > ytop:
            return False
    return True

def route_edge(f, t, exit_pt, entry_pt):
    """Explicit waypoints so the edge crosses no box it doesn't connect."""
    si, ti = col_of[f], col_of[t]
    S, T = _abs(f, exit_pt), _abs(t, entry_pt)
    es, en = _side(exit_pt), _side(entry_pt)
    if si == ti:
        if es in "TB" and en in "TB" and _clear_between(si, min(S[1], T[1]), max(S[1], T[1]), {f, t}):
            return []  # straight shot through the stack gap
        cx = corridor_x(si - 1 if es == "L" else si) + _off(("v", si, es))
        return [(cx, S[1]), (cx, T[1])]
    step = 1 if ti > si else -1
    pts = []
    y = S[1]
    if es in "TB":  # step into the gap beside the source before entering the corridor
        y = pos[f][1] + pos[f][3] + 14 if es == "B" else pos[f][1] - 14
        pts.append((S[0], y))
    ci = si if step == 1 else si - 1
    cx = corridor_x(ci) + _off(("v", ci))
    pts.append((cx, y))
    j = si + step
    while j != ti:  # cross each intermediate column through its nearest free band
        band = min(col_bands(j), key=lambda b: abs(b - T[1])) + _off(("h", j), 6)
        pts.append((cx, band))
        ci = j if step == 1 else j - 1
        cx = corridor_x(ci) + _off(("v", ci))
        pts.append((cx, band))
        j += step
    if en in "TB":
        ty = pos[t][1] - 14 if en == "T" else pos[t][1] + pos[t][3] + 14
        pts.append((cx, ty))
        pts.append((T[0], ty))
    else:
        pts.append((cx, T[1]))
    return pts

# arrows: ER notation. one=ERmandOne, zero-one=ERzeroToOne, many=ERzeroToMany, one-many=ERoneToMany
A = {"1": "ERmandOne", "01": "ERzeroToOne", "0n": "ERzeroToMany", "1n": "ERoneToMany"}
edges = [
    # (from, to, from-card, to-card, label, kind, (exitX,exitY), (entryX,entryY))
    # cards: 1, 01, 0n, 1n   kind: flow|data   pins: fractions of the box side
    # No table-to-table FK edges: FKs are documented in the column rows / index section.
    ("CLIENT_SCREEN", "REQUEST_HANDLER", "0n", "1", "every API call", "flow", (1, 0.5), (0, 0.5)),
    ("REQUEST_HANDLER", "VALIDATION_FUNNEL", "1", "0n", "candidates", "flow", (1, 0.5), (0, 0.5)),
    ("VALIDATION_FUNNEL", "THINGS", "1", "0n", "inserts", "data", (1, 0.5), (0, 0.3)),
]
KIND = {
    "flow": "strokeColor=#d79b00;strokeWidth=2;fontColor=#8a5a00;",
    "data": "strokeColor=#9673a6;strokeWidth=1.5;dashed=1;fontColor=#5e3f6e;",
}
_lbl = {}
def label_x(source):
    """Relative label position along the edge, staggered per source entity.

    draw.io's default midpoint is exactly where corridor-sharing edges run in
    parallel, so their labels stack. The first segment - just past the exit
    pin - is unique per edge, because exit pins on one box never coincide.
    """
    k = _lbl.get(source, 0)
    _lbl[source] = k + 1
    return round(-0.9 + (k % 4) * 0.1, 2)

for f, t, fc, tc, lbl, kind, ex, en in edges:
    pin = f"exitX={ex[0]};exitY={ex[1]};exitDx=0;exitDy=0;entryX={en[0]};entryY={en[1]};entryDx=0;entryDy=0;"
    style = (f"edgeStyle=orthogonalEdgeStyle;orthogonalLoop=1;jettySize=auto;html=1;rounded=1;"
             f"startArrow={A[fc]};startFill=0;endArrow={A[tc]};endFill=0;fontSize=10;"
             f"labelBackgroundColor=#ffffff;{pin}{KIND[kind]}")
    wps = route_edge(f, t, ex, en)
    geo = f'<mxGeometry relative="1" x="{label_x(f)}" as="geometry">'
    if wps:
        geo += '<Array as="points">' + "".join(f'<mxPoint x="{round(px)}" y="{round(py)}"/>' for px, py in wps) + '</Array>'
    geo += '</mxGeometry>'
    cells.append(f'<mxCell id="{nid()}" value="{escape(lbl)}" style="{style}" edge="1" parent="1" source="e_{f}" target="e_{t}">{geo}</mxCell>')

# legend
lg = [("client", "Client screens (React)"), ("server", "API server handlers"), ("pipeline", "Problem pipeline"),
      ("funnel", "Highlighted pipeline"), ("table", "Database table"), ("join", "Join / derived table")]
lx = 40
ly = max(p[1] + p[3] for p in pos.values()) + 60  # below the tallest column
cells.append(f'<mxCell id="{nid()}" value="Legend" style="text;html=1;fontStyle=1;fontSize=13;strokeColor=none;fillColor=none;" vertex="1" parent="1"><mxGeometry x="{lx}" y="{ly}" width="200" height="24" as="geometry"/></mxCell>')
for i, (k, txt) in enumerate(lg):
    hf, st, bf = LAYERS[k]
    cells.append(f'<mxCell id="{nid()}" value="{escape(txt)}" style="rounded=1;html=1;fillColor={hf};strokeColor={st};fontSize=11;align=left;spacingLeft=6;" vertex="1" parent="1"><mxGeometry x="{lx}" y="{ly+30+i*30}" width="220" height="24" as="geometry"/></mxCell>')
for i, (k, txt) in enumerate([("flow", "control flow (solid orange)"), ("data", "reads / writes (dashed purple)")]):
    cells.append(f'<mxCell id="{nid()}" value="{escape(txt)}" style="text;html=1;fontSize=11;align=left;strokeColor=none;fillColor=none;" vertex="1" parent="1"><mxGeometry x="{lx+240}" y="{ly+30+i*30}" width="260" height="24" as="geometry"/></mxCell>')
    cells.append(f'<mxCell id="{nid()}" style="html=1;endArrow=ERzeroToMany;startArrow=ERmandOne;endFill=0;startFill=0;{KIND[k]}" edge="1" parent="1"><mxGeometry relative="1" as="geometry"><mxPoint x="{lx+500}" y="{ly+42+i*30}" as="sourcePoint"/><mxPoint x="{lx+580}" y="{ly+42+i*30}" as="targetPoint"/></mxGeometry></mxCell>')

xml = '<mxGraphModel adaptiveColors="auto" grid="0" page="0"><root><mxCell id="0"/><mxCell id="1" parent="0"/>' + "".join(cells) + '</root></mxGraphModel>'
open(OUT_DIR + "/diagram.drawio", "w").write(xml)

encoded = quote(xml, safe='')
c = zlib.compressobj(9, zlib.DEFLATED, -15)
raw = c.compress(encoded.encode('utf-8')) + c.flush()
data = base64.b64encode(raw).decode()
payload = json.dumps({"type": "xml", "compressed": True, "data": data})
url = f"https://app.diagrams.net/?pv=0&grid=0#create={quote(payload, safe='')}"
html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8">
<style>
body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;display:flex;justify-content:center;align-items:center;min-height:100vh;margin:0;background:#f8f9fa}}
.card{{text-align:center;background:white;border-radius:12px;padding:40px;box-shadow:0 2px 8px rgba(0,0,0,0.1)}}
.card h2{{margin:0 0 8px;color:#1a1a1a}} .card p{{margin:0 0 24px;color:#666}}
.btn{{display:inline-block;padding:14px 32px;background:#4285f4;color:white;text-decoration:none;border-radius:8px;font-size:16px;font-weight:500}}
.btn:hover{{background:#3367d6}}
</style></head><body><div class="card"><h2>Diagram Ready</h2><p>Click below to open your diagram in draw.io</p>
<a class="btn" href="{url}" target="_blank" rel="noopener noreferrer">Open in draw.io</a></div></body></html>"""
open(OUT_DIR + "/diagram.html", "w").write(html)
print("url length", len(url))
