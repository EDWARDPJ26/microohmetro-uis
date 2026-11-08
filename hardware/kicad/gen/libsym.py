"""Carga simbolos de las librerias oficiales de KiCad (resolviendo 'extends')."""
import copy
import os
from sexp import parse, find, first, Str

LIBDIR = r"C:\Program Files\KiCad\10.0\share\kicad\symbols"
_cache = {}


def _lib(name):
    if name not in _cache:
        path = name if os.path.isabs(name) else os.path.join(LIBDIR, name + ".kicad_sym")
        with open(path, encoding="utf-8") as f:
            _cache[name] = parse(f.read())[0]
    return _cache[name]


def get_symbol(libname, symname, libpath=None):
    lib = _lib(libpath or libname)
    syms = {s[1]: s for s in find(lib, "symbol")}
    s = copy.deepcopy(syms[symname])
    ext = first(s, "extends")
    if ext:
        parent = copy.deepcopy(syms[ext[1]])
        # propiedades del hijo sobreescriben las del padre
        child_props = {p[1]: p for p in find(s, "property")}
        newp = []
        for x in parent:
            if isinstance(x, list) and x and x[0] == "property" and x[1] in child_props:
                newp.append(child_props.pop(x[1]))
            elif isinstance(x, list) and x and x[0] == "symbol":
                x = copy.deepcopy(x)
                x[1] = Str(x[1].replace(ext[1], symname, 1))
                newp.append(x)
            else:
                newp.append(x)
        newp[1] = Str(symname)
        for p in child_props.values():
            newp.insert(2, p)
        s = newp
    full = copy.deepcopy(s)
    full[1] = Str(f"{libname}:{symname}")
    return full


def pins(sym):
    """Lista de (numero, nombre, x, y, angulo, unidad) de un simbolo completo."""
    out = []
    for sub in find(sym, "symbol"):
        parts = sub[1].split("_")
        unit = int(parts[-2]) if parts[-2].isdigit() else 0
        if parts[-1] == "2":
            continue  # estilo De Morgan alternativo
        for p in find(sub, "pin"):
            at = first(p, "at")
            num = first(p, "number")[1]
            nam = first(p, "name")[1]
            out.append((num, nam, float(at[1]), float(at[2]), float(at[3]) if len(at) > 3 else 0.0, unit, p[1]))
    return out
