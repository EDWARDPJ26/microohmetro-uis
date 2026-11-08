"""Utilidades minimas para leer/escribir S-expressions de KiCad."""
import re

_tok = re.compile(r'\s*(?:(\()|(\))|("(?:[^"\\]|\\.)*")|([^\s()"]+))')


def parse(text):
    stack, cur = [], []
    pos = 0
    n = len(text)
    while pos < n:
        m = _tok.match(text, pos)
        if not m:
            break
        pos = m.end()
        if m.group(1):
            stack.append(cur)
            cur = []
        elif m.group(2):
            done = cur
            cur = stack.pop()
            cur.append(done)
        elif m.group(3) is not None:
            cur.append(Str(m.group(3)[1:-1].replace('\\"', '"')))
        elif m.group(4) is not None:
            cur.append(m.group(4))
    return cur


class Str(str):
    """Cadena entre comillas."""


def dump(e, ind=0):
    if isinstance(e, list):
        if not e:
            return "()"
        simple = all(not isinstance(x, list) for x in e)
        if simple:
            return "(" + " ".join(dump(x) for x in e) + ")"
        out = "(" + dump(e[0])
        for x in e[1:]:
            if isinstance(x, list):
                out += "\n" + "\t" * (ind + 1) + dump(x, ind + 1)
            else:
                out += " " + dump(x)
        return out + "\n" + "\t" * ind + ")"
    if isinstance(e, Str):
        return '"' + e.replace('"', '\\"') + '"'
    return str(e)


def find(e, key):
    return [x for x in e if isinstance(x, list) and x and x[0] == key]


def first(e, key):
    r = find(e, key)
    return r[0] if r else None
