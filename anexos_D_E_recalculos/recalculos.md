# Recálculo de las cuentas que no coincidieron

Hecho sin IA: aritmética exacta con los datos y el método que trae cada sentencia. Las cifras «declaradas» se copian de la sentencia; las «recalculadas», del cálculo de abajo.

## 1. UI-02 (sentencia 38940092): garantía por daños y perjuicios

Método de la sentencia (P./J. 71/2014): daños = VC × inflación × meses/12; perjuicios = VC × TIIE × meses/12. Duración: 75.2 + 62.26 = 137.46 días = 4.5820 meses (cada herramienta la redondeó a su modo).

| Herramienta | Lote | Daños declarados | Daños recalculados | Perjuicios declarados | Perjuicios recalculados | Total declarado | Total recalculado |
|---|---|---|---|---|---|---|---|
| ChatGPT | Lote 1 | 9,970 | 9,976.83 | 19,105 | 19,108.39 | 29,075 | 29,085.22 |
| ChatGPT | Lote 2 | 10,396 | 10,405.54 | 20,610 | 19,929.51 | 31,006 | 30,335.05 |
| Grok | Lote 1 | 7,388.73 | 7,393.47 | 24,263.08 | 24,259.82 | 31,651.81 | 31,653.29 |
| Grok | Lote 2 | 7,706.34 | 7,711.18 | 25,297.20 | 25,302.30 | 33,003.54 | 33,013.47 |
| Gemini | Lote 1 | 10,219.01 | 10,212.23 | 19,080.37 | 19,070.53 | 29,299.38 | 29,282.75 |
| Gemini | Lote 2 | 10,659.86 | 10,651.06 | 19,905.74 | 19,890.01 | 30,565.60 | 30,541.08 |

| Herramienta | Total declarado (dos lotes) | Total recalculado | Diferencia |
|---|---|---|---|
| ChatGPT | 60,081 | 59,420.27 | -660.73 |
| Grok | 64,655.35 | 64,666.76 | 11.41 |
| Gemini | 59,864.98 | 59,823.83 | -41.15 |

- Promedio de los totales **declarados** por las tres herramientas: 61,533.78. La sentencia dice «aproximadamente $61,500» (párr. 51).
- Promedio con los totales **recalculados**: 61,303.62.
- Garantía fijada por la sentencia: $60,000, «una cifra cerrada» (párr. 52).

## 2. Sentencia 41338150: días hábiles para la caducidad de la instancia

Periodo: del 09-07-2025 (día siguiente a la última actuación) al 05-02-2026: 212 días naturales, de los cuales 60 son sábado o domingo.

| Lista de días inhábiles | Hábiles declarados | Hábiles recalculados | Restando también el 14-nov-2025 (fuerza mayor) |
|---|---|---|---|
| La de ChatGPT (festivos LFT, vacaciones del TSJCDMX y 12-sep, 15-sep y 31-oct) | 116 | 116 | 115 |
| La de Gemini (sin 12-sep ni 31-oct; incluye 1 y 2 de noviembre) | 115 | 119 | 118 |

- ChatGPT: declara 96 inhábiles; con sus propias listas, sin duplicar, son 60 fines de semana más 36 días inhábiles entre semana = 96. Su cuenta es correcta: 116 hábiles.
- Gemini: declara 115, pero con su propia lista de inhábiles salen 119. Su resultado no se sigue de sus datos.
- La sentencia dice «ciento catorce o ciento quince días hábiles» (párr. 41): son los dos resultados declarados (116 y 115) menos el 14 de noviembre por fuerza mayor (párr. 43–44). Con las listas, lo correcto sería 115 (ChatGPT) o 118 (Gemini).
- La nota 20 de la sentencia atribuye el día de diferencia entre las herramientas a que Gemini no consideró el 12 de septiembre; entre semana, las listas difieren en cinco días (Gemini omite el 1 de agosto, el 12 de septiembre, el 31 de octubre y el 15 de diciembre, y agrega el 15 de julio; el 1 y 2 de noviembre que agrega caen en fin de semana), y el resultado de Gemini no corresponde a su lista.
- La conclusión jurídica (no transcurrieron 120 días hábiles) se sostiene con cualquiera de las cifras.

