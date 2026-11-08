# B1 — Diseño detallado v2 del micro-ohmímetro (1 mΩ – 1 Ω)

Base: las 19 correcciones del docente aprobadas el 2026-11-07.
Las marcas **[VERIFICAR B3]** son datos que se confirman contra el datasheet cuando se capture el esquemático.

---

## 1. Arquitectura v2

```
USB-C 24p ─ TVS ─ STUSB4500 (PD sink 9 V/2 A) ─ P-MOS VBUS ─ BQ25895 (buck 1,5 MHz) ─┬─ SYS (3,5–4,35 V)
                                                                                     │
LiPo 1S 2000 mAh ─ JST XH SMD ─ P-MOS polaridad ─ BAT ─┘                              │
                                                                                     ├─ Fuente de corriente pulsada 1,04 A
                                                                                     └─ AP2112K-3.3 ─ VDD 3,3 V ─┬─ ESP32-C3-MINI-1
                                                                                                                 ├─ ferrita ─ AVDD: AD7124-4
                                                                                                                 └─ REF3325, INA181A1
```

**Cadena de medición:**
- SYS → P-MOSFET (Q2) → banana I+ → DUT → banana I− → RS 120 mΩ (Kelvin) → GND.
- Los bananas S+/S− van por un filtro RC a AIN0/AIN1 del AD7124 (PGA de 128/16/2, buffers activados).
- Los terminales de sensado de RS van a AIN2/AIN3 (G = 1, sin buffer).
- El cálculo es **R_DUT = RS · V_DUT / V_RS**: es ratiométrico, así que se cancelan la referencia, la ganancia del INA y el valor exacto de la corriente.

---

## 2. Fuente de corriente pulsada (correcciones 3, 4 y 5)

| Elemento | Selección | Dato verificado |
|---|---|---|
| Referencia | **REF3325AIDBZR** (2,5 V, SOT-23-3) | ±0,15 % inicial, 30 ppm/°C, 3,9 µA, IOUT ±5 mA, dropout 110 mV |
| Sensado | **INA181A1IDBVR** (20 V/V, SOT-23-6) | VOS ±150 µV máx., EG ±0,1 % típ., VCM −0,2 a 26 V, BW 350 kHz, IQ 260 µA máx. |
| Lazo | **OPA388IDBVR** (SOT-23-5), alimentado desde SYS | Zero-drift, VOS 5 µV máx., GBW 10 MHz, alimentación de hasta 5,5 V |
| Paso | **NTD25P03LT4G** (P-MOS, −30 V, −25 A, DPAK, VGS(th) típ. −1,6 V) | SOA a 100 ms y VGS(th) máx. **[VERIFICAR B3]** |
| RS | Shunt de **0,12 Ω, 1 %, 4 terminales, 2512, ≥ 1 W, TCR ≤ 50 ppm/°C** (familia Vishay WSK2512) | MPN exacto **[VERIFICAR B3]** |

**Ecuación:** I = V_REF / (G_INA · RS) = 2,5 / (20 · 0,12) = **1,042 A**, con V_RS = 125 mV.
(RS pasa de 125 a 120 mΩ porque 0,12 Ω es un valor comercial; la caída sobre RS sigue siendo 125 mV.)

**Polaridad del lazo:** la salida del INA181 va a IN+ del OPA388 y VSET a IN−. Si la corriente sube, también sube la tensión de gate y el P-MOS conduce menos. Con VSET = 0, la gate queda en SYS y el P-MOS se apaga.

**Componentes del lazo:**
- Resistencia de gate: 100 Ω.
- Pull-up de gate a SYS: 100 kΩ, para que el P-MOS quede apagado si el OPA388 no está alimentado.
- Compensación: integrador con 10 kΩ y 10 nF C0G. Los valores finales salen de la simulación transitoria de B2.

**Pulso (I_OFF):**
- REF3325 → 10 kΩ → nodo VSET, con **22 nF** C0G a GND. La constante de tiempo de 0,22 ms hace de arranque suave y limita di/dt; el asentamiento al 0,01 % es de 3,3 ms (validado en B2).
- Un 2N7002 entre VSET y GND, con la gate en GPIO0 a través de 1 kΩ y un pull-up de 100 kΩ a VDD.
- **Al arrancar, el 2N7002 conduce y la corriente queda apagada (estado seguro).** El firmware pone GPIO0 en bajo para habilitar la corriente.
- Carga sobre la REF cuando VSET está a tierra: 2,5 V / 10 kΩ = 0,25 mA (el límite es 5 mA).

**Margen de tensión (peor caso: RDUT = 1 Ω y batería en el corte de 3,5 V):**
3,5 − 0,10 (P-MOS de polaridad a 1 A) − 1,042 (DUT) − 0,125 (RS) = **2,23 V disponibles para el P-MOS**, más que suficiente.

**Térmica (peor caso: RDUT ≈ 0 y SYS = 4,35 V):**
- Durante el pulso, VDS ≈ 4,35 − 0,1 − 0,125 ≈ 4,1 V, así que P ≈ **4,3 W**.
- Pulso de **120 ms cada 1 s** (12 %): la potencia media es de 0,51 W.
- Con RθJA ≈ 50 °C/W (DPAK con unos 4 cm² de cobre y vías), ΔT medio ≈ +26 °C.
- El pico dentro del pulso se acota con la ZθJC del datasheet **[VERIFICAR B3]**.

**R_LIFT = 0,68 Ω** (1 %, *thick film*, 2512 de 1 W) entre RS y GND. Su función es solo elevar el modo común (ver sección 3). Su precisión no importa. En el pulso disipa 0,74 W, con una media de 0,09 W.

**Corriente de dos niveles** (reemplaza la lectura con corriente apagada; ver la nota de la sección 3):
- **I_H = 1,042 A**, con VSET = 2,5 V.
- **I_L = 0,502 A**, con VSET = 1,205 V. Se obtiene con un 2N7002 (Q5, en GPIO3) que conecta 9,31 kΩ de VSET a GND, formando 10 kΩ / 9,31 kΩ.
- El valor exacto de I_L **no afecta el resultado**, porque V_RS se mide en los dos niveles. La referencia sigue siendo la REF3325.

**Secuencia por medición (unos 240 ms):**
1. Nivel I_L: 5 ms de asentamiento, luego una conversión de V_DUT y otra de V_RS.
2. Nivel I_H: lo mismo.
3. Corriente apagada.

Así **R = RS · (V_DUT,H − V_DUT,L) / (V_RS,H − V_RS,L)**. El offset del ADC y la FEM termoeléctrica son iguales en ambos niveles, así que se cancelan. ΔI = 0,54 A.

**Margen de tensión corregido** (1 Ω, batería en 3,5 V): 3,5 − 0,1 − 1,042 − 1,042·(0,12 + 0,68) = **1,52 V disponibles** para el P-MOS.

**Térmica corregida:** VDS,máx ≈ 4,35 − 0,1 − 0,83 = 3,4 V, así que el pico es de **3,5 W** y la media de 0,43 W (≈ +22 °C).

---

## 3. Entrada al AD7124-4 (corrección 10)

| Canal | Entradas | Setup | Rango | Uso |
|---|---|---|---|---|
| CH0 | AIN0 = S+, AIN1 = S− | G = 128, bipolar, buffers activados | ±19,5 mV | R ≤ 15 mΩ |
| CH1 | AIN0/AIN1 | G = 16, bipolar, buffers activados | ±156 mV | R ≤ 120 mΩ |
| CH2 | AIN0/AIN1 | G = 2, bipolar, buffers activados | ±1,25 V | R ≤ 1 Ω |
| CH3 | AIN2 = RS_S+, AIN3 = RS_S− | **G = 16**, bipolar, con buffers | ±156 mV | V_RS = 60 / 125 mV |

**Modo común (verificado en el datasheet del AD7124-4, Rev. E, notas 8 y 11):**
- Con G > 1 los buffers se activan solos.
- Cada pin debe estar entre AVSS + 0,1 y AVDD − 0,1 V.
- **El modo común debe estar entre AVSS + 0,1 + 0,5/G y AVDD − 0,1 − 0,5/G**: para G = 2, 0,35 V como mínimo; para G = 16, 0,131 V; para G = 128, 0,104 V.

**Por qué cambió:** en la versión inicial, con S− = 0,125 V, el canal de G = 2 tenía un modo común de 0,19 V (por debajo de 0,35 ✗). Además, con la corriente apagada el modo común era 0 V en todos los canales ✗. **R_LIFT** y la **corriente de dos niveles** lo resuelven:

| Estado | S− (V) | Modo común mínimo de DUT (V) | Modo común de RS (V) | Cumple G = 2 / 16 / 128 |
|---|---|---|---|---|
| I_L = 0,502 A | 0,401 | 0,40 | 0,37 | ✓ / ✓ / ✓ |
| I_H = 1,042 A | 0,833 | 0,83 | 0,77 | ✓ / ✓ / ✓ |
| S+ máximo (1 Ω, I_H) | 1,875 | — | — | Por debajo de 3,2 − 0,25 ✓ |

**Señal útil:** ΔI · R_DUT = 0,54 mV con 1 mΩ. El ruido con G = 128 es de ≈ 0,06 µV rms (Tabla 8 del datasheet: 0,063 µV a 40 SPS), así que la resolución es ≈ **0,011 % por lectura**.

**Filtro y protección por línea S±:**
- 1 kΩ en serie, 1 nF C0G a GND en cada línea y 10 nF C0G diferencial.
- Frecuencia de corte diferencial ≈ 7,6 kHz.
- Doble diodo **BAT54S** hacia AVDD y GND.
- Ajuste al punto 10 aprobado: la resistencia en serie sube de 100 Ω a 1 kΩ, porque con el DUT abierto S+ sube hasta SYS (4,35 V). Con 1 kΩ la corriente por el clamp queda por debajo de 1 mA.
- La corriente de bias con buffer (del orden de nA) × 1 kΩ da un offset de µV, que se cancela con la resta ON–OFF.

**Detección de DUT abierto:** si V_RS ≈ 0 con la corriente encendida, el firmware reporta "DUT ABIERTO".


**Referencia:** la interna de 2,5 V con REFOUT y 100 nF. Se hace la calibración interna de offset y de fondo de escala por cada setup, más una calibración de sistema con una resistencia patrón.

---

## 4. Energía (correcciones 1, 8 y 9)

### 4.1 USB-C PD
- **J3:** USB-C de 24 pines y 5 A, SMD con pestañas de carcasa pasantes.
- **TVS SMBJ12A** en VBUS.
- **STUSB4500** (sink PD autónomo con NVM):
  - PDO1 = 5 V / 3 A;
  - **PDO2 = 9 V / 2 A** (preferido).
  - **Verificado en el datasheet (DS12499 Rev. 8):**
    - VBUS soporta hasta 28 V.
    - Las terminaciones de pull-down de CC son internas, así que **se eliminan R15/R16**.
    - Se alimenta desde VDD = VBUS, con soporte de batería muerta: CC1DB a CC1 y CC2DB a CC2.
    - VBUS_EN_SNK es de alta tensión, en drenador abierto, y maneja un P-MOS directamente.
    - Con POWER_ONLY_ABOVE_5V, VBUS_EN_SNK solo se activa con contrato PDO2/PDO3.
    - ADDR0/ADDR1 van a GND si no hay MCU. Aquí se dejan en I²C, compartiendo el bus con el BQ25895, para leer el estado.
  - Los valores de los capacitores de VREG_1V2, VREG_2V7 y VDD se toman de la sección 6 del datasheet en B3.
- **Interruptor de VBUS:** P-MOS AO3401A (−30 V; VGS = −9 V, dentro del máximo de ±12 V), controlado por VBUS_EN_SNK.

### 4.2 Cargador BQ25895RTWR (verificado contra el datasheet)
| Parámetro | Valor |
|---|---|
| VBUS de operación / máximo absoluto | 3,9–14 V / 22 V |
| Conmutación | 1,5 MHz, inductor de **2,2 µH** con Isat ≥ 3,5 A y DCR ≤ 20 mΩ |
| ICHG | **2048 mA** (1C) por I²C, REG04 |
| Límite de entrada | ILIM: IINMAX = KILIM / RILIM, KILIM = 355 típ. → **RILIM = 178 Ω → 2,0 A** |
| Temporizador de seguridad | **Desactivado** (EN_TIMER = 0), según "velocidad sobre protecciones" |
| NTC | 10 kΩ SMD (B ≈ 3380–3435) junto a la batería; **RT1 = 5,23 kΩ, RT2 = 30,1 kΩ** (valores del datasheet) |
| Capacitores | VBUS 1 µF/25 V · PMID ≥ 8,2 µF (2 × 10 µF/25 V) · SYS 20 µF (2 × 10 µF/10 V) · BAT 10 µF · REGN 4,7 µF/10 V · BTST 47 nF |
| I²C | Dirección 0x6A; SDA en GPIO4, SCL en GPIO8; pull-ups de 10 kΩ a VDD |
| CE / OTG / QON | CE a GND (carga habilitada) · OTG a GND (sin boost) · QON libre (pull-up interno) |
| INT | Va a GPIO1, con pull-up de 10 kΩ |
| ADC interno | Mide VBAT, VSYS, VBUS e ICHG, así que **se elimina el divisor de batería** |
| BATFET | RON = 11 mΩ típ. |

**Tiempo de carga:** unos **1,0 h en CC + 0,4 h en CV ≈ 1,4–1,5 h** para 2000 mAh, frente a más de 5 h con el BQ24072.

### 4.3 Polaridad inversa de la batería
- P-MOS en serie con BAT+, con la gate a GND por 100 kΩ.
- A 2 A de carga, el AO3401A (RDS(on) ≈ 85 mΩ máx. a −2,5 V) disiparía 0,34 W y caería 0,17 V, lo que adelanta el fin de carga en CV.
- Por eso se usa un **P-MOS en DFN 3 × 3 con RDS(on) ≤ 20 mΩ a VGS = −2,5 V** (candidato AON7403) **[VERIFICAR B3]**. El AO3401A queda solo para el interruptor de VBUS.

### 4.4 Regulación a 3,3 V
- **AP2112K-3.3** desde SYS (600 mA; carga real de unos 350 mA de pico con Wi-Fi durante la OTA).
- Corte de batería en firmware a **3,5 V**, para mantener la regulación.
- **AVDD del AD7124** a través de una ferrita de 600 Ω a 100 MHz, con 10 µF + 100 nF.

### 4.5 Batería
LiPo 1S de **2000 mAh, unos 8 × 50 × 60 mm, descarga ≥ 2C**, conector **JST XH SMD S2B-XH-SM4-TB**.

---

## 5. MCU ESP32-C3-MINI-1-N4 (correcciones 6, 7 y 10)

| GPIO | Función | Nota |
|---|---|---|
| 0 | I_OFF (pulso de corriente) | Pull-up externo de 100 kΩ en la gate del 2N7002 → corriente apagada al arrancar |
| 1 | INT del BQ25895 | Pull-up de 10 kΩ |
| 3 | I_LOW (nivel I_L, mediante Q5) | 100 kΩ a GND en la gate: nivel I_H por defecto (la corriente sigue apagada mientras I_OFF esté activo) |
| 4 / 8 | I²C SDA / SCL | GPIO8 es pin de strapping: el pull-up de 10 kΩ lo mantiene en alto, como exige |
| 5 / 6 / 7 / 10 | SPI MISO (DOUT/RDY) / SCLK / MOSI / CS | SPI modo 3; CS con pull-up de 10 kΩ |
| 9 | BOOT | Pulsador a GND y pull-up de 10 kΩ |
| 18 / 19 | USB D− / D+ | Protegidos con el USBLC6-2SC6 |
| 20 / 21 | RX0 / TX0 | Solo test pads |
| 2 | LED de estado, activo en bajo (LED + 1 kΩ hacia VDD) | Pin de strapping: el LED lo mantiene en alto al arrancar |
| EN | RC de 10 kΩ + 1 µF y pulsador RESET | Recomendación de Espressif |

**OTA:** particiones con dos apps OTA + NVS (4 MB). El comando BLE `OTA` activa el modo de mantenimiento por Wi-Fi (ArduinoOTA). Hay *rollback* si el AD7124 no responde con su ID.

---

## 6. Presupuesto energético (sobre SYS)

| Bloque | Corriente media | Base |
|---|---|---|
| Pulso de 1,042 A × 12 % | 125 mA | Diseño |
| ESP32-C3 con BLE conectado | 30–45 mA | Estimado, **se mide** |
| AD7124-4 a potencia completa | 0,93 mA | Datasheet |
| OPA388 + INA181 + REF3325 | ≈ 2,2 mA | Datasheet |
| AP2112 IQ + pull-ups + LED | ≈ 1–3 mA | Estimado |
| **Total midiendo** | **≈ 160–175 mA** | **Autonomía ≈ 10–11 h** (2000 mAh × 0,9) |
| **Total en reposo** (BLE sin medir) | ≈ 35–50 mA | ≈ 36–50 h |

---

## 7. Cambios respecto a lo aprobado (para que quede trazable)
1. **RS:** de 125 mΩ a **120 mΩ**, por ser valor comercial. I = 1,042 A y V_RS sigue en 125 mV.
2. **Resistencias de entrada S±:** de 100 Ω a **1 kΩ**, para limitar la corriente por el clamp cuando el DUT está abierto.
3. **Alimentación de la fuente de corriente:** sale de **SYS** del BQ25895, que tiene power-path, y no directo de VBAT. Así, mientras se carga, los pulsos los entrega el adaptador.
4. **Polaridad inversa:** un P-MOS de RDS(on) bajo en DFN para 2 A de carga. El AO3401A pasa al interruptor de VBUS.
5. **Divisor de batería y CHARGING_STATUS:** se eliminan. Ese dato lo entrega el BQ25895 por I²C.
6. **R_LIFT de 0,68 Ω y corriente de dos niveles (1,042 / 0,502 A):** reemplazan la lectura con corriente apagada del punto 5. Son necesarios por el límite de modo común del PGA (notas 8 y 11 del datasheet). La cancelación de offset y FEM se mantiene.
7. **Canal de RS:** pasa a G = 16 con buffers. Ya es posible porque AIN3 queda en ≈ 0,34 V o más.
8. **STUSB4500:** las terminaciones Rd son internas (verificado), así que se eliminan R15/R16 de 5,1 kΩ.
