# B2 — Simulaciones PSpice del diseño v2

Herramienta: **Cadence PSpice 22.1** (`psp_cmd.exe`, en batch).
Circuito común: [`circuito_v2.inc`](circuito_v2.inc).
Datos exportados: [`datos/`](datos/), en CSV para graficar con pgfplots en el informe.

## Modelos usados
| Bloque | Modelo | Origen |
|---|---|---|
| OPA388 (lazo) | `OPA4388` (Rev. B, SBOMAZ6B) | **Oficial de TI** (es el mismo silicio que el OPA388) |
| INA181A1 | `INA181A1` (SBOMBB7) | **Oficial de TI** |
| REF3325 | Fuente de 2,5 V con tolerancia de ±0,15 % (DEV en R_REF) | Comportamental; datos del datasheet |
| Q2 (P-MOS de paso) | MOS nivel 1 equivalente: VTO = −1,6 V, Ciss ≈ 1,35 nF | Equivalente con los parámetros típicos del NTD25P03L |
| BAT54S | `BAT54S/PLP` | Librería de PSpice (NXP) |
| Q3/Q5 (2N7002) | Interruptor controlado por tensión (RON = 2 Ω) | Simplificación: solo conmutan nodos de alta impedancia |
| AD7124-4 | Carga de 1 nA por entrada (con buffers) | No existe modelo SPICE; su error se suma analíticamente en el presupuesto |

Cables de prueba simulados: **20 mΩ** en cada cable de fuerza y **100 mΩ** en cada cable de sensado. Así se verifica que la medición Kelvin no depende de ellos.

---

## S1 — Niveles DC y medición ratiométrica ([datos](datos/))
Archivos: `S1_niveles_VSYS3p5.cir` y `S1_niveles_VSYS4p35.cir` (secuencia I_L → I_H, muestreo al final de cada nivel).

| RDUT | I_L (A) | I_H (A) | R medida | Error | S− en I_L (V) | S+ en I_H (V) |
|---|---|---|---|---|---|---|
| 1 mΩ | 0,50233 | 1,04181 | 0,99995 mΩ | −0,0054 % | 0,412 | 0,855 |
| 10 mΩ | 0,50233 | 1,04181 | 9,9995 mΩ | −0,0054 % | 0,412 | 0,865 |
| 100 mΩ | 0,50233 | 1,04181 | 99,995 mΩ | −0,0054 % | 0,412 | 0,959 |
| 1 Ω | 0,50233 | 1,04181 | 0,99995 Ω | −0,0054 % | 0,412 | 1,896 |

- El resultado es **idéntico con SYS = 3,5 V y con SYS = 4,35 V**, así que es inmune a la tensión de la batería.
- El error de −0,0054 % es **constante**: es un error de ganancia sistemático, que se elimina con la calibración de sistema. Lo causa la corriente de polarización del INA181, que no pasa por RS.
- **Modo común** en el peor caso: S− = 0,412 V, por encima de 0,35 V (el mínimo del AD7124 con G = 2). S+ máximo = 1,90 V, por debajo de 2,95 V. ✓
- **Gate en el peor caso** (1 Ω, SYS = 3,5 V): 1,31 V, es decir VGS = −2,2 V, con margen. ✓

## S2 — Estabilidad del lazo ([`datos/S2_corriente.csv`](datos/S2_corriente.csv))
Escalón de I_L a I_H a los 12 ms y apagado a los 20 ms.

| RDUT | I final | Sobrepico | Asentamiento al 0,01 % |
|---|---|---|---|
| 1 mΩ | 1,04181 A | **0 %** | 3,32 ms |
| 1 Ω | 1,04181 A | **0 %** | 3,32 ms |

El lazo es estable y sin oscilación. El asentamiento lo fija el arranque suave de VSET: 10 kΩ y 22 nF (se bajó de 100 nF a 22 nF). **El firmware espera 5 ms** antes de convertir.

## S3 — Offset del OPA388 y FEM termoeléctrica (RDUT = 1 mΩ)
Archivos: `S3_offset_VOS5u.cir` y `S3_offset_VOSm5u.cir`.

| VOS del OPA388 | FEM en S+ | Error con 2 niveles | Error con 1 nivel |
|---|---|---|---|
| ±5 µV | −10 µV | **−0,0054 %** | +0,954 % |
| ±5 µV | 0 | **−0,0054 %** | −0,005 % |
| ±5 µV | +10 µV | **−0,0054 %** | −0,965 % |

- **El offset del OPA388 no influye**, porque la medición es ratiométrica. Lo mismo vale para el VOS de 45 µV del OPA391, que era lo que objetaba el docente.
- **Una FEM de ±10 µV daría ±0,96 % de error** midiendo con un solo nivel. **Con dos niveles se cancela por completo.**

## S4 — Montecarlo (300 corridas, distribución uniforme) ([`datos/MC_resumen.csv`](datos/MC_resumen.csv))
Tolerancias:
- RS ±1 % (o ±0,1 %);
- R_LIFT ±1 %;
- REF ±0,15 %;
- resistencias *thin film* ±0,1 %;
- resistencias *thick film* ±1 %.

| Caso | Corridas válidas | Media | σ | Rango | ±3σ |
|---|---|---|---|---|---|
| **v2**, RDUT = 1 mΩ, RS 1 % | 283 | +0,025 % | 0,57 % | −0,99 … +0,99 % | 1,72 % |
| **v2**, RDUT = 1 Ω, RS 1 % | 271 | +0,022 % | 0,56 % | −0,98 … +0,99 % | 1,68 % |
| **v2**, RDUT = 1 mΩ, **RS 0,1 %** | 286 | −0,001 % | **0,057 %** | −0,11 … +0,09 % | 0,17 % |
| **Diseño anterior** (amplificador diferencial con R al 1 %), RDUT = 10 mΩ | 299 | +5,7 % | **87,8 %** | −100 … +284 % | 263 % |

- En el diseño v2, la dispersión **coincide con la de una sola resistencia, RS** (una distribución uniforme de ±1 % tiene σ = 0,577 %). La REF, el INA181, el OPA388 y R_LIFT **se cancelan en la relación**.
- **El diseño anterior era inviable**: con resistencias del 1 % y un modo común de 3,2 V, el error de CMRR supera al propio valor medido. Esto justifica el cambio al PGA del AD7124 (corrección 10).
- Algunas corridas del v2 no convergieron en el arranque transitorio (UIC, t ≈ 3,6 µs): 17, 29 y 14, de 300 cada una. Se excluyeron. No es un fallo del circuito, sino del arranque numérico.

## S5 — Worst-Case y sensibilidad (RDUT = 1 mΩ), archivo `WC_RDUT1m.cir`
| Componente | Sensibilidad (% de R por cada 1 % del componente) |
|---|---|
| **RS** | **−0,990** |
| R_FP (1 kΩ, S+) | +0,047 |
| R_FN (1 kΩ, S−) | −0,035 |
| REF, R_INT, R_LIFT, R_RN | +0,012 |
| R_VSET, R_IL, R_G, R_GPU, R_RP | 0 |

**Peor caso con todos los componentes a la vez: +1,02 %.** Casi todo viene de RS. Conclusión de diseño:
- **Shunt de 0,1 %**, para obtener ±0,1 % sin calibrar; o
- **calibración única contra una resistencia patrón**, que elimina la tolerancia de RS y deja solo su TCR (≤ 50 ppm/°C).

---

## Pendiente para el informe (B6)
- Gráficas con pgfplots: histograma de la Montecarlo (v2 frente al diseño anterior), forma de onda del pulso de dos niveles y barras de sensibilidad.
- **Presupuesto de error total:** S4/S5 más el AD7124 (ruido de 0,063 µV rms con G = 128; error de ganancia después de la calibración) más el TCR de RS.

## Limitaciones declaradas
- El P-MOS es un modelo equivalente. Con el modelo del fabricante podrían cambiar el asentamiento y el margen de gate, pero no el resultado ratiométrico.
- El AD7124 no tiene modelo SPICE.
