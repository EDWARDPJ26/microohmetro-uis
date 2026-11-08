import sys
sys.path.insert(0, ".")
from libsym import get_symbol, pins
for spec in sys.argv[1:]:
    lib, s = spec.split(":")
    sym = get_symbol(lib, s)
    ps = sorted(pins(sym), key=lambda p: (p[5], p[0].zfill(4)))
    print(f"== {spec}: " + "  ".join(f"{p[0]}={p[1]}" + (f"[u{p[5]}]" if p[5] > 1 else "") for p in ps))
