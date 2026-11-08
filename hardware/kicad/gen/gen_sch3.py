"""Esquematico jerarquico v2 con CABLEADO EXPLICITO (KiCad 10).
Coordenadas de diseno en unidades de grilla U = 2,54 mm. Referencias numeradas por hoja (R4xx = hoja 4)."""
import math
import os
import sys
import uuid

sys.path.insert(0, os.path.dirname(__file__))
from libsym import get_symbol, pins  # noqa: E402
from sexp import dump  # noqa: E402

U = 2.54
HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.abspath(os.path.join(HERE, ".."))
NAME = "microohmetro_v2"
MYLIB = os.path.join(PROJ, "Librerias", "microohm.kicad_sym")
ROOT = str(uuid.uuid5(uuid.NAMESPACE_URL, "microohmetro_v2_root"))
_n = [0]


def uid():
    _n[0] += 1
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"mo3-{_n[0]}"))


R06, C06, C08 = "Resistor_SMD:R_0603_1608Metric", "Capacitor_SMD:C_0603_1608Metric", "Capacitor_SMD:C_0805_2012Metric"
R25, SOT23 = "Resistor_SMD:R_2512_6332Metric", "Package_TO_SOT_SMD:SOT-23"
DS = {
    "AD7124": "https://www.analog.com/media/en/technical-documentation/data-sheets/ad7124-4.pdf",
    "REF33": "https://www.ti.com/lit/ds/symlink/ref3325.pdf", "INA181": "https://www.ti.com/lit/ds/symlink/ina181.pdf",
    "OPA388": "https://www.ti.com/lit/ds/symlink/opa388.pdf", "BQ25895": "https://www.ti.com/lit/ds/symlink/bq25895.pdf",
    "STUSB4500": "https://www.st.com/resource/en/datasheet/stusb4500.pdf",
    "C3": "https://www.espressif.com/sites/default/files/documentation/esp32-c3-wroom-02_datasheet_en.pdf",
    "AP2112": "https://www.diodes.com/assets/Datasheets/AP2112.pdf",
    "USBLC6": "https://www.st.com/resource/en/datasheet/usblc6-2.pdf",
    "AO3401A": "https://www.aosmd.com/res/datasheets/AO3401A.pdf", "2N7002": "https://www.onsemi.com/pdf/datasheet/nds7002a-d.pdf",
    "BAT54S": "https://www.onsemi.com/pdf/datasheet/bat54lt1-d.pdf", "WSK2512": "https://www.vishay.com/docs/30108/wsk2512.pdf",
    "FCR7350": "https://www.cliffuk.co.uk/products/testandmeasurement/sockets/FCR7350.pdf",
    "JSTXH": "https://www.jst-mfg.com/product/pdf/eng/eXH.pdf", "NTD25P03": "https://www.onsemi.com/pdf/datasheet/ntd25p03l-d.pdf",
}
SHEETS = {  # clave: (archivo, titulo, descripcion, pagina)
    "USB": ("1_usb_pd.kicad_sch", "1. Entrada USB-C y Power Delivery",
            "VBUS_C -> TVS -> Q101 (abre solo con contrato PD de 9 V) -> VBUS_IN. CC1/CC2 al STUSB4500; D+/D- con ESD al ESP32.", 2),
    "CHG": ("2_cargador.kicad_sch", "2. Cargador y bateria",
            "VBUS_IN -> BQ25895 (buck 1,5 MHz) -> L201 -> SYS. BAT -> Q201||Q202 (polaridad) -> LiPo. TS con NTC.", 3),
    "PWR": ("3_regulacion.kicad_sch", "3. Regulacion 3,3 V",
            "SYS -> AP2112K-3.3 -> +3V3 (digital) -> FB401 -> AVDD (analogico del ADC).", 4),
    "SRC": ("4_fuente_corriente.kicad_sch", "4. Fuente de corriente pulsada",
            "U401 REF3325 -> R401 -> VSET -> R403 -> U402 OPA388 -> R404 -> Q403 P-MOS -> I_PLUS.   I = VSET / (20 x RS) = 1,042 A / 0,502 A.", 5),
    "KEL": ("5_kelvin_shunt.kicad_sch", "5. Medicion Kelvin y shunt",
            "I_PLUS -> DUT -> I_MINUS -> RS (0,12 Ohm, 4T) -> R_LIFT -> GND.  S+/S- y RS+/RS- van al ADC; INA181 cierra el lazo.", 6),
    "ADC": ("6_adc.kicad_sch", "6. ADC AD7124-4",
            "S+/S- -> 1k + 1n + 10n dif -> AIN0/AIN1 (PGA 128/16/2).  RS+/RS- -> 100 + 1n -> AIN2/AIN3 (G=16).  SPI al ESP32.", 7),
    "MCU": ("7_mcu.kicad_sch", "7. Microcontrolador ESP32-C3",
            "USB nativo (programacion y consola), SPI al ADC, I2C al cargador y al PD, control del pulso I_OFF / I_LOW, LED.", 8),
    "MEC": ("8_mecanicos.kicad_sch", "8. Mecanicos y puntos de prueba",
            "Agujeros M3, puntos de prueba y bandera de GND.", 9),
}
G, V3 = "GND", "+3V3"
POWER = {G: ("power", "GND", 270), V3: ("power", "+3V3", 90)}

comps, wires, xlabels, xpowers, xflags, xtexts, xrects = [], {k: [] for k in SHEETS}, [], [], [], [], []
_sym = {}


def sym(lib, name):
    if (lib, name) not in _sym:
        _sym[(lib, name)] = get_symbol(lib, name, MYLIB if lib == "microohm" else None)
    return _sym[(lib, name)]


def xf(x, y, rot):
    u, v = x, -y
    t = math.radians(rot)
    return (u * math.cos(t) + v * math.sin(t), -u * math.sin(t) + v * math.cos(t))


def C(sheet, ref, lib, name, value, fp, x, y, rot=0, pins_=None, ds="", mpn="", desc="", fpos=None):
    c = dict(sheet=sheet, ref=ref, lib=lib, name=name, value=value, fp=fp, x=x * U, y=y * U, rot=rot,
             pins=pins_ or {}, ds=ds, mpn=mpn, desc=desc, auto=False, fpos=fpos)
    comps.append(c)
    return c


def RES(sheet, ref, val, x, y, n1, n2, rot=90, fp=R06, spec="Thick film 1 %", mpn=""):
    return C(sheet, ref, "Device", "R", val, fp, x, y, rot, {"1": n1, "2": n2}, desc=spec, mpn=mpn)


def CAP(sheet, ref, val, x, y, n1, n2, rot=0, fp=C06, spec="X7R"):
    return C(sheet, ref, "Device", "C", val, fp, x, y, rot, {"1": n1, "2": n2}, desc=spec)


_auto = {k: 0 for k in SHEETS}
PST = {"USB": 63}


def PAS(sheet, ref, lib, name, val, fp, n1, n2, spec="", mpn=""):
    """Pasivo secundario: zona inferior, conectado por etiquetas."""
    i = _auto[sheet]
    _auto[sheet] += 1
    col, row = i % 7, i // 7
    c = C(sheet, ref, lib, name, val, fp, 14 + col * 12.5, PST.get(sheet, 58) + row * 4, 0 if name in ("LED", "D_TVS") else 90, {"1": n1, "2": n2}, desc=spec, mpn=mpn)
    c["auto"] = True
    return c


def PR(sheet, ref, val, n1, n2, fp=R06, spec="Thick film 1 %"):
    return PAS(sheet, ref, "Device", "R", val, fp, n1, n2, spec)


def PC(sheet, ref, val, n1, n2, fp=C06, spec="X7R"):
    return PAS(sheet, ref, "Device", "C", val, fp, n1, n2, spec)


def W(sheet, *pts):
    wires[sheet].append(list(pts))


def LBL(sheet, net, x, y, ang):
    xlabels.append((sheet, net, x * U, y * U, ang))


def PWR(sheet, net, x, y, outward):
    xpowers.append((sheet, net, x * U, y * U, outward))


def FLAG(sheet, x, y):
    xflags.append((sheet, x * U, y * U))


def TXT(sheet, s, x, y, size=1.5, bold=False, color="0 72 132 1"):
    xtexts.append((sheet, s, x * U, y * U, size, bold, color))


def RECT(sheet, x1, y1, x2, y2):
    xrects.append((sheet, x1 * U, y1 * U, x2 * U, y2 * U))


# =====================================================================================================
# HOJA 1 - USB / PD
s = "USB"
C(s, "J101", "Connector", "USB_C_Receptacle", "USB-C 24p 5 A", "Connector_USB:USB_C_Receptacle_Amphenol_12401610E4-2A",
  16, 37, 0, {"A1": G, "A12": G, "B1": G, "B12": G, "SH": G, "A4": "VBUS_C", "A9": "VBUS_C", "B4": "VBUS_C", "B9": "VBUS_C",
              "A5": "CC1", "B5": "CC2", "A6": "USB_DP", "B6": "USB_DP", "A7": "USB_DN", "B7": "USB_DN",
              **{p: "NC" for p in ["A2", "A3", "B2", "B3", "A8", "B8", "A10", "A11", "B10", "B11"]}},
  mpn="Amphenol 12401610E4#2A", desc="Receptaculo USB-C 24 pines (compatible EPR)")
C(s, "Q101", "Transistor_FET", "AO3401A", "AO3401A", SOT23, 44, 19, 270, {"2": "VBUS_C", "3": "VBUS_IN", "1": "VBUS_EN"},
  DS["AO3401A"], "AO3401A", "Interruptor de VBUS (VBUS_EN_SNK)")
C(s, "D101", "Device", "D_TVS", "SMBJ12A", "Diode_SMD:D_SMB", 29, 21.5, 90, {"1": G, "2": "VBUS_C"}, mpn="SMBJ12A", desc="TVS 12 V")
CAP(s, "C101", "10u/25V", 33, 21.5, "VBUS_C", G, fp=C08)
RES(s, "R101", "100k", 39.5, 14, "VBUS_C", "VBUS_EN")
C(s, "U101", "Interface_USB", "STUSB4500QTR", "STUSB4500QTR", "Package_DFN_QFN:QFN-24-1EP_4x4mm_P0.5mm_EP2.7x2.7mm", 80, 43, 0,
  {"24": "VBUS_C", "2": "CC1", "1": "CC1", "4": "CC2", "5": "CC2", "18": "VBUS_C", "9": "VBUS_IN", "22": V3,
   "21": "VREG_1V2", "23": "VREG_2V7", "10": G, "25": G, "7": "I2C_SCL", "8": "I2C_SDA", "12": G, "13": G, "6": G,
   "16": "VBUS_EN", **{p: "NC" for p in ["11", "19", "14", "20", "15", "17", "3"]}}, DS["STUSB4500"], "STUSB4500QTR",
  "Controlador USB PD sink (PDO2 = 9 V / 2 A)")
C(s, "U102", "Power_Protection", "USBLC6-2SC6", "USBLC6-2SC6", "Package_TO_SOT_SMD:SOT-23-6", 44, 40, 0,
  {"1": "USB_DN", "6": "USB_DN", "3": "USB_DP", "4": "USB_DP", "5": V3, "2": G}, DS["USBLC6"], "USBLC6-2SC6", "ESD en D+/D-")
CAP(s, "C102", "1u", 97, 31.5, "VREG_1V2", G)
CAP(s, "C103", "1u", 92, 33.5, "VREG_2V7", G)
PC(s, "C104", "1u", V3, G)
W(s, "J101.A4", (25, 27), (25, 20), (42, 20))
W(s, (29, 20), "D101.2"); W(s, (33, 20), "C101.1")
W(s, (36, 20), (36, 14), "R101.1"); W(s, "R101.2", (44, 14), "Q101.1"); W(s, (44, 14), (47, 14))
LBL(s, "VBUS_EN", 47, 14, 0); LBL(s, "VBUS_C", 27, 20, 90)
W(s, "Q101.3", (54, 20)); LBL(s, "VBUS_IN", 54, 20, 0)
FLAG(s, 40, 20); FLAG(s, 50, 20)
W(s, "J101.A5", (67, 29), (67, 39), "U101.1"); W(s, (67, 38), "U101.2")
W(s, "J101.B5", (65, 30), (65, 42), "U101.5"); W(s, (65, 41), "U101.4")
W(s, "J101.A7", (26, 32), (26, 40), "U102.1"); W(s, "J101.B7", (26, 33))
W(s, "J101.A6", (24, 34), (24, 41), "U102.3"); W(s, "J101.B6", (24, 35))
W(s, "U102.6", (52, 40)); LBL(s, "USB_DN", 52, 40, 0); LBL(s, "USB_DN", 34, 40, 90)
W(s, "U102.4", (52, 41)); LBL(s, "USB_DP", 52, 41, 0); LBL(s, "USB_DP", 30, 41, 270)
W(s, "U101.21", (82, 30), "C102.1"); W(s, "U101.23", (83, 32), "C103.1")

# =====================================================================================================
# HOJA 2 - CARGADOR
s = "CHG"
C(s, "U201", "Battery_Management", "BQ25895RTW", "BQ25895RTWR",
  "Package_DFN_QFN:Texas_RTW_WQFN-24-1EP_4x4mm_P0.5mm_EP2.7x2.7mm_ThermalVias", 50, 38, 0,
  {"1": "VBUS_IN", "23": "PMID", "22": "REGN", "21": "BTST", "19": "SW", "20": "SW", "15": "SYS", "16": "SYS",
   "13": "VBAT_CHG", "14": "VBAT_CHG", "17": G, "18": G, "25": G, "4": "CHG_STAT", "5": "I2C_SCL", "6": "I2C_SDA",
   "7": "BQ_INT", "8": G, "9": G, "10": "ILIM", "11": "TS", "12": "NC", "2": "NC", "3": "NC", "24": "NC"},
  DS["BQ25895"], "BQ25895RTWR", "Cargador buck 1S I2C, 2 A, power-path")
CAP(s, "C201", "1u/25V", 40, 28.5, "VBUS_IN", G)
RES(s, "R201", "178", 43, 46.5, "ILIM", G, rot=0, spec="IINMAX = 355/178 = 2,0 A")
C(s, "D201", "Device", "LED", "LED ambar CHG", "LED_SMD:LED_0603_1608Metric", 58.5, 31, 0, {"1": "CHG_STAT", "2": "LEDC_A"},
  desc="Indicador de carga")
RES(s, "R202", "1k", 63.5, 31, "LEDC_A", V3)
C(s, "L201", "Device", "L", "2.2u", "Inductor_SMD:L_Bourns-SRN4018", 66.5, 36, 90, {"1": "SW", "2": "SYS"},
  mpn="SRN4018-2R2M", desc="2,2 uH, Isat >= 3,5 A")
CAP(s, "C202", "47n", 59, 37.5, "SW", "BTST")
CAP(s, "C203", "10u/10V", 75, 29.5, "SYS", G, fp=C08)
CAP(s, "C204", "10u/10V", 80, 29.5, "SYS", G, fp=C08)
C(s, "Q201", "Transistor_FET", "AO3401A", "AO3401A", SOT23, 92, 40, 270, {"2": "VBAT_CHG", "3": "BATT_RAW", "1": "PG_POL"},
  DS["AO3401A"], "AO3401A", "Polaridad inversa")
C(s, "Q202", "Transistor_FET", "AO3401A", "AO3401A", SOT23, 92, 50, 270, {"2": "VBAT_CHG", "3": "BATT_RAW", "1": "PG_POL"},
  DS["AO3401A"], "AO3401A", "Polaridad inversa (paralelo)")
C(s, "J201", "Connector_Generic", "Conn_01x03", "LiPo 1S (JST XH)", "Connector_JST:JST_XH_S3B-XH-SM4-TB_1x03-1MP_P2.50mm_Horizontal",
  108, 42, 0, {"1": "BATT_RAW", "2": "TS", "3": G}, DS["JSTXH"], "S3B-XH-SM4-TB", "1 = BAT+, 2 = NTC, 3 = BAT-")
RES(s, "R203", "5.23k", 64, 44.5, "REGN", "TS", rot=0, spec="RT1 (datasheet)")
RES(s, "R204", "30.1k", 68, 49.5, "TS", G, rot=0, spec="RT2 (datasheet)")
C(s, "TH201", "Device", "Thermistor_NTC", "10k NTC", R06, 74, 49.5, 0, {"1": "TS", "2": G}, mpn="NCP18XH103F03RB",
  desc="DNP si la LiPo trae NTC")
PC(s, "C205", "10u/25V", "PMID", G, fp=C08); PC(s, "C206", "10u/25V", "PMID", G, fp=C08)
PC(s, "C207", "4.7u/10V", "REGN", G); PC(s, "C208", "10u/10V", "VBAT_CHG", G, fp=C08)
PR(s, "R205", "100k", "PG_POL", G)
W(s, "U201.1", (44, 31), (44, 27), (36, 27)); LBL(s, "VBUS_IN", 36, 27, 180); W(s, (40, 27), "C201.1")
W(s, "U201.10", (43, 45), "R201.1")
W(s, "U201.4", "D201.1"); W(s, "D201.2", "R202.1"); W(s, "R202.2", (66, 31)); PWR(s, V3, 66, 31, 90)
W(s, "U201.23", (58, 34)); LBL(s, "PMID", 58, 34, 0)
W(s, "U201.19", "L201.1"); W(s, (59, 36), "C202.1"); W(s, "U201.21", (56, 38), (56, 39), "C202.2")
W(s, "L201.2", (70, 36), (70, 28), (86, 28)); W(s, "U201.15", (71, 40), (71, 28))
W(s, (75, 28), "C203.1"); W(s, (80, 28), "C204.1"); LBL(s, "SYS", 86, 28, 0); FLAG(s, 84, 28)
W(s, "U201.13", (90, 41)); W(s, (88, 41), (88, 51), "Q202.2")
LBL(s, "VBAT_CHG", 80, 41, 270); FLAG(s, 76, 41)
W(s, "Q201.3", (106, 41)); W(s, "Q202.3", (98, 51), (98, 41)); FLAG(s, 102, 41)
W(s, "U201.22", (64, 43)); LBL(s, "REGN", 60, 43, 90)
W(s, "U201.11", (57, 45), (57, 48), (78, 48)); W(s, "R203.2", (64, 48)); W(s, (68, 48), "R204.1"); W(s, (74, 48), "TH201.1")
LBL(s, "TS", 78, 48, 0)

# =====================================================================================================
# HOJA 3 - REGULACION
s = "PWR"
C(s, "U301", "Regulator_Linear", "AP2112K-3.3", "AP2112K-3.3TRG1", "Package_TO_SOT_SMD:SOT-23-5", 48, 36, 0,
  {"1": "SYS", "3": "SYS", "2": G, "5": V3, "4": "NC"}, DS["AP2112"], "AP2112K-3.3TRG1", "LDO 600 mA")
CAP(s, "C301", "1u", 37, 36.5, "SYS", G)
CAP(s, "C302", "10u/10V", 56, 36.5, V3, G, fp=C08)
C(s, "FB301", "Device", "FerriteBead_Small", "600R@100MHz", "Inductor_SMD:L_0603_1608Metric", 64, 35, 90,
  {"1": V3, "2": "AVDD"}, mpn="BLM18KG601SN1D", desc="Ferrita de aislamiento analogico")
CAP(s, "C303", "10u/10V", 70, 36.5, "AVDD", G, fp=C08)
CAP(s, "C304", "100n", 76, 36.5, "AVDD", G)
W(s, (30, 35), "U301.1"); LBL(s, "SYS", 30, 35, 180); W(s, "U301.3", (43, 36), (43, 35))
W(s, (37, 35), "C301.1")
W(s, "U301.5", "FB301.1"); W(s, (56, 35), "C302.1"); PWR(s, V3, 60, 35, 90)
W(s, "FB301.2", (84, 35)); W(s, (70, 35), "C303.1"); W(s, (76, 35), "C304.1"); LBL(s, "AVDD", 84, 35, 0)
FLAG(s, 80, 35)

# =====================================================================================================
# HOJA 4 - FUENTE DE CORRIENTE
s = "SRC"
C(s, "U401", "Reference_Voltage", "REF3025", "REF3325AIDBZR", SOT23, 16, 32, 0, {"1": V3, "2": "VREF", "3": G},
  DS["REF33"], "REF3325AIDBZR", "Referencia 2,5 V +-0,15 %, 30 ppm/C")
CAP(s, "C401", "1u", 21, 33.5, "VREF", G)
RES(s, "R401", "10k", 25.5, 32, "VREF", "VSET", spec="Thin film 0,1 % (R_VSET)")
C(s, "Q401", "Transistor_FET", "2N7002", "2N7002", SOT23, 29, 36, 0, {"3": "VSET", "2": G, "1": "I_OFF"},
  DS["2N7002"], "2N7002", "Q_OFF: corriente apagada por defecto")
CAP(s, "C402", "22n", 35, 33.5, "VSET", G, spec="C0G (arranque suave)")
RES(s, "R402", "9.31k", 39, 33.5, "VSET", "NIL", rot=0, spec="Nivel I_L")
C(s, "Q402", "Transistor_FET", "2N7002", "2N7002", SOT23, 38, 39, 0, {"3": "NIL", "2": G, "1": "I_LOW"},
  DS["2N7002"], "2N7002", "Q_LOW: selecciona I_L")
RES(s, "R403", "10k", 43.5, 32, "VSET", "NINN", spec="Thin film 0,1 % (integrador)")
C(s, "U402", "Amplifier_Operational", "OPA333xxDBV", "OPA388IDBVR", "Package_TO_SOT_SMD:SOT-23-5", 54, 31, 0,
  {"3": "INA_OUT", "4": "NINN", "1": "OPA_OUT", "5": "SYS", "2": G}, DS["OPA388"], "OPA388IDBVR", "Lazo zero-drift")
CAP(s, "C403", "10n", 52.5, 41, "NINN", "OPA_OUT", rot=90, spec="C0G (integrador)")
RES(s, "R404", "100", 62.5, 31, "OPA_OUT", "GATE")
C(s, "Q403", "microohm", "Q_PMOS_GDS_DPAK", "NTD25P03LT4G", "Package_TO_SOT_SMD:TO-252-2", 72, 31, 0,
  {"1": "GATE", "3": "SYS", "2": "I_PLUS"}, DS["NTD25P03"], "NTD25P03LT4G", "P-MOS de paso (pulsos 3,5 W / 120 ms)")
RES(s, "R405", "100k", 67, 34.5, "GATE", "SYS", rot=0, spec="Pull-up de gate")
PC(s, "C404", "100n", V3, G); PC(s, "C405", "100n", "SYS", G)
PR(s, "R406", "100k", "I_LOW", G); PR(s, "R407", "100k", "I_OFF", V3, spec="Corriente apagada al arrancar")
W(s, "U401.2", "R401.1"); W(s, (21, 32), "C401.1")
W(s, "R401.2", "R403.1"); W(s, "Q401.3", (30, 32)); W(s, (35, 32), "C402.1"); W(s, (39, 32), "R402.1")
W(s, "Q401.1", (26, 36), (26, 41)); LBL(s, "I_OFF", 26, 41, 270)
W(s, "R402.2", "Q402.3"); W(s, "Q402.1", (34, 39), (34, 43)); LBL(s, "I_LOW", 34, 43, 270)
W(s, "R403.2", "U402.4"); W(s, (47, 32), (47, 41), "C403.1"); W(s, "C403.2", (59, 41), (59, 31))
W(s, "U402.1", "R404.1"); W(s, "R404.2", "Q403.1"); W(s, (67, 31), "R405.1")
W(s, "Q403.2", (73, 25), (82, 25)); LBL(s, "I_PLUS", 82, 25, 0)
W(s, "Q403.3", (73, 40)); W(s, "R405.2", (67, 38), (73, 38)); LBL(s, "SYS", 73, 40, 270)
TXT(s, "VSET = 2,5 V  -> I_H = 1,042 A", 25, 27.5, 1.4); TXT(s, "VSET = 1,205 V -> I_L = 0,502 A (Q402)", 25, 29, 1.4)

# =====================================================================================================
# HOJA 5 - KELVIN
s = "KEL"
for ref, net, col, mpn, y in [("J501", "I_PLUS", "rojo", "FCR7350R", 22), ("J502", "S_PLUS", "amarillo", "FCR7350Y", 27),
                              ("J503", "S_MINUS", "azul", "FCR7350L", 32), ("J504", "I_MINUS", "negro", "FCR7350B", 37)]:
    C(s, ref, "Connector_Generic", "Conn_01x01", f"{net} ({col})", "Connector:Banana_Jack_1Pin",
      16, y, 180, {"1": net}, "", f"Borne 4 mm de panel {col} (agujero 6 mm)", f"Borne banana 4 mm vertical {col}", fpos="T")
C(s, "R501", "Device", "R_Shunt", "0.12 1% 4T", "Resistor_SMD:R_Shunt_Vishay_WSK2512_6332Metric_T1.19mm", 40, 39, 0,
  {"1": "I_MINUS", "4": "NLIFT", "2": "RS_SP", "3": "RS_SN"}, DS["WSK2512"], "WSK2512R1200FEA", "Shunt Kelvin 0,12 Ohm 1 %", fpos="L")
RES(s, "R502", "0.68", 40, 44.5, "NLIFT", G, rot=0, fp=R25, spec="R_LIFT 1 % 1 W")
C(s, "U501", "Amplifier_Current", "INA181", "INA181A1IDBVR", "Package_TO_SOT_SMD:SOT-23-6", 54, 39, 0,
  {"3": "RS_SP", "4": "RS_SN", "6": V3, "2": G, "5": G, "1": "INA_OUT"}, DS["INA181"], "INA181A1IDBVR", "Sensado 20 V/V")
PC(s, "C501", "100n", V3, G)
W(s, "J501.1", (24, 22)); LBL(s, "I_PLUS", 24, 22, 0)
W(s, "J502.1", (24, 27)); LBL(s, "S_PLUS", 24, 27, 0)
W(s, "J503.1", (24, 32)); LBL(s, "S_MINUS", 24, 32, 0)
W(s, "J504.1", "R501.1"); W(s, "R501.4", "R502.1")
W(s, "R501.2", "U501.3"); W(s, "R501.3", "U501.4")
W(s, (45, 38), (45, 34)); LBL(s, "RS_SP", 45, 34, 90)
W(s, (47, 40), (47, 44)); LBL(s, "RS_SN", 47, 44, 270)
W(s, "U501.1", (62, 39)); LBL(s, "INA_OUT", 62, 39, 0)
RECT(s, 5, 19, 11.5, 40)
TXT(s, "DUT", 6.6, 29, 2.5, True); TXT(s, "externo", 6.2, 31, 1.4); TXT(s, "(pinzas", 6.0, 32.6, 1.2); TXT(s, "Kelvin)", 6.0, 34, 1.2)
TXT(s, "I+ e I- llevan la corriente; S+ y S- solo miden tension (sin corriente).", 14, 51, 1.4)
TXT(s, "R_LIFT eleva el modo comun >= 0,40 V (requisito del PGA con G > 1).", 14, 53, 1.4)

# =====================================================================================================
# HOJA 6 - ADC
s = "ADC"
C(s, "U601", "microohm", "AD7124-4BBCPZ", "AD7124-4BBCPZ-RL7", "Package_CSP:LFCSP-32-1EP_5x5mm_P0.5mm_EP3.6x3.6mm", 73, 40, 0,
  {"4": "AIN0", "5": "AIN1", "8": "AIN2", "9": "AIN3", "16": G, "17": G, "20": G, "21": G, "12": "NC", "13": "NC",
   "22": "REFOUT", "30": "SPI_SCLK", "29": "SPI_MOSI", "28": "SPI_MISO", "32": "SPI_CS", "27": V3, "31": G, "25": "NC",
   "24": "REGCAPA", "1": "REGCAPD", "26": "AVDD", "2": V3, "23": G, "3": G, "33": G}, DS["AD7124"], "AD7124-4BBCPZ-RL7",
  "ADC sigma-delta 24 bit, PGA 1-128")
RES(s, "R601", "1k", 16.5, 20, "S_PLUS", "AIN0", spec="Thin film 0,1 % 25 ppm/C")
RES(s, "R602", "1k", 16.5, 26, "S_MINUS", "AIN1", spec="Thin film 0,1 % 25 ppm/C")
CAP(s, "C601", "1n", 22, 21.5, "AIN0", G, spec="C0G")
CAP(s, "C602", "1n", 22, 27.5, "AIN1", G, spec="C0G")
CAP(s, "C603", "10n", 46, 22.5, "AIN0", "AIN1", spec="C0G diferencial")
C(s, "D601", "Diode", "BAT54S", "BAT54S", SOT23, 32, 18, 0, {"1": G, "2": "AVDD", "3": "AIN0"}, DS["BAT54S"], "BAT54S", "Clamp AIN0")
C(s, "D602", "Diode", "BAT54S", "BAT54S", SOT23, 34, 24, 0, {"1": G, "2": "AVDD", "3": "AIN1"}, DS["BAT54S"], "BAT54S", "Clamp AIN1")
RES(s, "R603", "100", 16.5, 44, "RS_SP", "AIN2", spec="Thin film 0,1 %")
RES(s, "R604", "100", 16.5, 50, "RS_SN", "AIN3", spec="Thin film 0,1 %")
CAP(s, "C604", "1n", 22, 45.5, "AIN2", G, spec="C0G")
CAP(s, "C605", "1n", 22, 51.5, "AIN3", G, spec="C0G")
CAP(s, "C606", "100n", 97, 36.5, "REFOUT", G)
CAP(s, "C607", "100n", 93, 37.5, "REGCAPA", G)
CAP(s, "C608", "100n", 89, 38.5, "REGCAPD", G)
PC(s, "C609", "1u", "AVDD", G); PC(s, "C610", "1u", V3, G); PC(s, "C611", "100n", V3, G)
PR(s, "R605", "10k", "SPI_CS", V3)
W(s, (10, 20), "R601.1"); LBL(s, "S_PLUS", 10, 20, 180)
W(s, "R601.2", (57, 20), (57, 31), "U601.4"); W(s, (22, 20), "C601.1"); W(s, (32, 20), "D601.3"); W(s, (46, 20), "C603.1")
W(s, (10, 26), "R602.1"); LBL(s, "S_MINUS", 10, 26, 180)
W(s, "R602.2", (55, 26), (55, 32), "U601.5"); W(s, (22, 26), "C602.1"); W(s, (34, 26), "D602.3"); W(s, "C603.2", (46, 26))
W(s, (10, 44), "R603.1"); LBL(s, "RS_SP", 10, 44, 180)
W(s, "R603.2", (53, 44), (53, 33), "U601.8"); W(s, (22, 44), "C604.1")
W(s, (10, 50), "R604.1"); LBL(s, "RS_SN", 10, 50, 180)
W(s, "R604.2", (59, 50), (59, 34), "U601.9"); W(s, (22, 50), "C605.1")
W(s, "U601.22", (97, 35), "C606.1"); W(s, "U601.24", (93, 36), "C607.1"); W(s, "U601.1", (89, 37), "C608.1")
W(s, "U601.27", (84, 38)); PWR(s, V3, 84, 38, 0)
W(s, "U601.31", (85, 39), (85, 42)); PWR(s, G, 85, 42, 270)

# =====================================================================================================
# HOJA 7 - MCU
s = "MCU"
C(s, "U701", "RF_Module", "ESP32-C3-WROOM-02", "ESP32-C3-WROOM-02-N4", "RF_Module:ESP32-C3-WROOM-02", 60, 38, 0,
  {"1": V3, "2": "EN", "9": G, "19": G, "18": "I_OFF", "17": "BQ_INT", "16": "LED_STAT", "15": "I_LOW", "3": "I2C_SDA",
   "4": "SPI_MISO", "5": "SPI_SCLK", "6": "SPI_MOSI", "7": "I2C_SCL", "8": "BOOT", "10": "SPI_CS", "13": "USB_DN",
   "14": "USB_DP", "11": "U0RX", "12": "U0TX"}, DS["C3"], "ESP32-C3-WROOM-02-N4", "MCU RISC-V, BLE 5, USB nativo")
RES(s, "R701", "10k", 46, 29.5, V3, "EN", rot=0)
CAP(s, "C701", "1u", 42, 32.5, "EN", G)
C(s, "SW701", "Switch", "SW_Push", "RESET", "Button_Switch_SMD:SW_Push_SPST_NO_Alps_SKRK", 38, 33, 90, {"2": "EN", "1": G}, fpos="L")
RES(s, "R702", "10k", 40, 40.5, V3, "BOOT", rot=0)
C(s, "SW702", "Switch", "SW_Push", "BOOT", "Button_Switch_SMD:SW_Push_SPST_NO_Alps_SKRK", 36, 44, 90, {"2": "BOOT", "1": G}, fpos="L")
PC(s, "C702", "10u/10V", V3, G, fp=C08); PC(s, "C703", "100n", V3, G)
PR(s, "R703", "10k", "I2C_SDA", V3); PR(s, "R704", "10k", "I2C_SCL", V3); PR(s, "R705", "10k", "BQ_INT", V3)
PAS(s, "D701", "Device", "LED", "LED verde STAT", "LED_SMD:LED_0603_1608Metric", "LED_STAT", "LEDS_A")
PR(s, "R706", "1k", "LEDS_A", V3)
W(s, "U701.2", "SW701.2"); W(s, (46, 31), "R701.2"); W(s, (42, 31), "C701.1")
W(s, "R701.1", (46, 28)); PWR(s, V3, 46, 28, 90)
W(s, "U701.8", "SW702.2"); W(s, (40, 42), "R702.2"); W(s, "R702.1", (40, 39)); PWR(s, V3, 40, 39, 90)

# =====================================================================================================
# HOJA 8 - MECANICOS
s = "MEC"
for i, net in enumerate(["U0TX", "U0RX", G, "SYS", "VBAT_CHG", "AVDD"]):
    C(s, f"TP{801 + i}", "Connector", "TestPoint", f"TP {net}", "TestPoint:TestPoint_Pad_D1.5mm", 14 + i * 14, 28, 0,
      {"1": net}, desc="Punto de prueba")
for i in range(4):
    C(s, f"H{801 + i}", "Mechanical", "MountingHole", "M3", "MountingHole:MountingHole_3.2mm_M3", 14 + i * 14, 44, 0, {},
      desc="Agujero de montaje M3")
PWR(s, G, 100, 30, 270); FLAG(s, 100, 30)

# =====================================================================================================
#                                        MOTOR DE SALIDA
for c in comps:
    c["x"] = round(c["x"] / 1.27) * 1.27
    c["y"] = round(c["y"] / 1.27) * 1.27
    c["sd"] = sym(c["lib"], c["name"])
    c["pl"] = pins(c["sd"])
REF = {c["ref"]: c for c in comps}


def pinpos(c, num):
    for p in c["pl"]:
        if p[0] == num:
            dx, dy = xf(p[2], p[3], c["rot"])
            return (round((c["x"] + dx) / 0.635) * 0.635, round((c["y"] + dy) / 0.635) * 0.635)
    raise KeyError(f"{c['ref']}.{num}")


def P(tok):
    if isinstance(tok, str):
        r, n = tok.split(".")
        return pinpos(REF[r], n)
    return (round(tok[0] * U / 0.635) * 0.635, round(tok[1] * U / 0.635) * 0.635)


net_sheets = {}
for c in comps:
    for n in c["pins"].values():
        if n != "NC":
            net_sheets.setdefault(n, set()).add(c["sheet"])
for (sh, net, *_r) in xlabels:
    net_sheets.setdefault(net, set()).add(sh)
GLOBAL = {n for n, ss in net_sheets.items() if len(ss) > 1 and n not in POWER} | {"LED_STAT"}


class Out:
    def __init__(self, path):
        self.path, self.b, self.used, self.pw = path, [], {}, 0

    def add(self, s):
        self.b.append(s)

    def symbol(self, libid, sd, ref, x, y, rot, pinnums, props, inbom=True):
        self.used[libid] = sd
        fa = (360 - rot) % 360 if rot in (90, 270) else 0
        s = (f'\t(symbol\n\t\t(lib_id "{libid}")\n\t\t(at {x:.3f} {y:.3f} {rot})\n\t\t(unit 1)\n\t\t(body_style 1)\n'
             f'\t\t(exclude_from_sim no)\n\t\t(in_bom {"yes" if inbom else "no"})\n\t\t(on_board yes)\n'
             f'\t\t(in_pos_files yes)\n\t\t(dnp no)\n\t\t(uuid "{uid()}")\n')
        for k, v, px, py, hide, just, size in props:
            j = f" (justify {just})" if just else ""
            h = "\n\t\t\t(hide yes)" if hide else ""
            s += (f'\t\t(property "{k}" "{v}"\n\t\t\t(at {px:.3f} {py:.3f} {fa}){h}\n'
                  f'\t\t\t(effects (font (size {size} {size})){j})\n\t\t)\n')
        for n in pinnums:
            s += f'\t\t(pin "{n}"\n\t\t\t(uuid "{uid()}")\n\t\t)\n'
        s += (f'\t\t(instances\n\t\t\t(project "{NAME}"\n\t\t\t\t(path "{self.path}"\n\t\t\t\t\t(reference "{ref}")\n'
              f'\t\t\t\t\t(unit 1)\n\t\t\t\t)\n\t\t\t)\n\t\t)\n\t)\n')
        self.add(s)

    def power(self, net, x, y, outward):
        lib, nm, base = POWER[net]
        rot = int((outward - base) % 360)
        PWN[0] += 1
        ref = f"#PWR{PWN[0]:03d}"
        vx, vy = xf(0, -3.4 if nm == "GND" else 3.4, rot)
        self.symbol(f"{lib}:{nm}", sym(lib, nm), ref, x, y, rot, ["1"],
                    [("Reference", ref, x, y, True, None, 1.27), ("Value", nm, x + vx, y + vy, False, None, 1.27),
                     ("Footprint", "", x, y, True, None, 1.27), ("Datasheet", "", x, y, True, None, 1.27),
                     ("Description", "", x, y, True, None, 1.27)], inbom=False)

    def label(self, net, x, y, ang):
        just = {0: "left", 90: "left", 180: "right", 270: "right"}[ang]
        if net not in GLOBAL:
            self.add(f'\t(label "{net}"\n\t\t(at {x:.3f} {y:.3f} {ang})\n'
                     f'\t\t(effects (font (size 1.27 1.27)) (justify {just} bottom))\n\t\t(uuid "{uid()}")\n\t)\n')
            return
        L = len(net) * 1.1 + 3.4
        dx, dy = {0: (L, 0), 180: (-L, 0), 90: (0, -L), 270: (0, L)}[ang]
        self.add(f'\t(global_label "{net}"\n\t\t(shape bidirectional)\n\t\t(at {x:.3f} {y:.3f} {ang})\n'
                 f'\t\t(effects (font (size 1.27 1.27)) (justify {just}))\n\t\t(uuid "{uid()}")\n'
                 f'\t\t(property "Intersheetrefs" "${{INTERSHEET_REFS}}"\n\t\t\t(at {x + dx:.3f} {y + dy:.3f} {ang})\n'
                 f'\t\t\t(effects (font (size 1.0 1.0) italic) (justify {just}))\n\t\t)\n\t)\n')

    def wire(self, a, b):
        self.add(f'\t(wire\n\t\t(pts (xy {a[0]:.3f} {a[1]:.3f}) (xy {b[0]:.3f} {b[1]:.3f}))\n'
                 f'\t\t(stroke (width 0) (type default))\n\t\t(uuid "{uid()}")\n\t)\n')

    def junction(self, p):
        self.add(f'\t(junction\n\t\t(at {p[0]:.3f} {p[1]:.3f})\n\t\t(diameter 0)\n\t\t(color 0 0 0 0)\n\t\t(uuid "{uid()}")\n\t)\n')

    def noconn(self, p):
        self.add(f'\t(no_connect\n\t\t(at {p[0]:.3f} {p[1]:.3f})\n\t\t(uuid "{uid()}")\n\t)\n')

    def text(self, s, x, y, size, bold, color, just="left bottom"):
        b = " (thickness 0.35) bold" if bold else ""
        self.add(f'\t(text "{s}"\n\t\t(exclude_from_sim no)\n\t\t(at {x:.2f} {y:.2f} 0)\n'
                 f'\t\t(effects (font (size {size} {size}){b} (color {color})) (justify {just}))\n\t\t(uuid "{uid()}")\n\t)\n')


PWN = [0]
sheet_uuid = {k: str(uuid.uuid5(uuid.NAMESPACE_URL, f"mo2-sheet-{k}")) for k in SHEETS}
OUT = {k: Out(f"/{ROOT}/{sheet_uuid[k]}") for k in SHEETS}
nets = {}


def on_seg(p, a, b):
    if a[0] == b[0] == p[0]:
        return min(a[1], b[1]) < p[1] < max(a[1], b[1])
    if a[1] == b[1] == p[1]:
        return min(a[0], b[0]) < p[0] < max(a[0], b[0])
    return False


for sk, O in OUT.items():
    # --- segmentos
    segs, touched = [], set()
    for poly in wires[sk]:
        pts = [P(t) for t in poly]
        for t, p in zip(poly, pts):
            if isinstance(t, str):
                touched.add(t)
        for a, b in zip(pts, pts[1:]):
            if a != b:
                segs.append((a, b))
    special = set()
    for (sh, net, x, y, ang) in xlabels:
        if sh == sk:
            special.add((round(x / 0.635) * 0.635, round(y / 0.635) * 0.635))
    for (sh, net, x, y, o) in xpowers:
        if sh == sk:
            special.add((round(x / 0.635) * 0.635, round(y / 0.635) * 0.635))
    for (sh, x, y) in xflags:
        if sh == sk:
            special.add((round(x / 0.635) * 0.635, round(y / 0.635) * 0.635))
    sheet_comps = [c for c in comps if c["sheet"] == sk]
    pin_pts, pin_own = {}, {}
    for c in sheet_comps:
        for p in c["pl"]:
            pp_ = pinpos(c, p[0])
            pin_pts[pp_] = pin_pts.get(pp_, 0) + 1
            pin_own.setdefault(pp_, set()).add(c["ref"])
    # --- division de segmentos en puntos interiores
    cand = set(pin_pts) | special | {e for s_ in segs for e in s_}
    changed = True
    while changed:
        changed = False
        for i, (a, b) in enumerate(segs):
            for p in cand:
                if on_seg(p, a, b):
                    segs[i] = (a, p)
                    segs.append((p, b))
                    changed = True
                    break
            if changed:
                break
    deg = {}
    for a, b in segs:
        deg[a] = deg.get(a, 0) + 1
        deg[b] = deg.get(b, 0) + 1
    for p, d in deg.items():
        extra = 1 if (p in pin_pts or p in special) else 0
        if d + extra >= 3:
            O.junction(p)
    for a, b in segs:
        O.wire(a, b)
    wired_pts = set(deg)
    # --- simbolos
    for c in sheet_comps:
        X0, Y0, rot = c["x"], c["y"], c["rot"]
        pts = [xf(p[2], p[3], rot) for p in c["pl"]] or [(0, 0)]
        minx, maxx = min(p[0] for p in pts), max(p[0] for p in pts)
        miny, maxy = min(p[1] for p in pts), max(p[1] for p in pts)
        two = len(c["pl"]) == 2
        horiz = two and abs(pts[0][1] - pts[1][1]) < 0.01
        if two and horiz:
            refp, valp = (X0, Y0 - 2.4, False, None, 1.27), (X0, Y0 + 2.7, False, None, 1.27)
        elif two:
            refp, valp = (X0 + 2.0, Y0 - 0.7, False, "left", 1.27), (X0 + 2.0, Y0 + 1.6, False, "left", 1.27)
        elif not c["pl"]:
            refp, valp = (X0, Y0 - 5.08, False, None, 1.27), (X0, Y0 + 5.08, False, None, 1.27)
        elif len(c["pl"]) <= 3 and c["lib"] in ("Transistor_FET", "microohm") and "PMOS" in c["name"] or c["name"] in ("AO3401A", "2N7002"):
            # transistores: texto a un costado
            side = X0 + maxx + 1.6 if rot == 0 else X0 + 2.6
            yy = Y0 - 0.6 if rot == 0 else Y0 + maxy + 2.6
            refp, valp = (side, yy, False, "left", 1.27), (side, yy + 2.2, False, "left", 1.27)
        else:
            bot_pwr = any(c["pins"].get(p[0]) in POWER and xf(p[2], p[3], rot)[1] >= maxy - 0.01 for p in c["pl"])
            yb = Y0 + max(maxy, 2.54) + (7.0 if bot_pwr else 3.2)
            xl = X0 + min(minx, -2.54)
            refp, valp = (xl, yb, False, "left", 1.524), (xl, yb + 2.6, False, "left", 1.27)
        fp_ = c.get("fpos")
        if fp_ == "L":
            refp, valp = (X0 + minx - 1.3, Y0 - 0.6, False, "right", 1.27), (X0 + minx - 1.3, Y0 + 1.7, False, "right", 1.27)
        elif fp_ == "T":
            refp, valp = (X0 + 1.2, Y0 - 3.0, False, "right", 1.27), (X0 + 7.6, Y0 - 3.0, False, "right", 1.27)
        props = [("Reference", c["ref"]) + refp, ("Value", c["value"]) + valp,
                 ("Footprint", c["fp"], X0, Y0, True, None, 1.27), ("Datasheet", c["ds"], X0, Y0, True, None, 1.27),
                 ("Description", c["desc"], X0, Y0, True, None, 1.27)]
        if c["mpn"]:
            props.append(("MPN", c["mpn"], X0, Y0, True, None, 1.27))
        O.symbol(f'{c["lib"]}:{c["name"]}', c["sd"], c["ref"], X0, Y0, rot, sorted({p[0] for p in c["pl"]}), props)
        side = {}
        for num, nam, px, py, pang, unit, etype in c["pl"]:
            net = c["pins"].get(num)
            pp = pinpos(c, num)
            out = int((pang + 180 + rot) % 360)
            if net is None:
                if etype == "no_connect" or c["name"] == "MountingHole":
                    continue
                raise SystemExit(f"Pin sin asignar {c['ref']}.{num}")
            if net == "NC":
                O.noconn(pp)
                continue
            nets.setdefault(net, set()).add(f"{c['ref']}.{num}")
            if pp in wired_pts or pp in special or len(pin_own.get(pp, ())) >= 2:
                continue
            if net in POWER:
                if out in (0, 180):
                    side.setdefault((net, out), []).append(pp)
                else:
                    O.power(net, pp[0], pp[1], out)
            else:
                O.label(net, pp[0], pp[1], out)
        for (net, out), lst in side.items():
            lst.sort(key=lambda p: p[1])
            runs, cur = [], [lst[0]]
            for p in lst[1:]:
                if abs(p[1] - cur[-1][1] - 2.54) < 0.01:
                    cur.append(p)
                else:
                    runs.append(cur)
                    cur = [p]
            runs.append(cur)
            for run in runs:
                stub = 2.54 if (two or len(run) == 1) else 5.08
                sx = run[0][0] + (stub if out == 0 else -stub)
                for p in run:
                    O.wire(p, (sx, p[1]))
                if len(run) == 1:
                    O.power(net, sx, run[0][1], out)
                    continue
                O.wire((sx, run[0][1]), (sx, run[-1][1]))
                for p in run[1:-1]:
                    O.junction((sx, p[1]))
                if net == G:
                    O.junction((sx, run[-1][1]))
                    O.wire((sx, run[-1][1]), (sx, run[-1][1] + 2.54))
                    O.power(net, sx, run[-1][1] + 2.54, 270)
                else:
                    O.junction((sx, run[0][1]))
                    O.wire((sx, run[0][1]), (sx, run[0][1] - 2.54))
                    O.power(net, sx, run[0][1] - 2.54, 90)
    # --- etiquetas, potencia y banderas explicitas
    for (sh, net, x, y, ang) in xlabels:
        if sh == sk:
            O.label(net, round(x / 0.635) * 0.635, round(y / 0.635) * 0.635, ang)
            nets.setdefault(net, set()).add(f"lbl@{sk}")
    for (sh, net, x, y, o) in xpowers:
        if sh == sk:
            O.power(net, x, y, o)
    for i, (sh, x, y) in enumerate(xflags):
        if sh == sk:
            ref = f"#FLG{sk}{i}"
            O.symbol("power:PWR_FLAG", sym("power", "PWR_FLAG"), ref, x, y, 0, ["1"],
                     [("Reference", ref, x, y, True, None, 1.27), ("Value", "PWR_FLAG", x, y - 3.6, False, None, 1.0),
                      ("Footprint", "", x, y, True, None, 1.27), ("Datasheet", "", x, y, True, None, 1.27),
                      ("Description", "", x, y, True, None, 1.27)], inbom=False)
    for (sh, s_, x, y, size, bold, color) in xtexts:
        if sh == sk:
            O.text(s_, x, y, size, bold, color)
    for (sh, x1, y1, x2, y2) in xrects:
        if sh == sk:
            O.add(f'\t(rectangle\n\t\t(start {x1:.2f} {y1:.2f})\n\t\t(end {x2:.2f} {y2:.2f})\n'
                  f'\t\t(stroke (width 0.3) (type dash) (color 120 120 120 1))\n\t\t(fill (type none))\n\t\t(uuid "{uid()}")\n\t)\n')
    fn, title, desc, page = SHEETS[sk]
    BLUE = "0 72 132 1"
    O.text(title, 7 * U, 6 * U, 3.2, True, BLUE)
    O.text(desc, 7 * U, 8.6 * U, 1.6, False, BLUE)
    if _auto[sk]:
        O.text("Componentes de soporte (desacoplo y polarizacion), conectados por etiqueta:", 7 * U, (PST.get(sk, 58) - 2.6) * U, 1.5, True, BLUE)
    O.text("Etiqueta global: [n] = pagina donde continua la senal.", 7 * U, 72 * U, 1.3, False, BLUE)


def tb(title):
    return (f'\t(title_block\n\t\t(title "{title}")\n\t\t(date "2026-11-07")\n\t\t(rev "2.0")\n'
            f'\t\t(company "Universidad Industrial de Santander - E3T")\n'
            f'\t\t(comment 1 "Micro-ohmimetro de precision 1 mOhm - 1 Ohm")\n'
            f'\t\t(comment 2 "E. A. Pacheco J. (2222236) - J. T. Albarracin C. (2220415)")\n'
            f'\t\t(comment 3 "Diseno de Sistemas Electronicos - Prof. Jaime Barrero")\n\t)\n')


def write(path, fuuid, title, body, used, paper="A4", root=False, extra=""):
    libsyms = "".join("\t\t" + dump(sd, 2) + "\n" for sd in used.values())
    s = (f'(kicad_sch\n\t(version 20260306)\n\t(generator "eeschema")\n\t(generator_version "10.0")\n'
         f'\t(uuid "{fuuid}")\n\t(paper "{paper}")\n' + tb(title) + '\t(lib_symbols\n' + libsyms + '\t)\n'
         + "".join(body) + extra)
    if root:
        s += '\t(sheet_instances\n\t\t(path "/"\n\t\t\t(page "1")\n\t\t)\n\t)\n'
    s += '\t(embedded_fonts no)\n)\n'
    with open(path, "w", encoding="utf-8") as f:
        f.write(s)


for k, (fn, title, desc, page) in SHEETS.items():
    write(os.path.join(PROJ, fn), str(uuid.uuid5(uuid.NAMESPACE_URL, f"mo2-file-{k}")), title, OUT[k].b, OUT[k].used)

# ======================================= HOJA RAIZ (A3) =======================================
RB = []


def rtext(s_, x, y, size=1.6, bold=False, color="0 72 132 1", just="left bottom"):
    b = " (thickness 0.35) bold" if bold else ""
    RB.append(f'\t(text "{s_}"\n\t\t(exclude_from_sim no)\n\t\t(at {x:.2f} {y:.2f} 0)\n'
              f'\t\t(effects (font (size {size} {size}){b} (color {color})) (justify {just}))\n\t\t(uuid "{uid()}")\n\t)\n')


def arrow(pts, txt=None, tpos=None, color="200 40 40 1"):
    pl = " ".join(f"(xy {a:.2f} {b:.2f})" for a, b in pts)
    RB.append(f'\t(polyline\n\t\t(pts {pl})\n\t\t(stroke (width 0.6) (type solid) (color {color}))\n\t\t(uuid "{uid()}")\n\t)\n')
    (x1, y1), (x2, y2) = pts[-2], pts[-1]
    a = math.atan2(y2 - y1, x2 - x1)
    L, Wd = 3.0, 1.4
    p1 = (x2 - L * math.cos(a) + Wd * math.sin(a), y2 - L * math.sin(a) - Wd * math.cos(a))
    p2 = (x2 - L * math.cos(a) - Wd * math.sin(a), y2 - L * math.sin(a) + Wd * math.cos(a))
    RB.append(f'\t(polyline\n\t\t(pts (xy {x2:.2f} {y2:.2f}) (xy {p1[0]:.2f} {p1[1]:.2f}) (xy {p2[0]:.2f} {p2[1]:.2f})'
              f' (xy {x2:.2f} {y2:.2f}))\n\t\t(stroke (width 0.3) (type solid) (color {color}))\n'
              f'\t\t(fill (type color) (color {color}))\n\t\t(uuid "{uid()}")\n\t)\n')
    if txt:
        rtext(txt, tpos[0], tpos[1], 1.6, True, color)


POS = {"USB": (20, 60), "CHG": (120, 60), "PWR": (220, 60), "MCU": (320, 60),
       "SRC": (20, 160), "KEL": (120, 160), "ADC": (220, 160), "MEC": (320, 215)}
sheet_blocks = []
for k, (fn, title, desc, page) in SHEETS.items():
    x, y = POS[k]
    w, h = (78, 42) if k != "MEC" else (78, 24)
    sheet_blocks.append(
        f'\t(sheet\n\t\t(at {x} {y})\n\t\t(size {w} {h})\n\t\t(exclude_from_sim no)\n\t\t(in_bom yes)\n\t\t(on_board yes)\n'
        f'\t\t(dnp no)\n\t\t(stroke (width 0.4) (type solid) (color 0 72 132 1))\n\t\t(fill (color 232 241 250 1))\n'
        f'\t\t(uuid "{sheet_uuid[k]}")\n\t\t(property "Sheetname" "{title}"\n\t\t\t(at {x} {y - 0.8} 0)\n'
        f'\t\t\t(effects (font (size 2.2 2.2) bold) (justify left bottom))\n\t\t)\n'
        f'\t\t(property "Sheetfile" "{fn}"\n\t\t\t(at {x} {y + h + 0.8} 0)\n'
        f'\t\t\t(effects (font (size 1.27 1.27) italic) (justify left top))\n\t\t)\n'
        f'\t\t(instances\n\t\t\t(project "{NAME}"\n\t\t\t\t(path "/{ROOT}"\n\t\t\t\t\t(page "{page}")\n\t\t\t\t)\n\t\t\t)\n\t\t)\n\t)\n')
    words, line, yy = desc.split(), "", y + 6
    for wd in words:
        if len(line) + len(wd) > 46:
            rtext(line, x + 2.5, yy, 1.45, color="30 30 30 1")
            line, yy = "", yy + 2.9
        line = (line + " " + wd).strip()
    rtext(line, x + 2.5, yy, 1.45, color="30 30 30 1")
    rtext(f"Pagina {page}", x + w - 2.5, y + h - 2.5, 1.5, True, just="right bottom")

PW_, SG, DG = "200 40 40 1", "20 120 40 1", "120 60 160 1"
arrow([(98, 75), (120, 75)], "VBUS_IN", (100, 73), PW_)
arrow([(198, 75), (220, 75)], "SYS", (205, 73), PW_)
arrow([(170, 102), (170, 125), (8, 125), (8, 181), (20, 181)], "SYS (alimenta OPA388 y P-MOS)", (60, 123), PW_)
arrow([(290, 102), (290, 160)], "+3V3 / AVDD", (292, 135), PW_)
arrow([(98, 175), (120, 175)], "I_PLUS", (101, 173), SG)
arrow([(120, 192), (98, 192)], "INA_OUT", (101, 196), SG)
arrow([(198, 175), (220, 175)], "S+/S-, RS+/RS-", (199, 173), SG)
arrow([(298, 181), (359, 181), (359, 102)], "SPI", (330, 179), DG)
arrow([(340, 102), (340, 150), (88, 150), (88, 160)], "I_OFF / I_LOW (pulso de 2 niveles)", (150, 148), DG)
arrow([(320, 92), (308, 92), (308, 50), (190, 50), (190, 60)], "I2C + BQ_INT", (230, 48), DG)
arrow([(190, 50), (85, 50), (85, 60)], None, None, DG)
arrow([(390, 60), (390, 38), (92, 38), (92, 60)], "USB D+/D- (programacion y consola)", (200, 36), DG)
rtext("Micro-ohmimetro de precision 1 mOhm - 1 Ohm  |  Diagrama de bloques y flujo de senales (v2)", 20, 22, 4, True)
rtext("Rojo: potencia     Verde: senal de medicion     Morado: control digital.     Cada bloque es una hoja (doble clic para abrirla).",
      20, 29, 1.9)
rtext("R_DUT = RS * (V_DUT,H - V_DUT,L) / (V_RS,H - V_RS,L)     (medicion ratiometrica de 2 niveles)", 20, 222, 2.4, True, PW_)
rtext("I_H = V_REF / (G_INA * RS) = 2,5 / (20 * 0,12) = 1,042 A     I_L = 0,502 A     Pulso: 120 ms cada 1 s", 20, 229, 2.0)
rtext("Referencias numeradas por hoja: R4xx = pagina 5 (fuente), C6xx = pagina 7 (ADC), etc.", 20, 236, 1.8)
write(os.path.join(PROJ, f"{NAME}.kicad_sch"), ROOT, "Micro-ohmimetro v2 - Diagrama general", RB, {}, paper="A3",
      root=True, extra="".join(sheet_blocks))

with open(os.path.join(PROJ, "netlist_resumen.txt"), "w", encoding="utf-8") as f:
    for n in sorted(nets):
        f.write(f"{n}{' (global)' if n in GLOBAL else ''}: {' '.join(sorted(nets[n]))}\n")
print(f"OK componentes={len(comps)} redes={len(nets)} globales={len(GLOBAL)}")
