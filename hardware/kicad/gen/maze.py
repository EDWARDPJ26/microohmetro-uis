"""Router de laberinto (A*) para completar conexiones pendientes que Freerouting dejo sin rutear.
Grilla de 0,1 mm; capas F.Cu / In2.Cu / B.Cu; vias pasantes; respeta holguras con el cobre ajeno."""
import heapq
import math
import os
import re
import subprocess
import pcbnew

PROJ = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PCB = os.path.join(PROJ, "microohmetro_v2.kicad_pcb")
KC = r"C:\Program Files\KiCad\10.0\bin\kicad-cli.exe"
MM, TO = pcbnew.FromMM, pcbnew.ToMM
G = 0.05
CLR = 0.16
LAYERS = [pcbnew.F_Cu, pcbnew.In2_Cu, pcbnew.B_Cu]
VIA_D, VIA_H = 0.6, 0.3


def drc_pairs():
    rpt = os.path.join(PROJ, "drc_maze.rpt")
    subprocess.run([KC, "pcb", "drc", PCB, "-o", rpt, "--severity-all"], capture_output=True)
    txt = open(rpt, encoding="utf-8").read()
    pairs = []
    for blk in re.split(r"\n(?=\[)", txt):
        if not blk.startswith("[unconnected_items]"):
            continue
        items = re.findall(r"@\(([\d.]+) mm, ([\d.]+) mm\): (.*)", blk)
        if len(items) == 2:
            net = re.search(r"\[([^\]]+)\]", items[0][2]).group(1)
            if net != "GND":
                pairs.append((net, items))
    return pairs


def build(b, net_code, w):
    ex = b.GetBoardEdgesBoundingBox()
    X0, Y0 = TO(ex.GetLeft()), TO(ex.GetTop())
    NX, NY = int(TO(ex.GetWidth()) / G) + 1, int(TO(ex.GetHeight()) / G) + 1
    grid = [bytearray(NX * NY) for _ in LAYERS]
    infl = CLR + w / 2

    def mark_rect(li, x1, y1, x2, y2, pad):
        ix1, iy1 = max(0, int((x1 - pad - X0) / G)), max(0, int((y1 - pad - Y0) / G))
        ix2, iy2 = min(NX - 1, int((x2 + pad - X0) / G) + 1), min(NY - 1, int((y2 + pad - Y0) / G) + 1)
        layers = range(len(LAYERS)) if li is None else [li]
        span = ix2 - ix1 + 1
        if span <= 0:
            return
        ones = b'' * span
        for L in layers:
            g = grid[L]
            for iy in range(iy1, iy2 + 1):
                g[iy * NX + ix1: iy * NX + ix1 + span] = ones

    def mark_seg(li, x1, y1, x2, y2, r):
        n = max(1, int(math.hypot(x2 - x1, y2 - y1) / 0.1))
        for i in range(n + 1):
            x, y = x1 + (x2 - x1) * i / n, y1 + (y2 - y1) * i / n
            mark_rect(li, x, y, x, y, r)

    # borde (0,5 mm)
    eb = int(0.5 / G)
    for L in range(len(LAYERS)):
        g = grid[L]
        for iy in range(NY):
            g[iy * NX: iy * NX + eb] = b'' * eb
            g[iy * NX + NX - eb: iy * NX + NX] = b'' * eb
        g[0: NX * eb] = b'' * (NX * eb)
        g[NX * (NY - eb):] = b'' * (NX * eb)
    for z in b.Zones():
        if z.GetIsRuleArea():
            bb = z.GetBoundingBox()
            mark_rect(None, TO(bb.GetLeft()), TO(bb.GetTop()), TO(bb.GetRight()), TO(bb.GetBottom()), w / 2)
    for p in b.GetPads():
        bb = p.GetBoundingBox()
        if p.GetNetCode() == net_code and p.GetNetCode() > 0:
            continue
        holes = p.GetAttribute() in (pcbnew.PAD_ATTRIB_PTH, pcbnew.PAD_ATTRIB_NPTH)
        for i, L in enumerate(LAYERS):
            if holes or p.IsOnLayer(L):
                mark_rect(i, TO(bb.GetLeft()), TO(bb.GetTop()), TO(bb.GetRight()), TO(bb.GetBottom()), infl)
    for t in b.GetTracks():
        if t.GetNetCode() == net_code:
            continue
        if t.GetClass() == "PCB_VIA":
            x, y, r = TO(t.GetPosition().x), TO(t.GetPosition().y), TO(t.GetWidth(pcbnew.F_Cu)) / 2
            mark_rect(None, x - r, y - r, x + r, y + r, infl)
        else:
            if t.GetLayer() not in LAYERS:
                continue
            li = LAYERS.index(t.GetLayer())
            mark_seg(li, TO(t.GetStart().x), TO(t.GetStart().y), TO(t.GetEnd().x), TO(t.GetEnd().y), TO(t.GetWidth()) / 2 + infl)
    return grid, X0, Y0, NX, NY


def item_cells(b, x, y, desc, NX, NY, X0, Y0, net=None):
    """celdas objetivo/origen (capa, ix, iy) de un pad o pista dado su punto del informe."""
    cells = set()
    for p in b.GetPads():
        if abs(TO(p.GetPosition().x) - x) < 0.01 and abs(TO(p.GetPosition().y) - y) < 0.01:
            bb = p.GetBoundingBox()
            for i, L in enumerate(LAYERS):
                if p.IsOnLayer(L) or p.GetAttribute() == pcbnew.PAD_ATTRIB_PTH:
                    for iy in range(int((TO(bb.GetTop()) - Y0) / G) + 1, int((TO(bb.GetBottom()) - Y0) / G)):
                        for ix in range(int((TO(bb.GetLeft()) - X0) / G) + 1, int((TO(bb.GetRight()) - X0) / G)):
                            cells.add((i, ix, iy))
            return cells, p
    best = None
    for t in b.GetTracks():
        if t.GetClass() == "PCB_TRACK" and "Track" in desc and t.GetNetname() == net:
            sx, sy, ex_, ey = TO(t.GetStart().x), TO(t.GetStart().y), TO(t.GetEnd().x), TO(t.GetEnd().y)
            if (abs(sx - x) < 0.02 and abs(sy - y) < 0.02) or (abs(ex_ - x) < 0.02 and abs(ey - y) < 0.02) or True:
                L2 = (ex_ - sx) ** 2 + (ey - sy) ** 2
                u = 0 if L2 == 0 else max(0, min(1, ((x - sx) * (ex_ - sx) + (y - sy) * (ey - sy)) / L2))
                d = math.hypot(x - (sx + u * (ex_ - sx)), y - (sy + u * (ey - sy)))
                if best is None or d < best[0]:
                    best = (d, t)
    if best:
        t = best[1]
        li = LAYERS.index(t.GetLayer()) if t.GetLayer() in LAYERS else 0
        sx, sy, ex_, ey = TO(t.GetStart().x), TO(t.GetStart().y), TO(t.GetEnd().x), TO(t.GetEnd().y)
        n = max(1, int(math.hypot(ex_ - sx, ey - sy) / G))
        for i in range(n + 1):
            cells.add((li, int(round((sx + (ex_ - sx) * i / n - X0) / G)), int(round((sy + (ey - sy) * i / n - Y0) / G))))
        return cells, t
    return cells, None


def astar(grid, NX, NY, src, dst, via_cells_ok):
    dst_set = set(dst)
    tx = sum(c[1] for c in dst) / len(dst)
    ty = sum(c[2] for c in dst) / len(dst)
    h = lambda ix, iy: math.hypot(ix - tx, iy - ty)  # noqa: E731
    openq, came, gs = [], {}, {}
    for c in src:
        gs[c] = 0
        heapq.heappush(openq, (h(c[1], c[2]), 0, c))
    allc = list(src) + list(dst)
    bx0 = max(0, min(c[1] for c in allc) - 200); bx1 = min(NX, max(c[1] for c in allc) + 200)
    by0 = max(0, min(c[2] for c in allc) - 200); by1 = min(NY, max(c[2] for c in allc) + 200)
    dirs = [(1, 0, 1), (-1, 0, 1), (0, 1, 1), (0, -1, 1), (1, 1, 1.414), (1, -1, 1.414), (-1, 1, 1.414), (-1, -1, 1.414)]
    n = 0
    while openq:
        f, gcur, c = heapq.heappop(openq)
        if c in dst_set:
            path = [c]
            while c in came:
                c = came[c]
                path.append(c)
            return path[::-1]
        n += 1
        if n > 3_000_000:
            return None
        L, ix, iy = c
        for dx, dy, cost in dirs:
            nx, ny = ix + dx, iy + dy
            if not (bx0 <= nx < bx1 and by0 <= ny < by1):
                continue
            nc = (L, nx, ny)
            if grid[L][ny * NX + nx] and nc not in dst_set:
                continue
            ng = gcur + cost
            if ng < gs.get(nc, 1e18):
                gs[nc] = ng; came[nc] = c
                heapq.heappush(openq, (ng + h(nx, ny), ng, nc))
        for L2 in range(len(LAYERS)):
            if L2 != L and via_cells_ok(ix, iy):
                nc = (L2, ix, iy)
                ng = gcur + 60
                if ng < gs.get(nc, 1e18):
                    gs[nc] = ng; came[nc] = c
                    heapq.heappush(openq, (ng + h(ix, iy), ng, nc))
    return None


def commit(b, net, path, w, X0, Y0):
    pts = [(p[0], X0 + p[1] * G, Y0 + p[2] * G) for p in path]
    segs, vias = [], []
    start = pts[0]
    prev = pts[0]
    pdir = None
    for cur in pts[1:]:
        if cur[0] != prev[0]:
            if (prev[1], prev[2]) != (start[1], start[2]):
                segs.append((prev[0], start[1], start[2], prev[1], prev[2]))
            vias.append((prev[1], prev[2]))
            start, pdir = cur, None
        else:
            d = (round((cur[1] - prev[1]) / G), round((cur[2] - prev[2]) / G))
            if pdir is not None and d != pdir:
                segs.append((prev[0], start[1], start[2], prev[1], prev[2]))
                start = prev
            pdir = d
        prev = cur
    if (prev[1], prev[2]) != (start[1], start[2]):
        segs.append((prev[0], start[1], start[2], prev[1], prev[2]))
    ni = b.FindNet(net)
    for L, x1, y1, x2, y2 in segs:
        t = pcbnew.PCB_TRACK(b)
        t.SetStart(pcbnew.VECTOR2I(MM(x1), MM(y1))); t.SetEnd(pcbnew.VECTOR2I(MM(x2), MM(y2)))
        t.SetWidth(MM(w)); t.SetLayer(LAYERS[L]); t.SetNet(ni)
        b.Add(t)
    for x, y in vias:
        v = pcbnew.PCB_VIA(b)
        v.SetPosition(pcbnew.VECTOR2I(MM(x), MM(y))); v.SetWidth(MM(VIA_D)); v.SetDrill(MM(VIA_H)); v.SetNet(ni)
        b.Add(v)
    return len(segs), len(vias)


WIDTH = {"PMID": [0.5, 0.3, 0.2], "VBUS_C": [0.3, 0.2], "VBUS_IN": [0.5, 0.3, 0.2], "Net-(J201-Pin_1)": [1.0, 0.6, 0.4]}
for it in range(3):
    pairs = drc_pairs()
    print(f"iteracion {it}: {len(pairs)} conexiones pendientes (sin GND)")
    if not pairs:
        break
    b = pcbnew.LoadBoard(PCB)
    for net, items in pairs:
        nc = b.FindNet(net).GetNetCode()
        done = False
        for w in WIDTH.get(net, [0.3, 0.25, 0.2]):
            grid, X0, Y0, NX, NY = build(b, nc, w)
            vr = int((VIA_D / 2 + CLR) / G) + 1

            def via_ok(ix, iy, grid=grid, NX=NX, NY=NY, vr=vr):
                for L in range(len(LAYERS)):
                    for dy in (-vr, 0, vr):
                        for dx in (-vr, 0, vr):
                            x, y = ix + dx, iy + dy
                            if not (0 <= x < NX and 0 <= y < NY) or grid[L][y * NX + x]:
                                return False
                return True
            (x1, y1, d1), (x2, y2, d2) = [(float(a), float(bb_), c) for a, bb_, c in items]
            src, _ = item_cells(b, x1, y1, d1, NX, NY, X0, Y0, net)
            dst, _ = item_cells(b, x2, y2, d2, NX, NY, X0, Y0, net)
            if not src or not dst:
                print("  sin celdas para", net)
                break
            path = astar(grid, NX, NY, list(src), list(dst), via_ok)
            if path:
                s, v = commit(b, net, path, w, X0, Y0)
                print(f"  {net}: ruteada con w={w} mm ({s} tramos, {v} vias)")
                done = True
                break
        if not done:
            print(f"  {net}: NO se pudo rutear")
    pcbnew.SaveBoard(PCB, b)
