import sys, os
sys.argv = ["x"]
src = open(os.path.join(os.path.dirname(__file__), "maze.py"), encoding="utf-8").read().split("WIDTH = {")[0]
exec(src)
pairs = drc_pairs()
b = pcbnew.LoadBoard(PCB)
for net, items in pairs:
    nc = b.FindNet(net).GetNetCode()
    grid, X0, Y0, NX, NY = build(b, nc, 0.2)
    (x1, y1, d1), (x2, y2, d2) = [(float(a), float(c), dd) for a, c, dd in items]
    s_, so = item_cells(b, x1, y1, d1, NX, NY, X0, Y0, net)
    t_, to = item_cells(b, x2, y2, d2, NX, NY, X0, Y0, net)
    # alcanzables desde el origen en la capa del origen
    from collections import deque
    seen = set(s_); q = deque(s_); n = 0
    while q and n < 200000:
        L, ix, iy = q.popleft(); n += 1
        for dx, dy in ((1,0),(-1,0),(0,1),(0,-1)):
            c = (L, ix+dx, iy+dy)
            if c in seen or not (0 <= c[1] < NX and 0 <= c[2] < NY) or grid[L][c[2]*NX+c[1]]:
                continue
            seen.add(c); q.append(c)
    blocked_dst = sum(1 for c in t_ if grid[c[0]][c[2]*NX+c[1]])
    print(f"{net}: src {len(s_)} celdas ({d1[:40]}) alcanzables {len(seen)} | dst {len(t_)} celdas, bloqueadas {blocked_dst} ({d2[:40]})")
print("---- distancias pad -> extremo de pista mas cercano de la misma red")
for net, items in pairs:
    (x1, y1, d1), (x2, y2, d2) = [(float(a), float(c), dd) for a, c, dd in items]
    for (x, y, d) in ((x1, y1, d1), (x2, y2, d2)):
        if d.startswith("Pad"):
            best = None
            for t in b.GetTracks():
                if t.GetNetname() == net and t.GetClass() == "PCB_TRACK":
                    for e in (t.GetStart(), t.GetEnd()):
                        dd = math.hypot(TO(e.x) - x, TO(e.y) - y)
                        if best is None or dd < best[0]:
                            best = (dd, TO(e.x), TO(e.y), t.GetLayerName())
            print(net, d[:30], "-> extremo a %.3f mm (%.2f,%.2f %s)" % best if best else "sin pistas")
