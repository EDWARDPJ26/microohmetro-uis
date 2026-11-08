"""Genera la libreria propia microohm.kicad_sym: AD7124-4 (LFCSP-32, pinout del datasheet Rev. E)
y P-MOS en DPAK con numeracion 1=G, 2=D, 3=S."""
import os

OUT = os.path.join(os.path.dirname(__file__), "..", "Librerias", "microohm.kicad_sym")


def pin(etype, x, y, ang, name, num, length=2.54, hide=False):
    h = " (hide yes)" if hide else ""
    return (f'\t\t\t(pin {etype} line (at {x:.2f} {y:.2f} {ang}) (length {length}){h}\n'
            f'\t\t\t\t(name "{name}" (effects (font (size 1.27 1.27))))\n'
            f'\t\t\t\t(number "{num}" (effects (font (size 1.27 1.27)))))\n')


def prop(k, v, x, y, hide=False):
    h = " (hide yes)" if hide else ""
    return f'\t\t(property "{k}" "{v}" (at {x} {y} 0){h} (effects (font (size 1.27 1.27))))\n'


def ad7124():
    left = [("4", "AIN0/IOUT/VBIAS", "bidirectional"), ("5", "AIN1/IOUT/VBIAS", "bidirectional"),
            ("8", "AIN2/IOUT/VBIAS/P1", "bidirectional"), ("9", "AIN3/IOUT/VBIAS/P2", "bidirectional"),
            ("16", "AIN4/IOUT/VBIAS", "bidirectional"), ("17", "AIN5/IOUT/VBIAS", "bidirectional"),
            ("20", "AIN6/IOUT/VBIAS/REFIN2(+)", "bidirectional"), ("21", "AIN7/IOUT/VBIAS/REFIN2(-)", "bidirectional"),
            ("12", "REFIN1(+)", "input"), ("13", "REFIN1(-)", "input")]
    right = [("30", "SCLK", "input"), ("29", "DIN", "input"), ("28", "DOUT/~{RDY}", "output"),
             ("32", "~{CS}", "input"), ("22", "REFOUT", "output"), ("24", "REGCAPA", "passive"),
             ("1", "REGCAPD", "passive"), ("27", "~{SYNC}", "input"), ("31", "CLK", "bidirectional"),
             ("25", "PSW", "passive")]
    top = [("26", "AVDD", "power_in"), ("2", "IOVDD", "power_in")]
    bot = [("23", "AVSS", "power_in"), ("3", "DGND", "power_in"), ("33", "EP", "passive")]
    dnc = ["6", "7", "10", "11", "14", "15", "18", "19"]
    w, h = 45.72, 50.8
    s = '\t(symbol "AD7124-4BBCPZ" (exclude_from_sim no) (in_bom yes) (on_board yes)\n'
    s += prop("Reference", "U", 0, h / 2 + 3.81)
    s += prop("Value", "AD7124-4BBCPZ-RL7", 0, -h / 2 - 3.81)
    s += prop("Footprint", "Package_CSP:LFCSP-32-1EP_5x5mm_P0.5mm_EP3.6x3.6mm", 0, -h / 2 - 6.35, True)
    s += prop("Datasheet", "https://www.analog.com/media/en/technical-documentation/data-sheets/ad7124-4.pdf", 0, -h / 2 - 8.89, True)
    s += prop("Description", "ADC sigma-delta 24 bit, 4 canales diferenciales, PGA 1-128, LFCSP-32 (CP-32-30)", 0, 0, True)
    s += '\t\t(symbol "AD7124-4BBCPZ_0_1"\n'
    s += f'\t\t\t(rectangle (start {-w/2} {h/2}) (end {w/2} {-h/2}) (stroke (width 0.254) (type default)) (fill (type background)))\n'
    s += '\t\t)\n\t\t(symbol "AD7124-4BBCPZ_1_1"\n'
    y0 = h / 2 - 2.54
    for i, (n, nm, t) in enumerate(left):
        s += pin(t, -w / 2 - 2.54, y0 - i * 2.54, 0, nm, n)
    for i, (n, nm, t) in enumerate(right):
        s += pin(t, w / 2 + 2.54, y0 - i * 2.54, 180, nm, n)
    for i, (n, nm, t) in enumerate(top):
        s += pin(t, 0 + i * 7.62, h / 2 + 2.54, 270, nm, n)
    for i, (n, nm, t) in enumerate(bot):
        s += pin(t, -7.62 + i * 7.62, -h / 2 - 2.54, 90, nm, n)
    for i, n in enumerate(dnc):
        s += pin("no_connect", w / 2 + 2.54, y0 - (len(right) + 1 + i) * 2.54 + 0.0, 180, "DNC", n)
    s += '\t\t)\n\t)\n'
    return s


def pmos_gds():
    s = '\t(symbol "Q_PMOS_GDS_DPAK" (pin_names (offset 0) hide) (exclude_from_sim no) (in_bom yes) (on_board yes)\n'
    s += prop("Reference", "Q", 5.08, 1.27)
    s += prop("Value", "NTD25P03LT4G", 5.08, -1.27)
    s += prop("Footprint", "Package_TO_SOT_SMD:TO-252-2", 5.08, -3.81, True)
    s += prop("Datasheet", "https://www.onsemi.com/pdf/datasheet/ntd25p03l-d.pdf", 5.08, -6.35, True)
    s += prop("Description", "P-MOSFET -30 V, logic level, DPAK (1=G, 2=D/tab, 3=S)", 0, 0, True)
    s += '\t\t(symbol "Q_PMOS_GDS_DPAK_0_1"\n'
    s += ('\t\t\t(polyline (pts (xy 0.254 0) (xy -2.54 0)) (stroke (width 0) (type default)) (fill (type none)))\n'
          '\t\t\t(polyline (pts (xy 0.254 1.905) (xy 0.254 -1.905)) (stroke (width 0.254) (type default)) (fill (type none)))\n'
          '\t\t\t(polyline (pts (xy 0.762 -1.27) (xy 0.762 -2.286)) (stroke (width 0.254) (type default)) (fill (type none)))\n'
          '\t\t\t(polyline (pts (xy 0.762 0.508) (xy 0.762 -0.508)) (stroke (width 0.254) (type default)) (fill (type none)))\n'
          '\t\t\t(polyline (pts (xy 0.762 2.286) (xy 0.762 1.27)) (stroke (width 0.254) (type default)) (fill (type none)))\n'
          '\t\t\t(polyline (pts (xy 2.54 2.54) (xy 2.54 1.778) (xy 0.762 1.778)) (stroke (width 0) (type default)) (fill (type none)))\n'
          '\t\t\t(polyline (pts (xy 2.54 -2.54) (xy 2.54 0) (xy 0.762 0)) (stroke (width 0) (type default)) (fill (type none)))\n'
          '\t\t\t(polyline (pts (xy 0.762 -1.778) (xy 3.302 -1.778) (xy 3.302 1.778) (xy 0.762 1.778)) (stroke (width 0) (type default)) (fill (type none)))\n'
          '\t\t\t(polyline (pts (xy 2.286 0) (xy 1.27 0.381) (xy 1.27 -0.381) (xy 2.286 0)) (stroke (width 0) (type default)) (fill (type outline)))\n'
          '\t\t\t(circle (center 1.651 0) (radius 2.794) (stroke (width 0.254) (type default)) (fill (type none)))\n')
    s += '\t\t)\n\t\t(symbol "Q_PMOS_GDS_DPAK_1_1"\n'
    s += pin("input", -5.08, 0, 0, "G", "1")
    s += pin("passive", 2.54, 5.08, 270, "D", "2")
    s += pin("passive", 2.54, -5.08, 90, "S", "3")
    s += '\t\t)\n\t)\n'
    return s


os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "w", encoding="utf-8") as f:
    f.write('(kicad_symbol_lib (version 20241209) (generator "microohm_gen") (generator_version "10.0")\n')
    f.write(ad7124())
    f.write(pmos_gds())
    f.write(')\n')
print("OK", os.path.abspath(OUT))
