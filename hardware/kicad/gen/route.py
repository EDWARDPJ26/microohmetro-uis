"""Exporta DSN, ejecuta Freerouting en modo consola e importa la sesion."""
import os, re, subprocess, sys, pcbnew
PROJ = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PCB = os.path.join(PROJ, "microohmetro_v2.kicad_pcb")
DSN = os.path.join(PROJ, "route", "microohmetro_v2.dsn")
SES = os.path.join(PROJ, "route", "pasada3.ses")
os.makedirs(os.path.dirname(DSN), exist_ok=True)
b = pcbnew.LoadBoard(PCB)
assert pcbnew.ExportSpecctraDSN(b, DSN)
d = open(DSN, encoding="utf-8").read()
d = re.sub(r"\(layer In1\.Cu\s*\(type signal\)", "(layer In1.Cu (type power)", d)
d = re.sub(r"\(net GND\s*\(pins[^)]*\)\s*\)", "", d)
open(DSN, "w", encoding="utf-8").write(d)
passes = sys.argv[1] if len(sys.argv) > 1 else "40"
cmd = ["java", "-jar", r"C:\Users\edwar\AppData\Local\freerouting\app\freerouting-executable.jar",
       "-de", DSN, "-do", SES, "-mp", passes, "--gui.enabled=false"]
print(" ".join(cmd)); sys.stdout.flush()
r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
print("\n".join(l for l in r.stdout.splitlines() if re.search(r"pass|unrouted|completed|score|ERROR|incomplete", l, re.I))[-3000:])
print("ses existe:", os.path.exists(SES))
if os.path.exists(SES):
    b = pcbnew.LoadBoard(PCB)
    ok = pcbnew.ImportSpecctraSES(b, SES)
    print("import:", ok)
    filler = pcbnew.ZONE_FILLER(b)
    filler.Fill(b.Zones())
    pcbnew.SaveBoard(PCB, b)
    print("pistas:", len([t for t in b.GetTracks() if t.GetClass() == "PCB_TRACK"]), "vias:", len([t for t in b.GetTracks() if t.GetClass() == "PCB_VIA"]))
