"""Resume las decisiones descargadas del verificador y deja la lista de usos propios.

    python exploracion/verificar/pasar_verificacion.py DECISIONES.csv      (desde metodo_ia_pjf/)

DECISIONES.csv es lo que baja «Descargar mis decisiones». Guarda una copia en exploracion/verificar/decisiones/
(el original no se toca) y escribe exploracion/verificar/usos_propios.csv con las sentencias que la persona
marcó como uso del órgano. Traducción: organo = incluir; parte o mencion = excluir; duda = pendiente.
Imprime cuántas hay de cada decisión, por origen; un uso propio «fuera del cribado» es una omisión del cribado.
"""
import csv
import json
import shutil
import sys
from collections import Counter
from pathlib import Path

AQUI = Path(__file__).resolve().parent
SUB = AQUI / "../../../Anexos/Anexo 1/SubAnexos"
VALIDAS = {"organo": "incluir", "parte": "excluir", "mencion": "excluir", "duda": "pendiente", "": "sin decidir"}

if len(sys.argv) != 2:
    sys.exit(__doc__)
origen = Path(sys.argv[1])
with open(origen, encoding="utf-8-sig", newline="") as f:
    filas = list(csv.DictReader(f))

# Revisa que las decisiones sean de las cuatro opciones
# Aplica las correcciones posteriores (correcciones_verificacion.csv), con su fecha y motivo; el archivo de
# decisiones no se modifica. La corrección solo vale si la decisión original es la que dice la corrección.
corr = AQUI / "correcciones_verificacion.csv"
if corr.exists():
    with open(corr, encoding="utf-8-sig", newline="") as f:
        cambios = {c["id_sentencia"]: c for c in csv.DictReader(f)}
    for r in filas:
        c = cambios.get(r["id_sentencia"])
        if c:
            if r["decision"] != c["decision_original"]:
                sys.exit(f"Corrección de {r['id_sentencia']}: esperaba «{c['decision_original']}» y la decisión es "
                         f"«{r['decision']}». No se escribió nada.")
            r["decision"] = c["decision_corregida"]
            r["nota"] = (r["nota"] + " " if r["nota"] else "") + f"[corregido {c['fecha']}: {c['motivo']}]"
    print(f"Correcciones aplicadas: {len(cambios)}")

malas = [r["id_sentencia"] for r in filas if r["decision"] not in VALIDAS]
if malas:
    sys.exit(f"Decisiones no reconocidas en: {', '.join(malas)}. No se escribió nada.")

# Guarda una copia del archivo descargado, para que quede junto al proyecto
(AQUI / "decisiones").mkdir(exist_ok=True)
copia = AQUI / "decisiones" / origen.name
if not copia.exists():
    shutil.copy2(origen, copia)

# Escribe la lista de usos propios con los datos de cada sentencia
meta = {m["id"]: m for m in map(json.loads, (SUB / "metadata.jsonl").read_text(encoding="utf-8").splitlines()) if m}
propios = [r for r in filas if r["decision"] == "organo"]
with open(AQUI / "usos_propios.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f)
    w.writerow(["id_sentencia", "origen", "organo", "circuito", "fecha", "tipo_asunto", "nota"])
    for r in propios:
        m = meta[r["id_sentencia"]]
        w.writerow([r["id_sentencia"], r["origen"], m["organo"], m["circuito"], m["fecha"], m["tipo_asunto"], r["nota"]])

# Imprime el resumen
cuenta = Counter((r["origen"], VALIDAS[r["decision"]]) for r in filas)
for o in ("candidata del cribado", "fuera del cribado"):
    print(o + ": " + " · ".join(f"{v} {cuenta[(o, v)]}" for v in ("incluir", "excluir", "pendiente", "sin decidir")))
omisiones = sum(1 for r in propios if r["origen"] == "fuera del cribado")
print(f"Usos propios: {len(propios)} sentencias de {len({meta[r['id_sentencia']]['organo'] for r in propios})} órganos "
      f"(más UI-01). Omisiones del cribado: {omisiones}.")
print(f"Escrito {AQUI / 'usos_propios.csv'}; copia de las decisiones en {copia}")
