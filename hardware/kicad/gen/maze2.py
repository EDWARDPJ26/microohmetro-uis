"""Une islas de una misma red (A*), partiendo de TODO el cobre de la isla origen."""
import math, os, sys
sys.path.insert(0, os.path.dirname(__file__))
src_code = open(os.path.join(os.path.dirname(__file__), "maze.py"), encoding="utf-8").read().split("WIDTH = {")[0]
exec(src_code)


def islands(b, net):
    items = []
    for p in b.GetPads():
        if p.GetNetname() == net:
            bb = p.GetBoundingBox()
            items.append(("pad", p, (TO(bb.GetLeft()), TO(bb.GetTop()), TO(bb.GetRight()), TO(bb.GetBottom())),
                          [i for i, L in enumerate(LAYERS) if p.IsOnLayer(L) or p.GetAttribute() == pcbnew.PAD_ATTRIB_PTH]))
    for t in b.GetTracks():
        if t.GetNetname() != net:
            continue
        if t.GetClass() == "PCB_VIA":
            x, y = TO(t.GetPosition().x), TO(t.GetPosition().y)
            items.append(("via", t, (x, y), list(range(len(LAYERS)))))
        elif t.GetLayer() in LAYERS:
            items.append(("trk", t, (TO(t.GetStart().x), TO(t.GetStart().y), TO(t.GetEnd().x), TO(t.GetEnd().y), TO(t.GetWidth()) / 2),
                          [LAYERS.index(t.GetLayer())]))
    par = list(range(len(items)))

    def f(i):
        while par[i] != i:
            par[i] = par[par[i]]; i = par[i]
        return i

    def pts(it):
        if it[0] == "pad":
            g = it[2]; return [((g[0] + g[2]) / 2, (g[1] + g[3]) / 2)]
        if it[0] == "via":
            return [it[2]]
        return [(it[2][0], it[2][1]), (it[2][2], it[2][3])]

    def touches(a, b_):
        if not set(a[3]) & set(b_[3]):
            return False
        for (x, y) in pts(a):
            if b_[0] == "pad":
                g = b_[2]
                if g[0] - 0.05 <= x <= g[2] + 0.05 and g[1] - 0.05 <= y <= g[3] + 0.05:
                    return True
            elif b_[0] == "via":
                if math.hypot(x - b_[2][0], y - b_[2][1]) < 0.3:
                    return True
            else:
                g = b_[2]
                dx, dy = g[2] - g[0], g[3] - g[1]
                L = dx * dx + dy * dy
                u = 0 if L == 0 else max(0, min(1, ((x - g[0]) * dx + (y - g[1]) * dy) / L))
                if math.hypot(x - (g[0] + u * dx), y - (g[1] + u * dy)) <= g[4] + 0.01:
                    return True
        return False
    for i in range(len(items)):
        for j in range(i + 1, len(items)):
            if touches(items[i], items[j]) or touches(items[j], items[i]):
                par[f(i)] = f(j)
    groups = {}
    for i, it in enumerate(items):
        groups.setdefault(f(i), []).append(it)
    return list(groups.values())


def cells_of(group, X0, Y0, NX, NY):
    cs = set()
    for kind, obj, g, lays in group:
        if kind == "pad":
            for L in lays:
                for iy in range(int((g[1] - Y0) / G) + 1, int((g[3] - Y0) / G)):
                    for ix in range(int((g[0] - X0) / G) + 1, int((g[2] - X0) / G)):
                        cs.add((L, ix, iy))
        elif kind == "via":
            for L in lays:
                cs.add((L, int(round((g[0] - X0) / G)), int(round((g[1] - Y0) / G))))
        else:
            n = max(1, int(math.hypot(g[2] - g[0], g[3] - g[1]) / G))
            for i in range(n + 1):
                cs.add((lays[0], int(round((g[0] + (g[2] - g[0]) * i / n - X0) / G)), int(round((g[1] + (g[3] - g[1]) * i / n - Y0) / G))))
    return cs


WIDTHS = {"PMID": [0.5, 0.3, 0.2], "SYS": [0.6, 0.4, 0.25], "VBUS_C": [0.3, 0.2]}
for it in range(3):
    pairs = drc_pairs()
    nets_pend = sorted(set(n for n, _ in pairs))
    print(f"iteracion {it}: pendientes {len(pairs)} -> {nets_pend}")
    if not pairs:
        break
    b = pcbnew.LoadBoard(PCB)
    for net in nets_pend:
        nc = b.FindNet(net).GetNetCode()
        for w in WIDTHS.get(net, [0.25, 0.2]):
            grid, X0, Y0, NX, NY = build(b, nc, w)
            grs = islands(b, net)
            if len(grs) < 2:
                break
            grs.sort(key=len, reverse=True)
            src = cells_of(grs[0], X0, Y0, NX, NY)
            dst = set()
            for g_ in grs[1:2]:
                dst |= cells_of(g_, X0, Y0, NX, NY)
            vr = int((VIA_D / 2 + CLR) / G) + 1

            def via_ok(ix, iy, grid=grid, NX=NX, NY=NY, vr=vr):
                for L in range(len(LAYERS)):
                    for dy in (-vr, 0, vr):
                        for dx in (-vr, 0, vr):
                            x, y = ix + dx, iy + dy
                            if not (0 <= x < NX and 0 <= y < NY) or grid[L][y * NX + x]:
                                return False
                return True
            path = astar(grid, NX, NY, list(src), list(dst), via_ok)
            if path:
                s, v = commit(b, net, path, w, X0, Y0)
                print(f"  {net}: isla unida con w={w} ({s} tramos, {v} vias)")
                break
        else:
            print(f"  {net}: sin camino")
    pcbnew.SaveBoard(PCB, b)
