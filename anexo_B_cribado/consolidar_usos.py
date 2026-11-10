"""Exploración 3. Consolida los usos institucionales repetidos (regla del 23-oct-2026 en libro_codigos_usos.md).

    python exploracion/consolidar_usos.py        (desde metodo_ia_pjf/)

Un mismo órgano que declara la misma tarea con el mismo machote en varias sentencias cuenta como UN uso.
Las sentencias de ese machote se juntan en una fila; las demás candidatas del cribado quedan una por fila.
No toca cribado/data/caso/universo_del_caso.csv (ni su columna de verificación manual): lo lee y escribe aparte.

Para cada sentencia del machote se registran, por búsqueda de palabras:
  version       con_instruccion: transcribe la instrucción dada a la IA («Redacta una síntesis…», «Te compartiré
                un proyecto…»); sin_instruccion: no. (Corrección del 26-oct-2026: antes se tomaba como versión la
                palabra «prompt» junto a la síntesis, que es solo el rótulo «(en inglés: prompt)»; las 196 transcriben
                la instrucción.)
  rotulo_prompt «si» cuando la instrucción va rotulada «(en inglés: prompt)» cerca de la síntesis; dato descriptivo
  otro_prompt   «si» cuando además dice «prompt» lejos de la síntesis: puede ser OTRO uso; esa sentencia
                se cuenta en el machote y además queda como candidata propia para revisarla a mano

Escribe en exploracion/cribado/:
  universo_consolidado.csv          una fila por unidad de conteo (uso institucional o candidata)
  uso_institucional_sentencias.csv  las sentencias de cada uso institucional, con su fecha y su versión
"""
import csv
import json
import re
import sys
import unicodedata
from collections import Counter
from pathlib import Path

csv.field_size_limit(sys.maxsize)
BASE = Path(__file__).resolve().parent
SUB = BASE / "../../Anexos/Anexo 1/SubAnexos"
CRIB = BASE / "cribado"

# Usos institucionales decididos a mano: órgano y patrón del machote (texto en minúsculas, sin acentos)
USOS_INSTITUCIONALES = [{
    "id_uso": "UI-01",
    "tarea": "sintesis_ciudadana",
    "organo": ("Juzgado Segundo de Distrito en Materia Administrativa, Especializado en Competencia Económica, "
               "Radiodifusión y Telecomunicaciones, con residencia en la Ciudad de México y Jurisdicción en toda la República"),
    "patron": r"sintesis (?:en lenguaje )?ciudadan[ao]|lenguaje ciudadano",
}]
SINTESIS = re.compile(r"s[ií]ntesis", re.I)
PROMPT = re.compile(r"\bprompts?\b", re.I)
INSTRUCCION = re.compile(r"(?:redacta|elabora|genera|haz)\s+una\s+(?:breve\s+)?s[ií]ntesis|te\s+compartir[eé]\s+un\s+proyecto", re.I)


def sin_acentos(t):
    return "".join(c for c in unicodedata.normalize("NFD", t.lower()) if unicodedata.category(c) != "Mn")


def version(texto):
    """(versión de la síntesis, ¿hay otro «prompt» lejos de la síntesis?)"""
    cerca = [bool(SINTESIS.search(texto[max(0, h.start() - 250): h.end() + 150])) for h in PROMPT.finditer(texto)]
    v = "con_instruccion" if INSTRUCCION.search(texto) else "sin_instruccion"
    return v, ("si" if any(cerca) else "no"), ("si" if not all(cerca) else "no")


if __name__ == "__main__":
    # Carga las candidatas del cribado y los metadatos
    with open(CRIB / "data/caso/universo_del_caso.csv", encoding="utf-8-sig") as f:
        cand = list(csv.DictReader(f))
    meta = {m["id"]: m for m in map(json.loads, (SUB / "metadata.jsonl").read_text(encoding="utf-8").splitlines()) if m}

    # Asigna cada sentencia del machote a su uso institucional y registra su versión
    miembros, en_uso = [], {}
    for ui in USOS_INSTITUCIONALES:
        pat = re.compile(ui["patron"])
        for sid, m in meta.items():
            ruta = SUB / "txt" / f"{sid}.txt"
            if m["organo"] != ui["organo"] or not ruta.exists():
                continue
            texto = re.sub(r"\s+", " ", ruta.read_text(encoding="utf-8"))
            if pat.search(sin_acentos(texto)):
                v, rotulo, otro = version(texto)
                miembros.append({"id_uso": ui["id_uso"], "id_sentencia": sid, "fecha": m["fecha"], "version": v,
                                 "rotulo_prompt": rotulo, "otro_prompt": otro})
                en_uso[sid] = (ui["id_uso"], otro)
    miembros.sort(key=lambda r: (r["id_uso"], r["fecha"], r["id_sentencia"]))

    # Arma la tabla consolidada: una fila por uso institucional y una por cada otra candidata
    cab = ["unidad", "tipo", "id_sentencia", "organo", "circuito", "fecha_primera", "fecha_ultima", "n_sentencias",
           "versiones", "invocacion_expresa", "invocacion_implicita", "uso_propio_candidato", "evidencia_uso",
           "verificacion_manual", "nota"]
    filas = []
    for ui in USOS_INSTITUCIONALES:
        ms = [r for r in miembros if r["id_uso"] == ui["id_uso"]]
        vs = Counter(r["version"] for r in ms)
        filas.append({"unidad": ui["id_uso"], "tipo": "uso_institucional", "organo": ui["organo"],
                      "circuito": meta[ms[0]["id_sentencia"]]["circuito"], "fecha_primera": ms[0]["fecha"],
                      "fecha_ultima": ms[-1]["fecha"], "n_sentencias": len(ms),
                      "versiones": " · ".join(f"{k} {n}" for k, n in vs.most_common()),
                      "nota": f"tarea: {ui['tarea']}; una sola unidad de conteo (regla de uso institucional repetido)"})
    for c in cand:
        uso = en_uso.get(c["id_sentencia"])
        if uso and uso[1] == "no":
            continue                     # ya contada dentro del uso institucional
        filas.append({"unidad": c["id_sentencia"], "tipo": "candidata", "id_sentencia": c["id_sentencia"],
                      "organo": c["organo"], "circuito": c["circuito"], "fecha_primera": c["fecha"],
                      "fecha_ultima": c["fecha"], "n_sentencias": 1,
                      **{k: c[k] for k in ("invocacion_expresa", "invocacion_implicita", "uso_propio_candidato",
                                           "evidencia_uso", "verificacion_manual")},
                      "nota": (f"también en {uso[0]}, con otro «prompt» lejos de la síntesis: revisar si declara otro uso. " if uso else "") + c["nota"]})

    # Escribe las dos tablas e imprime el resumen
    with open(CRIB / "universo_consolidado.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=cab)
        w.writeheader()
        w.writerows(filas)
    with open(CRIB / "uso_institucional_sentencias.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=["id_uso", "id_sentencia", "fecha", "version", "rotulo_prompt", "otro_prompt"])
        w.writeheader()
        w.writerows(miembros)
    otros = [r for r in filas if r["tipo"] == "candidata"]
    print(f"Candidatas del cribado: {len(cand)} sentencias")
    for r in filas:
        if r["tipo"] == "uso_institucional":
            print(f"{r['unidad']}: {r['n_sentencias']} sentencias, {r['fecha_primera']} a {r['fecha_ultima']} ({r['versiones']})")
    print(f"Otras candidatas: {len(otros)} de {len({r['organo'] for r in otros})} órganos")
    print(f"Unidades de conteo: {len(filas)}")
