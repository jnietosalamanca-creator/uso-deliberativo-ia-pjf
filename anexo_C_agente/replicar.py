"""Replica el agente que codificó como codificador 2 las sentencias del artículo (libro de códigos v1.0).

    python3 replicar.py preparar N [--trabajo DIR] [--prueba]   arma una carpeta limpia para la corrida N
    python3 replicar.py correr N [--trabajo DIR] [--claude RUTA]  lanza el agente con Claude Code
    python3 replicar.py revisar N [--trabajo DIR]               revisa la salida y el registro de la corrida
    python3 replicar.py comparar A.csv B.csv [--salida X.csv]   acuerdo por campo y alfa de Krippendorff

Ver LEEME.md. Solo usa la biblioteca estándar de Python.

El agente trabaja en una carpeta FUERA de este paquete (por omisión ~/replica_agente_trabajo), que solo tiene los
insumos: así no puede ver originales/, donde están los códigos del autor y las corridas publicadas.
revisar hace lo mismo que recoger.py del proyecto: fichas completas, valores del libro, reglas de pase, faltantes
y citas literales. Los valores no se corrigen: se reportan.
"""
import argparse
import csv
import json
import re
import shutil
import subprocess
import sys
from collections import Counter
from pathlib import Path

sys.dont_write_bytecode = True
AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
from alfa import alfa_nominal, bootstrap  # noqa: E402

MODELO = "claude-opus-5-5"
HERRAMIENTAS = "Read,Write,Grep,Glob"
TRABAJO = Path.home() / "replica_agente_trabajo"
# Mismos valores que config.py del proyecto
SEMILLA, REMUESTREOS, ALFA_SUFICIENTE, ALFA_TENTATIVO = 20260929, 5000, 0.80, 0.667
REGLAS = {
    "p_norma": ("prompt", ["completo", "parcial"]), "p_hechos": ("prompt", ["completo", "parcial"]),
    "p_metodo": ("prompt", ["completo", "parcial"]), "p_limites": ("prompt", ["completo", "parcial"]),
    "recalculo": ("tarea_numerica", ["si"]),
}
OCULTO = {"recalculo": "no_aplica"}
FIJAS = {"codificador", "unidad", "sentencia", "nota", "revisada"}


def leer_libro(ruta):
    """Campos de las secciones 2 a 6 del libro: [{campo, valores, libre}]."""
    campos, seccion = [], None
    for l in Path(ruta).read_text(encoding="utf-8").splitlines():
        m = re.match(r"##\s*(\d+)\.\s*(.+)", l)
        if m:
            seccion = 2 <= int(m.group(1)) <= 6
            continue
        if not seccion or not re.match(r"\|\s*`\w+`", l):
            continue
        celdas = [c.strip() for c in l.strip().strip("|").split("|")]
        valores = {v.group(1) for v in (re.search(r"`(\w+)`", p) for p in celdas[-1].split("·")) if v}
        campos.append({"campo": celdas[0].strip("`"), "valores": valores, "libre": "texto libre" in celdas[-1]})
    return campos


def espacios(t):
    return re.sub(r"\s+", " ", t or "").strip().lower()


def preparar(n, trabajo, prueba):
    corrida = trabajo / f"corrida_{n}"
    if corrida.exists():
        sys.exit(f"Ya existe {corrida}. No se tocó nada.")
    ins = trabajo / "insumos_v10"
    if not ins.exists():
        shutil.copytree(AQUI / "insumos_v10", ins)
    corrida.mkdir(parents=True)
    prompt = (AQUI / "prompt.txt").read_text(encoding="utf-8")
    if prueba:  # solo la ficha más corta, para probar la instalación sin gastar una corrida completa
        fichas = json.loads((ins / "fichas.json").read_text(encoding="utf-8"))
        chica = min(fichas, key=lambda f: (ins / f["archivo"]).stat().st_size)
        ins = trabajo / f"insumos_v10_prueba_{n}" / "insumos_v10"
        (ins / "fichas").mkdir(parents=True)
        shutil.copy(AQUI / "insumos_v10/instrucciones.md", ins)
        shutil.copy(AQUI / "insumos_v10" / chica["archivo"], ins / "fichas")
        (ins / "fichas.json").write_text(json.dumps([chica], ensure_ascii=False, indent=1), encoding="utf-8")
        prompt = prompt.replace("17 fichas", "1 ficha")
    prompt = prompt.replace("{INSUMOS}", str(ins)).replace("{SALIDA}", str(corrida / "salida.jsonl"))
    (corrida / "prompt_usado.txt").write_text(prompt, encoding="utf-8")
    print(f"Lista: {corrida}\nInsumos: {ins}")


def correr(n, trabajo, claude):
    corrida = trabajo / f"corrida_{n}"
    prompt = corrida / "prompt_usado.txt"
    if not prompt.exists():
        sys.exit(f"Falta {prompt}. Corre primero: replicar.py preparar {n}")
    # --restricted: sin comandos ni internet y con los archivos confinados a la carpeta de trabajo. El agente lee
    # texto de terceros (las sentencias), así que no debe poder ejecutar nada, y la ceguera queda garantizada.
    cmd = [claude, "-p", "--restricted", "--model", MODELO, "--tools", HERRAMIENTAS, "--allowedTools", HERRAMIENTAS,
           "--strict-mcp-config", "--output-format", "stream-json", "--verbose"]
    with open(prompt, encoding="utf-8") as ent, open(corrida / "registro.jsonl", "w", encoding="utf-8") as sal:
        r = subprocess.run(cmd, stdin=ent, stdout=sal, cwd=trabajo)
    print(f"Terminó con código {r.returncode}. Registro: {corrida / 'registro.jsonl'}")


def auditar(corrida, trabajo):
    """Rutas absolutas fuera de la carpeta de trabajo en lo que el agente pidió hacer, y modelo que respondió."""
    fuera, modelos, ruta = [], Counter(), corrida / "registro.jsonl"
    if not ruta.exists():
        return None, modelos
    for l in ruta.read_text(encoding="utf-8").splitlines():
        o = json.loads(l)
        if o.get("type") != "assistant":
            continue
        modelos[o["message"].get("model")] += 1
        for b in o["message"]["content"]:
            if b.get("type") == "tool_use":
                texto = b["input"].get("command") or b["input"].get("file_path") or b["input"].get("path") or ""
                fuera += [r for r in re.findall(r"(?:/Users|/home|/private|~)/[^\s\"';|&)]+", texto)
                          if not r.startswith(str(trabajo)) and "/tmp/" not in r]
    return fuera, modelos


def revisar(n, trabajo):
    corrida = trabajo / f"corrida_{n}"
    usado = (corrida / "prompt_usado.txt").read_text(encoding="utf-8")
    ins = Path(re.search(r"la ÚNICA que puedes leer\): (.+?)/\n", usado).group(1))
    campos = leer_libro(ins / "instrucciones.md")
    nombres = [c["campo"] for c in campos]
    valores = {c["campo"]: c["valores"] for c in campos}
    libres = {c["campo"] for c in campos if c["libre"]}
    fichas = json.loads((ins / "fichas.json").read_text(encoding="utf-8"))
    textos = {(f["unidad"], f["sentencia"]): espacios((ins / f["archivo"]).read_text(encoding="utf-8")) for f in fichas}
    if not (corrida / "salida.jsonl").exists():
        sys.exit(f"El agente no escribió {corrida / 'salida.jsonl'}. Revisa el final de {corrida / 'registro.jsonl'} "
                 "(por ejemplo, «Not logged in» significa que falta iniciar sesión en Claude Code).")
    salida = {}
    for i, l in enumerate((corrida / "salida.jsonl").read_text(encoding="utf-8").splitlines(), 1):
        if l.strip():
            try:
                o = json.loads(l)
            except json.JSONDecodeError as e:
                sys.exit(f"Renglón {i} no es JSON válido: {e}")
            salida[(str(o.get("unidad")), str(o.get("sentencia")))] = o

    problemas, filas = [], []
    for k in salida.keys() - textos.keys():
        problemas.append({"unidad": k[0], "sentencia": k[1], "campo": "", "problema": "ficha que no existe"})
    for f in fichas:
        k = (f["unidad"], f["sentencia"])
        o = salida.get(k)
        if not o:
            problemas.append({"unidad": k[0], "sentencia": k[1], "campo": "", "problema": "ficha sin codificar"})
            continue
        v, c = o.get("valores") or {}, o.get("citas") or {}
        aplica = lambda campo: campo not in REGLAS or v.get(REGLAS[campo][0]) in REGLAS[campo][1]
        fila = {"codificador": f"replica_corrida{n}", "unidad": k[0], "sentencia": k[1]}
        for campo in nombres:
            val = (v.get(campo) or "").strip()
            if not aplica(campo):
                if val and val != OCULTO.get(campo):
                    problemas.append({"unidad": k[0], "sentencia": k[1], "campo": campo, "problema": f"valor «{val}» donde no aplica"})
                val = OCULTO.get(campo, "")
            elif not val:
                problemas.append({"unidad": k[0], "sentencia": k[1], "campo": campo, "problema": "falta el valor"})
            elif campo not in libres and val not in valores[campo]:
                problemas.append({"unidad": k[0], "sentencia": k[1], "campo": campo, "problema": f"valor «{val}» no está en el libro"})
            cita = (c.get(campo) or "").strip()
            if val and aplica(campo) and cita and espacios(cita).strip(" .…\"“”«»") not in textos[k]:
                problemas.append({"unidad": k[0], "sentencia": k[1], "campo": campo, "problema": "cita no encontrada en la sentencia"})
            fila[campo], fila["cita_" + campo] = val, cita
        fila["nota"] = (o.get("nota") or "").strip()
        filas.append(fila)

    cab = ["codificador", "unidad", "sentencia"] + [x for campo in nombres for x in (campo, "cita_" + campo)] + ["nota"]
    with open(corrida / f"replica_corrida{n}.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=cab)
        w.writeheader()
        w.writerows(filas)
    with open(corrida / "revision.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=["unidad", "sentencia", "campo", "problema"])
        w.writeheader()
        w.writerows(problemas)
    print(f"Corrida {n}: {len(filas)} de {len(fichas)} fichas · {len(problemas)} problemas")
    for p, m in Counter(p["problema"].split("«")[0].strip() for p in problemas).most_common():
        print(f"  {m:3}  {p}")
    fuera, modelos = auditar(corrida, trabajo)
    if fuera is None:
        print("Sin registro.jsonl: no se puede auditar qué hizo el agente.")
    else:
        print(f"Modelo que respondió: {dict(modelos)}")
        print(f"Rutas fuera de la carpeta de trabajo: {len(fuera)}" + "".join(f"\n  {r}" for r in fuera[:20]))
    print(f"Escrito {corrida / f'replica_corrida{n}.csv'} y revision.csv")


def valor(r, campo):
    v = (r.get(campo) or "").strip()
    return re.sub(r"[\s\-]+", "", v.lower()) if campo == "herramienta" else v   # «Chat GPT» = «ChatGPT»


def comparar(ruta_a, ruta_b, salida):
    leer = lambda p: {(r["unidad"], r["sentencia"]): r for r in csv.DictReader(open(p, encoding="utf-8-sig", newline=""))}
    a, b = leer(ruta_a), leer(ruta_b)
    # Las fichas que sí cuentan son las de los archivos de originales/ (14 de las 17; las otras 3 no son uso propio)
    vigentes = set(leer(AQUI / "originales/agente_corrida1.csv"))
    fichas = sorted(set(a) & set(b) & vigentes)
    if not fichas:
        sys.exit("Los dos archivos no comparten ninguna ficha vigente.")
    campos = [c for c in next(iter(a.values())) if c not in FIJAS and not c.startswith("cita_")]
    r3 = lambda x: "" if x is None else round(x, 3)
    filas = []
    for c in campos:
        pares = [(valor(a[f], c) or None, valor(b[f], c) or None) for f in fichas]
        ambos = [list(p) for p in pares if p[0] and p[1]]
        alfa = alfa_nominal(ambos) if ambos else None
        ic = bootstrap(ambos, REMUESTREOS, SEMILLA) if alfa is not None else (None, None)
        lectura = ("sin datos" if not ambos else "sin variación (todos el mismo valor)" if alfa is None else
                   "suficiente" if alfa >= ALFA_SUFICIENTE else "tentativo" if alfa >= ALFA_TENTATIVO else "insuficiente")
        filas.append({"campo": c, "n_ambos": len(ambos), "n_solo_uno": sum(1 for p in pares if bool(p[0]) != bool(p[1])),
                      "acuerdo_simple": r3(sum(p[0] == p[1] for p in ambos) / len(ambos)) if ambos else "",
                      "alfa": r3(alfa), "ic95_inf": r3(ic[0]), "ic95_sup": r3(ic[1]), "lectura": lectura})
    print(f"{len(fichas)} fichas comparadas")
    for f in filas:
        print(f"  {f['campo']:26} acuerdo {f['acuerdo_simple']!s:6} alfa {f['alfa']!s:6} {f['lectura']}")
    if salida:
        with open(salida, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.DictWriter(f, fieldnames=list(filas[0]))
            w.writeheader()
            w.writerows(filas)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="orden", required=True)
    for nombre in ("preparar", "correr", "revisar"):
        s = sub.add_parser(nombre)
        s.add_argument("n")
        s.add_argument("--trabajo", type=Path, default=TRABAJO)
        if nombre == "preparar":
            s.add_argument("--prueba", action="store_true", help="una sola ficha, para probar la instalación")
        if nombre == "correr":
            s.add_argument("--claude", default="claude", help="ruta del ejecutable de Claude Code")
    s = sub.add_parser("comparar")
    s.add_argument("a")
    s.add_argument("b")
    s.add_argument("--salida")
    arg = ap.parse_args()
    if arg.orden == "preparar":
        preparar(arg.n, arg.trabajo.resolve(), arg.prueba)
    elif arg.orden == "correr":
        correr(arg.n, arg.trabajo.resolve(), arg.claude)
    elif arg.orden == "revisar":
        revisar(arg.n, arg.trabajo.resolve())
    else:
        comparar(arg.a, arg.b, arg.salida)
