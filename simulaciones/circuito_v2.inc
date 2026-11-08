* ==========================================================================
* Micro-ohmimetro v2 - fuente de corriente pulsada de 2 niveles + red Kelvin
* Uso: .INC "circuito_v2.inc" desde cada archivo de analisis.
* Modelos: OPA4388 e INA181A1 = modelos PSpice oficiales de TI.
*          REF3325 = fuente de 2,5 V con tolerancia (RREF con DEV).
*          Q2 = P-MOS equivalente (VTO=-1,6 V, tipico NTD25P03L).
* Parametros esperados desde el archivo principal:
*   RDUT, VSYS, VOS_OPA, VEMF
* ==========================================================================
.LIB "modelos/opa4388_pspice/OPA4388.LIB"
.LIB "modelos/ina181a1_pspice/ina181a1.lib"
.LIB "C:/Cadence/SPB_22.1/tools/pspice/library/phil_diode.lib"

* ---- Alimentaciones -------------------------------------------------------
V_SYS  SYS 0 {VSYS}
V_VDD  VDD 0 3.3

* ---- REF3325: 2,5 V +/-0,15 % (DEV en RREF) --------------------------------
I_REF  0 NREF0 1m
R_REF  NREF0 0 RREFMOD 2.5k
E_REF  VREF 0 NREF0 0 1
.MODEL RREFMOD RES(R=1 DEV=0.15%)

* ---- Nodo VSET: 10k + 100n (arranque suave); Q5 fija el nivel I_L ---------
R_VSET VREF VSET RTF01 10k
C_VSET VSET 0 22n
* Q5 (nivel bajo): conmuta 9,31k a GND cuando LOWCTL=1 V
S_LOW  VSET NIL LOWCTL 0 SWMOD
R_IL   NIL 0 RTK1 9.31k
* Q3 (apagado seguro): cortocircuita VSET cuando OFFCTL=1 V
S_OFF  VSET 0 OFFCTL 0 SWMOD
.MODEL SWMOD VSWITCH(RON=2 ROFF=1G VON=0.6 VOFF=0.4)

* ---- Lazo: OPA388 (alimentado desde SYS) ------------------------------------
* IN+ = salida INA181 (realimentacion), IN- = VSET via integrador
V_OS   INAOUT NINP {VOS_OPA}
R_INT  VSET NINN RTF01 10k
C_INT  NOUT NINN 10n
X_U4   NINP NINN SYS 0 NOUT OPA4388
R_G    NOUT GATE RTK1 100
R_GPU  GATE SYS RTK1 100k

* ---- Q2: P-MOS de paso (S=SYS, D=IPLUS) ------------------------------------
M_Q2   IPLUS GATE SYS SYS PMOSEQ
.MODEL PMOSEQ PMOS(LEVEL=1 VTO=-1.6 KP=5.9 W=1 L=1 LAMBDA=0.01 CGSO=1.1n CGDO=0.25n RD=10m RS=5m)

* ---- Red Kelvin: cables de fuerza (20 mOhm c/u) y DUT ----------------------
R_LFP  IPLUS DUT_T 20m
R_DUT  DUT_T DUT_B {RDUT}
R_LFN  DUT_B IMINUS 20m
* Cables de sensado (100 mOhm c/u) + FEM termoelectrica en S+
V_EMF  DUT_T NSP0 {VEMF}
R_LSP  NSP0 SP 100m
R_LSN  DUT_B SN 100m

* ---- RS (Kelvin, 4 terminales) y R_LIFT ------------------------------------
R_RS   IMINUS NLIFT RSMOD 0.12
R_LIFT NLIFT 0 RLMOD 0.68
.MODEL RSMOD RES(R=1 DEV=1%)
.MODEL RLMOD RES(R=1 DEV=1%)

* ---- INA181A1: sensa RS ----------------------------------------------------
X_U3   IMINUS NLIFT VDD 0 0 INAOUT INA181A1

* ---- Entrada AD7124 canal DUT: 1k + 1nF (MC) + 10nF dif + BAT54S ---------
R_FP   SP AIN0 RTF01 1k
R_FN   SN AIN1 RTF01 1k
C_CP   AIN0 0 1n
C_CN   AIN1 0 1n
C_DIF  AIN0 AIN1 10n
X_D3   0 VDD AIN0 BAT54S/PLP
X_D4   0 VDD AIN1 BAT54S/PLP
* Carga del ADC con buffers (1 nA tipico)
I_B0   AIN0 0 1n
I_B1   AIN1 0 1n

* ---- Entrada AD7124 canal RS: 100 ohm por linea ----------------------------
R_RP   IMINUS AIN2 RTF01 100
R_RN   NLIFT  AIN3 RTF01 100
C_RP   AIN2 0 1n
C_RN   AIN3 0 1n

.MODEL RTF01 RES(R=1 DEV=0.1%)
.MODEL RTK1  RES(R=1 DEV=1%)
