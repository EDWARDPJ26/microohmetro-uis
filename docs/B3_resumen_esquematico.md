# B3 — Esquemático KiCad v2 (versión 2: jerárquica y cableada)

**Proyecto:** `microohmetro_v2.kicad_pro` (KiCad 10.0.6). **Esquemático jerárquico de 9 páginas:**

| Página | Archivo | Contenido |
|---|---|---|
| 1 (A3) | `microohmetro_v2.kicad_sch` | **Diagrama de bloques y flujo de señales**, con flechas por color: rojo para potencia, verde para medición y morado para control |
| 2 | `1_usb_pd.kicad_sch` | USB-C, STUSB4500, interruptor de VBUS y ESD |
| 3 | `2_cargador.kicad_sch` | BQ25895, inductor, SYS, polaridad inversa, LiPo y NTC |
| 4 | `3_regulacion.kicad_sch` | AP2112K-3.3 y ferrita AVDD |
| 5 | `4_fuente_corriente.kicad_sch` | REF3325 → VSET → OPA388 → P-MOS (I_PLUS) |
| 6 | `5_kelvin_shunt.kicad_sch` | Bananas, DUT, RS de 4 terminales, R_LIFT e INA181 |
| 7 | `6_adc.kicad_sch` | AD7124-4 con filtros, clamps y desacoplos |
| 8 | `7_mcu.kicad_sch` | ESP32-C3 con EN/BOOT/RESET |
| 9 | `8_mecanicos.kicad_sch` | Puntos de prueba y agujeros M3 |

**Criterios de legibilidad aplicados**
- La **cadena principal de cada bloque va cableada pin a pin**, con uniones automáticas.
- Las **etiquetas globales** se usan solo para las señales que pasan a otra hoja, y muestran la referencia de página `[n]`.
- Los componentes de soporte (desacoplos y pull-ups) van en una fila inferior, conectados por etiqueta.
- Las **referencias están numeradas por hoja** (R4xx = página 5), lo que facilita la trazabilidad.
- Las referencias y valores se ubican sin solaparse, y los GND/+3V3 laterales se agrupan en un único símbolo.

**Generado por script** (`gen/gen_sch3.py`), así que es reproducible.
**Exportados:** `../imagenes/esquematico_v2.pdf` (9 páginas vectoriales), un SVG por hoja, `microohmetro_v2.net` y `../imagenes/bom_kicad.csv`.

## Verificación
| Prueba | Resultado |
|---|---|
| ERC (`kicad-cli sch erc`) | **0 errores**, 6 advertencias benignas (PWR_FLAG de GND frente a pines bidireccionales del AD7124 atados a GND) |
| **Netlist exportada frente a netlist de diseño** | **60 de 60 redes idénticas** (comparación automática pin a pin) |
| Componentes / redes | 103 / 60, sin redes de un solo pin |
| Footprints | **27 de 27 existen** en las librerías oficiales de KiCad 10 |
| Modelos 3D | 23 de 27 disponibles. Faltan el JST XH SM4 (no existe en la librería) y el WSK2512 de 4 terminales: se resuelven en B4. Los agujeros y los TP no llevan 3D |

## Símbolos propios (`Librerias/microohm.kicad_sym`)
- **AD7124-4BBCPZ:** 33 pines, con la numeración LFCSP-32 **verificada en la tabla 7 del datasheet Rev. E**. Así se corrige el error del diseño anterior, que usaba un símbolo de 16 pines sobre un footprint de 33 pads.
- **Q_PMOS_GDS_DPAK:** numeración 1 = G, 2 = D (tab), 3 = S, igual que el footprint TO-252-2.

## Cambios respecto a B1 (para que queden trazables)
| # | Cambio | Motivo |
|---|---|---|
| 1 | **ESP32-C3-WROOM-02-N4** en lugar del C3-MINI-1 | Mismo chip ESP32-C3, activo, con USB nativo en IO18/IO19. **Está en la librería oficial de KiCad, con footprint y 3D verificados**; el MINI-1 no está. El módulo es unos 5 mm más grande |
| 2 | Bananas **Cliff FCR7350 R/B/Y/L** (4 mm, PCB) en lugar de Keystone 575-4 | Están en la librería de KiCad con 3D y en los colores pedidos (rojo, negro, amarillo, azul) |
| 3 | Batería con **JST XH S3B-XH-SM4-TB (3 pines: BAT+, NTC, BAT−)** | No existe el SMD de 2 pines en la librería. El de 3 pines aprovecha la NTC que traen muchas LiPo (TH1 se deja DNP en ese caso) |
| 4 | Polaridad inversa con **2 × AO3401A en paralelo** (≈ 43 mΩ) | A 2 A disipan 0,17 W en total. Son componentes de librería con 3D, en lugar del AON7403 sin footprint |
| 5 | **VSYS del STUSB4500 a +3V3** | Según el datasheet, SCL/SDA se van a 0 si no hay VDD ni VSYS. Sin este cambio, con el USB desconectado el bus I²C del BQ25895 quedaría bloqueado |
| 6 | **VBUS del USBLC6-2SC6 a +3V3** | Su VBUS admite ≤ 6 V, y con PD a 9 V se dañaría |
| 7 | AD7124: **SYNC a +3V3, CLK a GND** (reloj interno) y AIN4–AIN7 a GND | SYNC en bajo detendría las conversiones |
| 8 | BQ25895: **D+/D−/DSEL sin conexión** | La detección BC1.2 se deshabilita por I²C (AUTO_DPDM_EN = 0), porque el contrato lo negocia el STUSB4500 |
| 9 | OPA388 con el símbolo `OPA333xxDBV` y REF3325 con el símbolo `REF3025` | Pinout DBV/DBZ idéntico, verificado contra las tablas de pines de los datasheets |

## Pendientes antes de fabricar (se verifican en B4)
- EP del LFCSP-32 (CP-32-30): se usa 3,6 × 3,6 mm. **Hay que confirmarlo contra el plano de ADI.**
- MPN y corriente del USB-C Amphenol 12401610E4#2A (5 A).
- Conexión de VBUS_VS_DISCH y DISCH del STUSB4500, según la nota de aplicación de ST.
