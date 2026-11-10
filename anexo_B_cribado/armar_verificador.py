"""Arma verificar.html: una sola página para decidir, sentencia por sentencia, quién usó la IA.

    python exploracion/verificar/armar_verificador.py        (desde metodo_ia_pjf/)

Junta en una fila de trabajo las candidatas del cribado que no son UI-01 (lector45/) y las sentencias con
marcador de herramienta o prompt que el cribado no tomó (cribado/fuera_del_cribado.csv). Para cada una lleva
los párrafos pertinentes (los que mencionan la IA, una herramienta o prompt, o la clave de las tesis) y el
texto completo. La página no sugiere respuestas: muestra el texto y guarda lo que decide la persona.
Las decisiones se bajan con «Descargar mis decisiones» y se resumen con pasar_verificacion.py.
"""
import csv
import hashlib
import json
import re
import sys
from pathlib import Path

csv.field_size_limit(sys.maxsize)
AQUI = Path(__file__).resolve().parent
EXP = AQUI.parent
SUB = EXP / "../../Anexos/Anexo 1/SubAnexos"

IA = re.compile(r"inteligencias?\s+artificial(?:es)?", re.I)
HERRAMIENTA = re.compile(r"\b(?:chat\s*-?\s*gpt|gpt-\d|copilot|gemini|claude|prompts?|azure|clipchamp|modelos? de lenguaje)\b", re.I)
TESIS = re.compile(r"II\.\s*2\s*[oº°]\.?\s*C\.?\s*(?:J\s*/\s*[12]|[89])\s*K|20316(?:39|40)|2031(?:009|010)", re.I)

# Preguntas especiales para sentencias concretas (las demás llevan la pregunta general)
ESPECIALES = {
    "40483087": "Su síntesis ya cuenta en UI-01. Aparte de la síntesis, ¿hay OTRO uso de IA en esta sentencia? "
                "Si no lo hay, elige «Nadie: solo se menciona».",
}


def leer(ruta):
    with open(ruta, encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


if __name__ == "__main__":
    # Reúne las dos listas, en ese orden, con su origen
    meta = {m["id"]: m for m in map(json.loads, (SUB / "metadata.jsonl").read_text(encoding="utf-8").splitlines()) if m}
    cola = [(r["id_sentencia"], "candidata del cribado") for r in leer(EXP / "lector45/data/caso/universo_del_caso.csv")]
    cola += [(r["id_sentencia"], "fuera del cribado") for r in leer(EXP / "cribado/fuera_del_cribado.csv")]

    # Para cada sentencia: datos, párrafos pertinentes y texto completo
    items = []
    for sid, origen in cola:
        m = meta[sid]
        texto = (SUB / "txt" / f"{sid}.txt").read_text(encoding="utf-8")
        parrafos = [re.sub(r"\s+", " ", p).strip() for p in re.split(r"\n\s*\n", texto)]
        pert = [p for p in parrafos if p and (IA.search(p) or HERRAMIENTA.search(p) or TESIS.search(p))]
        items.append({"id": sid, "origen": origen, "organo": m["organo"], "fecha": m["fecha"],
                      "tipo_asunto": m["tipo_asunto"], "pertinentes": pert, "completo": texto,
                      "especial": ESPECIALES.get(sid, "")})

    # Inserta los datos en la plantilla y escribe la página
    datos = {"items": items, "huella": hashlib.sha256(" ".join(i["id"] for i in items).encode()).hexdigest()[:12],
             "ia": IA.pattern, "herramienta": HERRAMIENTA.pattern}
    js = json.dumps(datos, ensure_ascii=False).replace("</", "<\\/")
    pagina = (AQUI / "plantilla_verificador.html").read_text(encoding="utf-8").replace("__DATOS__", js)
    (AQUI / "verificar.html").write_text(pagina, encoding="utf-8")
    print(f"verificar.html: {len(items)} sentencias "
          f"({sum(i['origen'] == 'candidata del cribado' for i in items)} candidatas, "
          f"{sum(i['origen'] == 'fuera del cribado' for i in items)} fuera del cribado)")
