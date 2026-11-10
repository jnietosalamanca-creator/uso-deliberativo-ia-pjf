"""Recálculo, sin IA, de las dos cuentas que no coincidieron en la codificación (UI-02 y 41338150).

    python exploracion/definitiva/recalculos.py        (desde metodo_ia_pjf/)

Rehace la aritmética con los datos y el método que trae cada sentencia; no vuelve a correr los prompts (el libro de
usos lo excluye: «no son los mismos y no prueba nada»). Montos con aritmética decimal exacta; días hábiles con el
calendario, día por día. Escribe exploracion/definitiva/resultados/recalculos.md con cada paso, para cotejarlo con una
calculadora y un calendario.

Datos tomados de la sentencia 38940092 (UI-02, párrafos 49 a 53) y de la 41338150 (párrafos 40 a 44).
"""
from datetime import date, timedelta
from decimal import Decimal as D, ROUND_HALF_UP
from pathlib import Path

DEST = Path(__file__).resolve().parent / "resultados" / "recalculos.md"
md = ["# Recálculo de las cuentas que no coincidieron", "",
      "Hecho sin IA: aritmética exacta con los datos y el método que trae cada sentencia. Las cifras «declaradas» se "
      "copian de la sentencia; las «recalculadas», del cálculo de abajo.", ""]


def peso(x, n=2):
    return x.quantize(D(1).scaleb(-n), rounding=ROUND_HALF_UP)


# ─── UI-02 · sentencia 38940092 · garantía por daños y perjuicios de dos lotes ─────────────────────────────────────
VC = {"Lote 1": D("605096.15"), "Lote 2": D("631098.00")}
DIAS = D("75.2") + D("62.26")                                       # amparo indirecto + revisión (párr. 49)
# Cada herramienta usó sus propias tasas y su propio redondeo de los meses; se respeta lo que declaró cada una
HERR = {
    "ChatGPT": {"inflacion": D("4.32"), "tiie": D("8.274"), "meses": D("4.58"),
                "declarado": {"Lote 1": (D("9970"), D("19105"), D("29075")), "Lote 2": (D("10396"), D("20610"), D("31006"))},
                "total_declarado": D("60081")},
    "Grok": {"inflacion": D("3.2"), "tiie": D("10.5"), "meses": D("4.582"),
             "declarado": {"Lote 1": (D("7388.73"), D("24263.08"), D("31651.81")), "Lote 2": (D("7706.34"), D("25297.20"), D("33003.54"))},
             "total_declarado": D("64655.35")},
    "Gemini": {"inflacion": D("4.42"), "tiie": D("8.2540"), "meses": D("4.582"),
               "declarado": {"Lote 1": (D("10219.01"), D("19080.37"), D("29299.38")), "Lote 2": (D("10659.86"), D("19905.74"), D("30565.60"))},
               "total_declarado": D("59864.98")},
}
md += ["## 1. UI-02 (sentencia 38940092): garantía por daños y perjuicios", "",
       f"Método de la sentencia (P./J. 71/2014): daños = VC × inflación × meses/12; perjuicios = VC × TIIE × meses/12. "
       f"Duración: 75.2 + 62.26 = {DIAS} días = {peso(DIAS / 30, 4)} meses (cada herramienta la redondeó a su modo).", "",
       "| Herramienta | Lote | Daños declarados | Daños recalculados | Perjuicios declarados | Perjuicios recalculados | Total declarado | Total recalculado |",
       "|---|---|---|---|---|---|---|---|"]
totales = {}
for h, p in HERR.items():
    tot = D(0)
    for lote, vc in VC.items():
        danos = vc * p["inflacion"] / 100 * p["meses"] / 12
        perj = vc * p["tiie"] / 100 * p["meses"] / 12
        d_dec, p_dec, t_dec = p["declarado"][lote]
        md.append(f"| {h} | {lote} | {d_dec:,} | {peso(danos):,} | {p_dec:,} | {peso(perj):,} | {t_dec:,} | {peso(danos + perj):,} |")
        tot += danos + perj
    totales[h] = tot
md += ["", "| Herramienta | Total declarado (dos lotes) | Total recalculado | Diferencia |", "|---|---|---|---|"]
for h, p in HERR.items():
    md.append(f"| {h} | {p['total_declarado']:,} | {peso(totales[h]):,} | {peso(totales[h] - p['total_declarado']):,} |")
prom_dec = sum(p["total_declarado"] for p in HERR.values()) / 3
prom_rec = sum(totales.values()) / 3
md += ["", f"- Promedio de los totales **declarados** por las tres herramientas: {peso(prom_dec):,}. La sentencia dice "
       "«aproximadamente $61,500» (párr. 51).",
       f"- Promedio con los totales **recalculados**: {peso(prom_rec):,}.",
       "- Garantía fijada por la sentencia: $60,000, «una cifra cerrada» (párr. 52).", ""]

# ─── 41338150 · días hábiles para la caducidad de la instancia ─────────────────────────────────────────────────────
INICIO, FIN = date(2025, 7, 9), date(2026, 2, 5)                    # del día siguiente a la última actuación a la promoción


def dias(desde, hasta):
    return [desde + timedelta(n) for n in range((hasta - desde).days + 1)]


def rango(a, b):
    return set(dias(a, b))


PERIODO = dias(INICIO, FIN)
CHATGPT = ({date(2025, 9, 16), date(2025, 11, 17), date(2025, 12, 25), date(2026, 1, 1), date(2026, 2, 2)}   # festivos LFT
           | rango(date(2025, 7, 16), date(2025, 8, 1)) | rango(date(2025, 12, 15), date(2026, 1, 6))        # vacaciones
           | {date(2025, 9, 12), date(2025, 9, 15), date(2025, 10, 31)})                                       # por acuerdo
GEMINI = (rango(date(2025, 7, 15), date(2025, 7, 31)) | {date(2025, 9, 15), date(2025, 9, 16)}
          | {date(2025, 11, 1), date(2025, 11, 2), date(2025, 11, 17)} | rango(date(2025, 12, 16), date(2025, 12, 31))
          | rango(date(2026, 1, 1), date(2026, 1, 6)) | {date(2026, 2, 2)})
FUERZA_MAYOR = {date(2025, 11, 14)}                                  # aviso del OAJ de la CDMX (párr. 43–44)


def habiles(inhabiles):
    return [d for d in PERIODO if d.weekday() < 5 and d not in inhabiles]


fines = sum(1 for d in PERIODO if d.weekday() >= 5)
h_c, h_g = len(habiles(CHATGPT)), len(habiles(GEMINI))
h_c_fm, h_g_fm = len(habiles(CHATGPT | FUERZA_MAYOR)), len(habiles(GEMINI | FUERZA_MAYOR))
inh_c_semana = sum(1 for d in CHATGPT if INICIO <= d <= FIN and d.weekday() < 5)
md += ["## 2. Sentencia 41338150: días hábiles para la caducidad de la instancia", "",
       f"Periodo: del {INICIO:%d-%m-%Y} (día siguiente a la última actuación) al {FIN:%d-%m-%Y}: {len(PERIODO)} días naturales, "
       f"de los cuales {fines} son sábado o domingo.", "",
       "| Lista de días inhábiles | Hábiles declarados | Hábiles recalculados | Restando también el 14-nov-2025 (fuerza mayor) |",
       "|---|---|---|---|",
       f"| La de ChatGPT (festivos LFT, vacaciones del TSJCDMX y 12-sep, 15-sep y 31-oct) | 116 | {h_c} | {h_c_fm} |",
       f"| La de Gemini (sin 12-sep ni 31-oct; incluye 1 y 2 de noviembre) | 115 | {h_g} | {h_g_fm} |",
       "", f"- ChatGPT: declara 96 inhábiles; con sus propias listas, sin duplicar, son {fines} fines de semana más "
       f"{inh_c_semana} días inhábiles entre semana = {fines + inh_c_semana}. Su cuenta es correcta: {h_c} hábiles.",
       f"- Gemini: declara 115, pero con su propia lista de inhábiles salen {h_g}. Su resultado no se sigue de sus datos.",
       f"- La sentencia dice «ciento catorce o ciento quince días hábiles» (párr. 41): son los dos resultados declarados "
       f"(116 y 115) menos el 14 de noviembre por fuerza mayor (párr. 43–44). Con las listas, lo correcto sería "
       f"{h_c_fm} (ChatGPT) o {h_g_fm} (Gemini).",
       "- La nota 20 de la sentencia atribuye el día de diferencia entre las herramientas a que Gemini no consideró el 12 de "
       "septiembre; entre semana, las listas difieren en cinco días (Gemini omite el 1 de agosto, el 12 de septiembre, el "
       "31 de octubre y el 15 de diciembre, y agrega el 15 de julio; el 1 y 2 de noviembre que agrega caen en fin de "
       "semana), y el resultado de Gemini no corresponde a su lista.",
       "- La conclusión jurídica (no transcurrieron 120 días hábiles) se sostiene con cualquiera de las cifras.", ""]

DEST.write_text("\n".join(md) + "\n", encoding="utf-8")
print("\n".join(md))
