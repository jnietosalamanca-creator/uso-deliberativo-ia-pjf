#!/usr/bin/env python3
"""Paso 3 · Universo del caso: toda sentencia que invoca el criterio sobre IA o declara un uso propio de IA.

    python3 universo_del_caso.py RUTA_SUBANEXOS [--clasificacion data/clasificacion/todo_corrida1.jsonl]

El caso no se muestrea: se reúnen todas las sentencias que cumplen al menos una de tres reglas, fijadas antes de
codificar (protocolo, Paso 3):

  1. Invocación expresa: el texto de la sentencia cita la clave, el rubro o el registro digital de alguna de las cuatro
     tesis del Segundo Tribunal Colegiado en Materia Civil del Segundo Circuito (II.2o.C.8 K y II.2o.C.9 K, 11a.
     época; II.2o.C. J/1 K y II.2o.C. J/2 K, 12a. época).
  2. Invocación implícita: sin citarlas, los párrafos que mencionan la IA (con su contexto) usan el vocabulario
     propio de al menos dos de los cuatro elementos mínimos (ELEMENTOS, abajo).
  3. Uso propio declarado: un párrafo que menciona la IA dice, con voz del órgano («este tribunal», «la suscrita»,
     «la presente resolución»…), que se usó IA. Si existe la clasificación del Paso 2, el párrafo debe ser una mención
     específica.

Las reglas buscan con amplitud; lo que encuentran se verifica a mano (columna verificacion_manual: «incluir» o
«excluir», con su razón en «nota»). Solo se excluye un falso positivo evidente, por ejemplo, el uso de IA de una
parte que la regla 3 tomó por uso del órgano.

Escribe data/caso/universo_del_caso.csv y data/caso/universo_del_caso.json. Solo usa la biblioteca estándar.
"""
import argparse
import csv
import json
import re
from collections import Counter
from pathlib import Path

from clasificar_modelo import ultimas

AQUI = Path(__file__).resolve().parent
ORGANO_CREADOR = "Segundo Tribunal Colegiado en Materia Civil del Segundo Circuito"
VOTOS = {"38079611_6", "38079611_9", "29889267"}

# Regla 1: clave, rubro o registro digital de las cuatro tesis
EXPRESA = re.compile(
    r"II\.\s?2o\.\s?C\.\s?(?:J/\s?[12]|[89])\s?K"                       # claves
    r"|INTELIGENCIA\s+ARTIFICIAL\s+APLICADA\s+EN\s+PROCESOS\s+JURISDICCIONALES"  # rubro
    r"|\b20310(?:09|10)\b|\b20316(?:39|40)\b",                          # registros digitales
    re.I)

# Regla 2: vocabulario propio de cada elemento mínimo de la jurisprudencia II.2o.C. J/2 K (12a.)
ELEMENTOS = {
    "a": re.compile(r"proporcionalidad e inocuidad|razonamientos? num[eé]ricos?", re.I),
    "b": re.compile(r"protecci[oó]n de (?:los )?datos", re.I),
    "c": re.compile(r"transparencia y (?:la )?explicabilidad|explicabilidad|metodolog[ií]a, los datos empleados", re.I),
    "d": re.compile(r"supervisi[oó]n y (?:la )?decisi[oó]n humanas?|supervisi[oó]n humana|auxiliar y no como sustituto", re.I),
}

# Regla 3: voz del órgano + verbo de uso + IA, dentro de la misma oración
VOZ = (r"(?:este (?:tribunal|órgano|juzgado|colegiado)|esta (?:autoridad|juzgadora|sala|potestad|resolución|ejecutoria|"
       r"sentencia)|el suscrito|la suscrita|este órgano jurisdiccional|la presente (?:sentencia|resolución|ejecutoria)|"
       r"resolución que es elaborada|se informa que esta)")
USO = r"(?:emple|utiliz|us[óo]|hizo uso|se vali|valió|apoy|asistencia|elaborad|cread|generad|auxili)"
PROPIO = re.compile(VOZ + r"[^.]{0,220}?" + USO + r"[^.]{0,160}?inteligencia\s+artificial"
                    r"|inteligencia\s+artificial[^.]{0,120}(?:utilizada|empleada) por este", re.I)


def leer_clasificacion(ruta):
    """Código del Paso 2 por huella, si ya existe la clasificación; si no, un diccionario vacío."""
    p = Path(ruta)
    if not p.exists():
        return {}
    cod = {}
    for r in ultimas(p).values():
        j = r.get("json") or {}
        if not r.get("problema") and j.get("codigo") in ("especifica", "generica"):
            cod[r["id"]] = j["codigo"]
    return cod


def main():
    # Lee las rutas de la línea de comandos y carga metadatos, textos y unidades
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("subanexos")
    ap.add_argument("--clasificacion", default=str(AQUI / "data/clasificacion/todo_corrida1.jsonl"))
    a = ap.parse_args()
    sub = Path(a.subanexos)
    meta = {m["id"]: m for m in map(json.loads, (sub / "metadata.jsonl").read_text(encoding="utf-8").splitlines()) if m}
    unidades = [json.loads(l) for l in (AQUI / "data/unidades/unidades.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    por_sentencia = {}
    for u in unidades:
        por_sentencia.setdefault(u["id_sentencia"], []).append(u)
    codigo = leer_clasificacion(a.clasificacion)

    # Aplica las tres reglas a cada sentencia con texto
    filas = []
    for ruta in sorted((sub / "txt").glob("*.txt")):
        i = ruta.stem
        texto = re.sub(r"\s+", " ", ruta.read_text(encoding="utf-8"))
        claves = sorted({re.sub(r"\s+", " ", m.group(0)).upper() for m in EXPRESA.finditer(texto)})
        us = por_sentencia.get(i, [])
        contexto = " ".join(re.sub(r"\s+", " ", f"{u['contexto_anterior']} {u['registro']} {u['contexto_posterior']}") for u in us)
        elementos = [k for k, rx in ELEMENTOS.items() if rx.search(contexto)]
        implicita = not claves and len(elementos) >= 2
        uso, evidencia, cod_uso = False, "", ""
        for u in us:
            m = PROPIO.search(re.sub(r"\s+", " ", u["registro"]))
            if not m:
                continue
            cod = codigo.get(u["huella_registro"], "sin dato")
            if cod in ("especifica", "sin dato"):
                uso, evidencia, cod_uso = True, m.group(0)[:300], cod
                break
        if not (claves or implicita or uso):
            continue
        m = meta[i]
        filas.append({
            "id_sentencia": i, "organo": m["organo"], "circuito": m.get("circuito", ""), "fecha": m["fecha"],
            "tipo_asunto": m["tipo_asunto"], "organo_creador": "sí" if m["organo"] == ORGANO_CREADOR else "no",
            "voto": "sí" if i in VOTOS else "no",
            "invocacion_expresa": "sí" if claves else "no", "claves_citadas": " | ".join(claves),
            "elementos_vocabulario": ",".join(elementos), "invocacion_implicita": "sí" if implicita else "no",
            "uso_propio_candidato": "sí" if uso else "no", "evidencia_uso": evidencia, "codigo_paso2": cod_uso,
            "verificacion_manual": "", "nota": ""})

    # Guarda la tabla (con las columnas de verificación vacías) y un resumen
    sal = AQUI / "data/caso"
    sal.mkdir(parents=True, exist_ok=True)
    destino = sal / "universo_del_caso.csv"
    if destino.exists():
        # Conserva la verificación manual ya hecha si se vuelve a correr
        with destino.open(encoding="utf-8-sig") as f:
            previo = {r["id_sentencia"]: r for r in csv.DictReader(f)}
        for r in filas:
            if r["id_sentencia"] in previo:
                r["verificacion_manual"] = previo[r["id_sentencia"]].get("verificacion_manual", "")
                r["nota"] = previo[r["id_sentencia"]].get("nota", "")
    filas.sort(key=lambda r: (r["fecha"], r["id_sentencia"]))
    with destino.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(filas[0].keys()))
        w.writeheader()
        w.writerows(filas)
    resumen = {
        "sentencias_en_el_universo": len(filas),
        "por_regla": {"expresa": sum(r["invocacion_expresa"] == "sí" for r in filas),
                      "implicita": sum(r["invocacion_implicita"] == "sí" for r in filas),
                      "uso_propio": sum(r["uso_propio_candidato"] == "sí" for r in filas)},
        "organos": len({r["organo"] for r in filas}),
        "organos_que_invocan_el_criterio": len({r["organo"] for r in filas if "sí" in (r["invocacion_expresa"], r["invocacion_implicita"])}),
        "del_organo_creador": sum(r["organo_creador"] == "sí" for r in filas),
        "clasificacion_del_paso2": "usada" if codigo else "aún no existe: la regla 3 queda sin ese filtro",
        "primera_fecha": filas[0]["fecha"], "ultima_fecha": filas[-1]["fecha"],
        "elementos_mas_frecuentes": dict(Counter(e for r in filas for e in r["elementos_vocabulario"].split(",") if e)),
    }
    (sal / "universo_del_caso.json").write_text(json.dumps(resumen, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(resumen, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
