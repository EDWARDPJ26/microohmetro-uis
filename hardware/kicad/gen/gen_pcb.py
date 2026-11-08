"""Genera el PCB v2 (4 capas) desde la netlist de KiCad: footprints, redes, ubicacion por zonas,
contorno, reglas, zonas de cobre, keepout de antena y silueta de bateria."""
import os
import sys
import math
import pcbnew

sys.path.insert(0, os.path.dirname(__file__))
from sexp import parse, find, first  # noqa: E402

PROJ = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
FPDIR = r"C:\Program Files\KiCad\10.0\share\kicad\footprints"
NET = os.path.join(PROJ, "microohmetro_v2.net")
OUT = os.path.join(PROJ, "microohmetro_v2.kicad_pcb")
W, H = 64.0, 116.0
OX, OY = 100.0, 50.0           # origen de la placa en la hoja
MM = pcbnew.FromMM


def P(x, y):
    return pcbnew.VECTOR2I(MM(OX + x), MM(OY + y))


# ------------------------------------------------------------------ netlist
t = parse(open(NET, encoding="utf-8").read())[0]
comps = {}
for c in find(first(t, "components"), "comp"):
    ref = first(c, "ref")[1]
    comps[ref] = dict(value=first(c, "value")[1], fp=first(c, "footprint")[1] if first(c, "footprint") else "")
padnet = {}
for n in find(first(t, "nets"), "net"):
    name = first(n, "name")[1].split("/")[-1]
    for nd in find(n, "node"):
        padnet[(first(nd, "ref")[1], first(nd, "pin")[1])] = name

board = pcbnew.BOARD()
board.SetCopperLayerCount(4)
ds = board.GetDesignSettings()
ds.SetCopperLayerCount(4)
nets = {}
for name in sorted(set(padnet.values())):
    ni = pcbnew.NETINFO_ITEM(board, name)
    board.Add(ni)
    nets[name] = ni

# ------------------------------------------------------------------ ubicacion fija (x, y, rot, capa)
#  Zona superior (y 0-36): bornes, fuente, Kelvin, ADC  |  zona bateria (y 38-98)  |  franja inferior (98-110)
FIX = {
    # bornes banana (I+, S+, S-, I-)
    "J501": (13.5, 8, 0, "F"), "J502": (25.2, 8, 0, "F"), "J503": (36.9, 8, 0, "F"), "J504": (48.6, 8, 0, "F"),
    # fuente de corriente (izquierda)
    "Q403": (8.0, 21, 90, "F"), "U402": (8.0, 30.5, 0, "F"), "U401": (16.0, 32, 0, "F"),
    "Q401": (21.0, 27.5, 0, "F"), "Q402": (16.0, 26.5, 0, "F"),
    # ADC (centro)
    "U601": (31.0, 26, 0, "F"), "D601": (24.0, 17.5, 0, "F"), "D602": (36.0, 17.5, 0, "F"),
    # Kelvin / shunt (derecha)
    "R501": (52.0, 19, 90, "F"), "R502": (58.5, 22, 90, "F"), "U501": (45.0, 24, 0, "F"),
    # entrada USB / PD (izquierda, zona bateria)
    "J101": (6.0, 54, 270, "F"), "U101": (17.0, 53, 0, "F"), "Q101": (11.0, 64, 0, "F"),
    "D101": (6.5, 69, 90, "F"), "U102": (16.0, 63, 0, "F"),
    # cargador
    "U201": (24.0, 76, 0, "F"), "L201": (31.0, 76, 0, "F"),
    # regulacion
    "U301": (14.0, 88, 0, "F"), "FB301": (20.0, 92, 0, "F"),
    # MCU (antena hacia el borde derecho)
    "U701": (46.0, 68, 270, "F"), "SW701": (38.0, 94, 0, "F"), "SW702": (46.0, 94, 0, "F"),
    # bateria y polaridad (franja inferior)
    "J201": (32.0, 109.5, 180, "F"), "Q201": (20.0, 107, 0, "F"), "Q202": (20.0, 112, 0, "F"),
    "TH201": (32.0, 76, 0, "B"),
    # mecanicos
    "H801": (3.8, 3.8, 0, "F"), "H802": (60.2, 3.8, 0, "F"), "H803": (3.8, 112.2, 0, "F"), "H804": (60.2, 112.2, 0, "F"),
    "TP801": (55.0, 94, 0, "F"), "TP802": (59.0, 94, 0, "F"), "TP803": (55.0, 98, 0, "F"),
    "TP804": (59.0, 98, 0, "F"), "TP805": (55.0, 102, 0, "F"), "TP806": (59.0, 102, 0, "F"),
}
# zona permitida para los pasivos auto-ubicados segun su hoja (primer digito de la referencia)
ZONE = {"1": (1, 44, 30, 72), "2": (18, 68, 40, 104), "3": (8, 82, 30, 102), "4": (1, 14, 22, 43),
        "5": (42, 14, 63, 43), "6": (18, 14, 44, 43), "7": (28, 82, 54, 104), "8": (50, 90, 63, 104)}
MODEL3D_FIX = {  # modelos 3D faltantes en la libreria -> aproximacion
    "Resistor_SMD:R_Shunt_Vishay_WSK2512_6332Metric_T1.19mm": "${KICAD10_3DMODEL_DIR}/Resistor_SMD.3dshapes/R_2512_6332Metric.step",
    "Connector_JST:JST_XH_S3B-XH-SM4-TB_1x03-1MP_P2.50mm_Horizontal":
        "${KICAD10_3DMODEL_DIR}/Connector_JST.3dshapes/JST_XH_S3B-XH-A_1x03_P2.50mm_Horizontal.step",
    "Connector:Banana_Jack_1Pin": "${KICAD10_3DMODEL_DIR}/Connector.3dshapes/Banana_Cliff_FCR7350R_S16N-PC_Horizontal.step",
}

fps = {}
for ref, c in comps.items():
    lib, name = c["fp"].split(":")
    m = pcbnew.FootprintLoad(os.path.join(FPDIR, lib + ".pretty"), name)
    m.SetReference(ref)
    m.SetValue(c["value"])
    m.SetFPID(pcbnew.LIB_ID(lib, name))
    for pad in m.Pads():
        n = padnet.get((ref, pad.GetNumber()))
        if n:
            pad.SetNet(nets[n])
    if c["fp"] in MODEL3D_FIX:
        for mod in m.Models():
            mod.m_Filename = MODEL3D_FIX[c["fp"]]
        if c["fp"] == "Connector:Banana_Jack_1Pin":
            for mod in m.Models():
                mod.m_Scale = pcbnew.VECTOR3D(0.6, 0.6, 0.6)
                mod.m_Rotation = pcbnew.VECTOR3D(-90, 0, 0)
    board.Add(m)
    fps[ref] = m


def place(m, x, y, rot, side):
    if side == "B" and not m.IsFlipped():
        m.Flip(m.GetPosition(), pcbnew.FLIP_DIRECTION_TOP_BOTTOM)
    m.SetOrientationDegrees(rot)
    m.SetPosition(P(x, y))


for ref, (x, y, r, side) in FIX.items():
    place(fps[ref], x, y, r, side)


def cbox(m, margin=0.25):
    lay = pcbnew.B_CrtYd if m.IsFlipped() else pcbnew.F_CrtYd
    sh = m.GetCourtyard(lay)
    bb = sh.BBox() if sh.OutlineCount() else m.GetBoundingBox(False)
    return (pcbnew.ToMM(bb.GetLeft()) - OX - margin, pcbnew.ToMM(bb.GetTop()) - OY - margin,
            pcbnew.ToMM(bb.GetRight()) - OX + margin, pcbnew.ToMM(bb.GetBottom()) - OY + margin)


def overlap(a, b):
    return not (a[2] <= b[0] or b[2] <= a[0] or a[3] <= b[1] or b[3] <= a[1])


placed = [cbox(fps[r]) for r in FIX]
side_of = {r: FIX[r][3] for r in FIX}
# pasivos: cerca del centroide de los pads con los que comparten red
anchors_pad = {}
for ref in FIX:
    for pad in fps[ref].Pads():
        if pad.GetNetname():
            p = pad.GetPosition()
            anchors_pad.setdefault(pad.GetNetname(), []).append((pcbnew.ToMM(p.x) - OX, pcbnew.ToMM(p.y) - OY))
POWERNETS = {"GND", "+3V3"}
order = sorted([r for r in fps if r not in FIX], key=lambda r: r)
for ref in order:
    m = fps[ref]
    sig = [pad.GetNetname() for pad in m.Pads() if pad.GetNetname() and pad.GetNetname() not in POWERNETS]
    pts = [p for n in sig for p in anchors_pad.get(n, [])]
    z = ZONE[ref.lstrip("RCDLQUJSWTHFB")[0]] if ref.lstrip("RCDLQUJSWTHFB") else (1, 1, 63, 109)
    if pts:
        tx = sum(p[0] for p in pts) / len(pts)
        ty = sum(p[1] for p in pts) / len(pts)
    else:
        tx, ty = (z[0] + z[2]) / 2, (z[1] + z[3]) / 2
    tx, ty = min(max(tx, z[0] + 2), z[2] - 2), min(max(ty, z[1] + 2), z[3] - 2)
    best = None
    for rot in (0, 90):
        for rad in [i * 0.5 for i in range(0, 60)]:
            found = None
            steps = max(1, int(2 * math.pi * rad / 0.5)) if rad else 1
            for k in range(steps):
                a = 2 * math.pi * k / steps
                x, y = round((tx + rad * math.cos(a)) * 4) / 4, round((ty + rad * math.sin(a)) * 4) / 4
                place(m, x, y, rot, "F")
                b = cbox(m)
                if b[0] < z[0] or b[1] < z[1] or b[2] > z[2] or b[3] > z[3]:
                    continue
                if any(overlap(b, o) for o in placed):
                    continue
                found = (rad, x, y, rot)
                break
            if found:
                if best is None or found[0] < best[0]:
                    best = found
                break
    if best is None:
        raise SystemExit(f"No cabe {ref} en su zona {z}")
    _, x, y, rot = best
    place(m, x, y, rot, "F")
    placed.append(cbox(m))
    for pad in m.Pads():
        if pad.GetNetname():
            p = pad.GetPosition()
            anchors_pad.setdefault(pad.GetNetname(), []).append((pcbnew.ToMM(p.x) - OX, pcbnew.ToMM(p.y) - OY))

# ------------------------------------------------------------------ contorno (esquinas redondeadas r=3)
def seg(layer, a, b, w=0.1):
    s = pcbnew.PCB_SHAPE(board, pcbnew.SHAPE_T_SEGMENT)
    s.SetLayer(layer); s.SetStart(P(*a)); s.SetEnd(P(*b)); s.SetWidth(MM(w)); board.Add(s)


def arc(layer, c, start, mid, end, w=0.1):
    s = pcbnew.PCB_SHAPE(board, pcbnew.SHAPE_T_ARC)
    s.SetLayer(layer); s.SetArcGeometry(P(*start), P(*mid), P(*end)); s.SetWidth(MM(w)); board.Add(s)


r = 3.0
k = r * (1 - math.cos(math.radians(45)))
seg(pcbnew.Edge_Cuts, (r, 0), (W - r, 0)); seg(pcbnew.Edge_Cuts, (W, r), (W, H - r))
seg(pcbnew.Edge_Cuts, (W - r, H), (r, H)); seg(pcbnew.Edge_Cuts, (0, H - r), (0, r))
arc(pcbnew.Edge_Cuts, None, (W - r, 0), (W - k, k), (W, r)); arc(pcbnew.Edge_Cuts, None, (W, H - r), (W - k, H - k), (W - r, H))
arc(pcbnew.Edge_Cuts, None, (r, H), (k, H - k), (0, H - r)); arc(pcbnew.Edge_Cuts, None, (0, r), (k, k), (r, 0))

# ------------------------------------------------------------------ silueta de bateria (cara inferior)
BX0, BY0, BX1, BY1 = 7.0, 44.0, 57.0, 104.0
for a, b in [((BX0, BY0), (BX1, BY0)), ((BX1, BY0), (BX1, BY1)), ((BX1, BY1), (BX0, BY1)), ((BX0, BY1), (BX0, BY0))]:
    seg(pcbnew.B_SilkS, a, b, 0.15)
    seg(pcbnew.B_Fab, a, b, 0.1)


def text(s, x, y, layer, size=1.2, mirror=False):
    tx = pcbnew.PCB_TEXT(board)
    tx.SetText(s); tx.SetPosition(P(x, y)); tx.SetLayer(layer)
    tx.SetTextSize(pcbnew.VECTOR2I(MM(size), MM(size))); tx.SetTextThickness(MM(size * 0.15))
    if mirror:
        tx.SetMirrored(True)
    board.Add(tx)


text("LiPo 1S 2000 mAh (8 x 50 x 60 mm) - cinta doble faz", 32, 72, pcbnew.B_SilkS, 1.5, True)
text("Zona sin componentes en cara inferior", 32, 75, pcbnew.B_SilkS, 1.2, True)
text("I+", 13.5, 15.2, pcbnew.F_SilkS, 1.6); text("S+", 25.2, 15.2, pcbnew.F_SilkS, 1.6)
text("S-", 36.9, 15.2, pcbnew.F_SilkS, 1.6); text("I-", 48.6, 15.2, pcbnew.F_SilkS, 1.6)
text("MICRO-OHMIMETRO v2  UIS 2026", 32, 42.6, pcbnew.F_SilkS, 1.2)

# ------------------------------------------------------------------ reglas y clases de red
ds.m_TrackMinWidth = MM(0.15)
ds.m_MinThroughDrill = MM(0.2)
ds.m_ViasMinSize = MM(0.45)
ds.m_ViasMinAnnularWidth = MM(0.1)
ds.m_MinClearance = MM(0.15)
ds.m_HoleClearance = MM(0.2)
ds.m_CopperEdgeClearance = MM(0.2)
ns = ds.m_NetSettings
dflt = ns.GetDefaultNetclass()
dflt.SetTrackWidth(MM(0.2)); dflt.SetClearance(MM(0.15)); dflt.SetViaDiameter(MM(0.6)); dflt.SetViaDrill(MM(0.3))
CLASSES = {
    "GND_PLANO": (0.4, 0.15, ["GND"]),
    "POT_ALTA": (1.0, 0.15, ["I_PLUS", "I_MINUS", "NLIFT", "SYS", "VBAT_CHG", "BATT_RAW", "SW", "PMID", "VBUS_IN", "VBUS_C"]),
    "POT": (0.4, 0.15, ["+3V3", "AVDD", "REGN", "VREG_1V2", "VREG_2V7"]),
    "KELVIN": (0.2, 0.15, ["S_PLUS", "S_MINUS", "RS_SP", "RS_SN", "AIN0", "AIN1", "AIN2", "AIN3"]),
}
for cname, (tw, cl, members) in CLASSES.items():
    ncl = pcbnew.NETCLASS(cname)
    ncl.SetTrackWidth(MM(tw)); ncl.SetClearance(MM(cl)); ncl.SetViaDiameter(MM(0.8 if tw >= 1 else 0.6))
    ncl.SetViaDrill(MM(0.4 if tw >= 1 else 0.3))
    ns.SetNetclass(cname, ncl)
    for mbr in members:
        ns.SetNetclassPatternAssignment(mbr, cname)

# ------------------------------------------------------------------ zonas de cobre GND (In1 completo, In2, F/B relleno)
def zone(layer, net, prio=0, pts=None, keepout=False):
    z = pcbnew.ZONE(board)
    z.SetLayer(layer)
    if keepout:
        z.SetIsRuleArea(True); z.SetDoNotAllowTracks(True); z.SetDoNotAllowVias(True); z.SetDoNotAllowZoneFills(True)
        z.SetDoNotAllowPads(False); z.SetDoNotAllowFootprints(False)
        z.SetLayerSet(pcbnew.LSET.AllCuMask())
    else:
        z.SetNet(nets[net]); z.SetAssignedPriority(prio)
        z.SetMinThickness(MM(0.2)); z.SetLocalClearance(MM(0.2))
        z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)
        z.SetThermalReliefGap(MM(0.3)); z.SetThermalReliefSpokeWidth(MM(0.4))
    o = z.Outline()
    o.NewOutline()
    for x, y in (pts or [(0.3, 0.3), (W - 0.3, 0.3), (W - 0.3, H - 0.3), (0.3, H - 0.3)]):
        o.Append(MM(OX + x), MM(OY + y))
    board.Add(z)
    return z


zone(pcbnew.In1_Cu, "GND")
zone(pcbnew.In2_Cu, "GND")
zone(pcbnew.B_Cu, "GND")
zone(pcbnew.F_Cu, "GND")
# keepout de antena del ESP32-C3 (borde derecho, todas las capas de cobre)
u = fps["U701"]
ant_x0 = W - 8.3
zone(pcbnew.F_Cu, None, pts=[(ant_x0, 53.0), (W, 53.0), (W, 83.0), (ant_x0, 83.0)], keepout=True)

board.SetFileName(OUT)
pcbnew.SaveBoard(OUT, board)
print("OK", OUT, "footprints:", len(fps), "redes:", len(nets))
xs = [cbox(fps[r]) for r in fps]
print("extension componentes x %.1f..%.1f  y %.1f..%.1f" % (min(b[0] for b in xs), max(b[2] for b in xs), min(b[1] for b in xs), max(b[3] for b in xs)))
