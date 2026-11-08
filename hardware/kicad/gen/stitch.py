"""Vias de cosido GND: une cada pad GND (cara superior/inferior) al plano interno In1 y
coloca vias termicas en el pad expuesto del AD7124. Las zonas GND pasan a conexion solida."""
import math
import os
import pcbnew

PROJ = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PCB = os.path.join(PROJ, "microohmetro_v2.kicad_pcb")
b = pcbnew.LoadBoard(PCB)
MM, TO = pcbnew.FromMM, pcbnew.ToMM
gnd = b.FindNet("GND")
VIA_D, VIA_H, CLR = 0.6, 0.3, 0.2

for z in b.Zones():
    if not z.GetIsRuleArea():
        z.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL)

obst = []  # (tipo, geometria, red)
for p in b.GetPads():
    bb = p.GetBoundingBox()
    obst.append(("box", (TO(bb.GetLeft()), TO(bb.GetTop()), TO(bb.GetRight()), TO(bb.GetBottom())), p.GetNetCode(), p))
for t in b.GetTracks():
    if t.GetClass() == "PCB_TRACK":
        obst.append(("seg", (TO(t.GetStart().x), TO(t.GetStart().y), TO(t.GetEnd().x), TO(t.GetEnd().y), TO(t.GetWidth()) / 2),
                     t.GetNetCode(), t))
    elif t.GetClass() == "PCB_VIA":
        obst.append(("via", (TO(t.GetPosition().x), TO(t.GetPosition().y), TO(t.GetWidth(pcbnew.F_Cu)) / 2), t.GetNetCode(), t))
edge = b.GetBoardEdgesBoundingBox()
EX0, EY0, EX1, EY1 = TO(edge.GetLeft()), TO(edge.GetTop()), TO(edge.GetRight()), TO(edge.GetBottom())
keep = []
for z in b.Zones():
    if z.GetIsRuleArea():
        bb = z.GetBoundingBox()
        keep.append((TO(bb.GetLeft()), TO(bb.GetTop()), TO(bb.GetRight()), TO(bb.GetBottom())))


def dseg(px, py, x1, y1, x2, y2):
    dx, dy = x2 - x1, y2 - y1
    L = dx * dx + dy * dy
    u = 0 if L == 0 else max(0, min(1, ((px - x1) * dx + (py - y1) * dy) / L))
    return math.hypot(px - (x1 + u * dx), py - (y1 + u * dy))


def free(x, y, r, net, ignore=None):
    if x - r < EX0 + 0.5 or x + r > EX1 - 0.5 or y - r < EY0 + 0.5 or y + r > EY1 - 0.5:
        return False
    for k in keep:
        if k[0] - r < x < k[2] + r and k[1] - r < y < k[3] + r:
            return False
    for kind, g, nc, obj in obst:
        if obj is ignore:
            continue
        need = r + CLR if nc != net else 0
        if nc == net and kind != "box":
            continue
        if kind == "box":
            dx = max(g[0] - x, 0, x - g[2])
            dy = max(g[1] - y, 0, y - g[3])
            if math.hypot(dx, dy) < (need if nc != net else 0) or (nc == net and obj is not ignore and math.hypot(dx, dy) < 0.05 and False):
                return False
        elif kind == "seg":
            if dseg(x, y, *g[:4]) < need + g[4]:
                return False
        else:
            if math.hypot(x - g[0], y - g[1]) < need + g[2]:
                return False
    return True


def add_via(x, y):
    v = pcbnew.PCB_VIA(b)
    v.SetPosition(pcbnew.VECTOR2I(MM(x), MM(y)))
    v.SetWidth(MM(VIA_D)); v.SetDrill(MM(VIA_H)); v.SetNet(gnd); v.SetViaType(pcbnew.VIATYPE_THROUGH)
    b.Add(v)
    obst.append(("via", (x, y, VIA_D / 2), gnd.GetNetCode(), v))


def add_track(x1, y1, x2, y2, layer):
    t = pcbnew.PCB_TRACK(b)
    t.SetStart(pcbnew.VECTOR2I(MM(x1), MM(y1))); t.SetEnd(pcbnew.VECTOR2I(MM(x2), MM(y2)))
    t.SetWidth(MM(0.3)); t.SetLayer(layer); t.SetNet(gnd)
    b.Add(t)
    obst.append(("seg", (x1, y1, x2, y2, 0.15), gnd.GetNetCode(), t))


n_via = 0
# 1) vias termicas en el EP del AD7124 (U601 pad 33)
u = b.FindFootprintByReference("U601")
for p in u.Pads():
    if p.GetNumber() == "33":
        cx, cy = TO(p.GetPosition().x), TO(p.GetPosition().y)
        for dx in (-0.9, 0, 0.9):
            for dy in (-0.9, 0, 0.9):
                if free(cx + dx, cy + dy, VIA_D / 2, gnd.GetNetCode()):
                    add_via(cx + dx, cy + dy); n_via += 1
# 2) cada pad SMD de GND recibe una via (en el pad si es grande, si no, con un tramo corto)
for p in b.GetPads():
    if p.GetNetCode() != gnd.GetNetCode() or p.GetAttribute() not in (pcbnew.PAD_ATTRIB_SMD,):
        continue
    if p.GetParentFootprint().GetReference() in ("U601", "J101", "U201", "U701") and p.GetNumber() in ("33", "25", "19", "SH"):
        continue
    cx, cy = TO(p.GetPosition().x), TO(p.GetPosition().y)
    sx, sy = TO(p.GetSize(pcbnew.F_Cu).x), TO(p.GetSize(pcbnew.F_Cu).y)
    layer = pcbnew.B_Cu if p.IsOnLayer(pcbnew.B_Cu) and not p.IsOnLayer(pcbnew.F_Cu) else pcbnew.F_Cu
    if min(sx, sy) >= 1.0 and free(cx, cy, VIA_D / 2, gnd.GetNetCode()) and not any(
            k == 'via' and math.hypot(g[0] - cx, g[1] - cy) < 1.0 for k, g, nc, o in obst):
        add_via(cx, cy); n_via += 1
        continue
    fc = p.GetParentFootprint().GetPosition()
    ang0 = math.atan2(cy - TO(fc.y), cx - TO(fc.x))
    done = False
    for dist in (0.9, 1.2, 1.5, 1.9, 2.4):
        for k in range(16):
            a = ang0 + (k // 2 + 1) * (math.pi / 8) * (1 if k % 2 else -1) if k else ang0
            x, y = cx + dist * math.cos(a), cy + dist * math.sin(a)
            x, y = round(x * 20) / 20, round(y * 20) / 20
            if not free(x, y, VIA_D / 2, gnd.GetNetCode()):
                continue
            # el tramo no debe cruzar cobre ajeno
            ok = True
            for i in range(1, 8):
                qx, qy = cx + (x - cx) * i / 8, cy + (y - cy) * i / 8
                if not free(qx, qy, 0.15, gnd.GetNetCode(), ignore=p):
                    ok = False
                    break
            if not ok:
                continue
            add_track(cx, cy, x, y, layer); add_via(x, y); n_via += 1; done = True
            break
        if done:
            break
    if not done:
        print("sin via:", p.GetParentFootprint().GetReference(), p.GetNumber())
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
pcbnew.SaveBoard(PCB, b)
print("vias de cosido GND:", n_via)
