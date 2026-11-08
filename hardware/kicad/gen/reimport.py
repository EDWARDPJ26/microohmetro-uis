import os, pcbnew
PROJ = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PCB = os.path.join(PROJ, "microohmetro_v2.kicad_pcb")
b = pcbnew.LoadBoard(PCB)
print("import SES:", pcbnew.ImportSpecctraSES(b, os.path.join(PROJ, "route", "pasada1.ses")))
pcbnew.SaveBoard(PCB, b)
