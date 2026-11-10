#!/usr/bin/env python3
"""Paso 2 · Clasificación automática de las menciones con un modelo de lenguaje.

    python3 clasificar_modelo.py muestra [--corrida 1] [--modelo claude-opus-5-5]           # envío directo
    python3 clasificar_modelo.py muestra --lotes [--esperar]                                 # por lotes, a mitad de precio
    python3 clasificar_modelo.py todo --lotes --corrida 2
    python3 clasificar_modelo.py muestra --simular                                           # arma las peticiones sin enviarlas

«muestra» clasifica los 300 textos sorteados (data/muestra/muestra_para_codificar.json), para medir el acuerdo entre
el modelo y la codificación humana. «todo» clasifica los 1,580 textos distintos de data/unidades/unidades.jsonl; el
código de cada texto se copia después a todas sus apariciones (resumen_base.py).

Cada texto es una petición independiente, sin historial, con temperatura 0 y el prompt prompt_clasificacion_v2.1.txt
tal cual. El mensaje de sistema (el prompt con el libro de códigos, igual en todas las peticiones) se marca para la
caché de la API: se cobra completo una vez y después a una fracción del precio. La caché no cambia lo que el modelo
recibe ni lo que responde.

Dos formas de envío:
  - directo (por omisión): una petición tras otra; la caché dura 5 minutos.
  - --lotes: todas las peticiones pendientes van en un lote de la Message Batches API, que cuesta la mitad y se
    resuelve en minutos u horas (máximo 24). La caché dura 1 hora. La primera ejecución crea el lote y guarda su
    identificador en data/clasificacion/<modo>_corrida<N>.lote.json; las siguientes consultan su estado y, cuando
    terminó, descargan los resultados. Con --esperar, el script consulta cada minuto hasta que termine.

Las salidas se guardan sin editar, una por línea, en data/clasificacion/<modo>_corrida<N>.jsonl, con el modelo que
respondió, la fecha, los parámetros, la huella del prompt y el uso de tokens (incluida la caché). Si una petición falla,
queda registrada y se vuelve a pedir en la siguiente ejecución. Para medir el acuerdo del modelo consigo mismo se hace
una segunda corrida (--corrida 2).

Vía sin API (--agentes): «preparar» divide los textos en grupos fijos de --tam-grupo (25 por omisión) y escribe en
data/clasificacion/agentes_<modo>_corrida<N>/ las instrucciones (el mismo mensaje de sistema) y un archivo por grupo;
cada grupo lo codifica un subagente de Claude Code a ciegas, que escribe grupo_NN.salida.jsonl; «recoger» valida esas
salidas y las guarda en el mismo formato que la API. Diferencias que se declaran: la temperatura no se controla y cada
agente ve varios textos en la misma conversación.

Requiere la variable de entorno ANTHROPIC_API_KEY (salvo con --agentes). Solo usa la biblioteca estándar de Python.
"""
import argparse
import csv
import hashlib
import json
import os
import random
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

AQUI = Path(__file__).resolve().parent
PROMPT = AQUI / "prompt_clasificacion_v2.1.txt"
API = "https://api.anthropic.com/v1"
MAX_TOKENS = 400
TEMPERATURA = 0


def ahora():
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def partes_del_prompt():
    """Separa el mensaje de sistema y la plantilla por unidad del archivo del prompt."""
    t = PROMPT.read_text(encoding="utf-8")
    ini_sis = t.index("=== MENSAJE DE SISTEMA ===")
    ini_usu = t.index("=== MENSAJE DE USUARIO (plantilla por unidad) ===")
    sistema = t[ini_sis + len("=== MENSAJE DE SISTEMA ==="):ini_usu].strip()
    plantilla = t[ini_usu + len("=== MENSAJE DE USUARIO (plantilla por unidad) ==="):].strip()
    return sistema, plantilla


def textos(modo):
    """Lista de (identificador, anterior, registro, posterior) que se van a clasificar."""
    if modo == "muestra":
        datos = json.loads((AQUI / "data/muestra/muestra_para_codificar.json").read_text(encoding="utf-8"))
        return [(u["id"], u["anterior"], u["registro"], u["posterior"]) for u in datos]
    # En «todo», un texto por huella: el representante es la unidad con el identificador más bajo (como en muestreo.py)
    rep = {}
    for linea in (AQUI / "data/unidades/unidades.jsonl").read_text(encoding="utf-8").splitlines():
        if linea.strip():
            u = json.loads(linea)
            h = u["huella_registro"]
            if h not in rep or u["id_unidad"] < rep[h]["id_unidad"]:
                rep[h] = u
    return [(h, u["contexto_anterior"], u["registro"], u["contexto_posterior"]) for h, u in sorted(rep.items())]


def peticion(modelo, sistema, plantilla, ant, reg, pos, ttl):
    """Parámetros de una petición a la API de mensajes; el mensaje de sistema va marcado para la caché."""
    usuario = (plantilla.replace("{parrafo_anterior}", ant or "(no hay)")
                        .replace("{parrafo_registro}", reg)
                        .replace("{parrafo_posterior}", pos or "(no hay)"))
    cache = {"type": "ephemeral", "ttl": ttl} if ttl == "1h" else {"type": "ephemeral"}
    return {"model": modelo, "max_tokens": MAX_TOKENS, "temperature": TEMPERATURA,
            "system": [{"type": "text", "text": sistema, "cache_control": cache}],
            "messages": [{"role": "user", "content": usuario}]}


def leer_json(texto):
    """Extrae el objeto JSON de la respuesta y comprueba que respete el formato y la regla del libro."""
    try:
        j = json.loads(texto[texto.index("{"):texto.rindex("}") + 1])
    except ValueError:
        return None, "la respuesta no trae un JSON válido"
    if j.get("codigo") not in ("especifica", "generica"):
        return j, "código fuera de las categorías"
    debe = "especifica" if j.get("t1") == "si" and "si" in (j.get("t2"), j.get("t3")) else "generica"
    if j["codigo"] != debe:
        return j, "el código no coincide con t1, t2 y t3"
    if j["codigo"] == "generica" and j.get("criterio_judicial") not in ("si", "no"):
        return j, "falta la etapa 2 en una genérica"
    return j, ""


def api(clave, metodo, ruta, cuerpo=None, intentos=6, crudo=False):
    """Llama a la API; reintenta con espera creciente si el servicio está saturado o la red falla."""
    datos = json.dumps(cuerpo).encode() if cuerpo is not None else None
    url = ruta if ruta.startswith("http") else API + ruta
    for k in range(intentos):
        req = urllib.request.Request(url, data=datos, method=metodo, headers={
            "x-api-key": clave, "anthropic-version": "2023-06-01", "content-type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=300) as r:
                contenido = r.read()
                return contenido.decode("utf-8") if crudo else json.loads(contenido)
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503, 529) and k < intentos - 1:
                time.sleep(min(60, 2 ** k + random.random()))
                continue
            raise RuntimeError(f"HTTP {e.code}: {e.read()[:300]!r}")
        except (urllib.error.URLError, TimeoutError):
            if k < intentos - 1:
                time.sleep(min(60, 2 ** k + random.random()))
                continue
            raise


def fila_de_respuesta(base, mensaje):
    """Convierte una respuesta de la API en la fila que se guarda (salida sin editar y su lectura)."""
    texto = "".join(b.get("text", "") for b in mensaje.get("content", []) if b.get("type") == "text")
    j, problema = leer_json(texto)
    return dict(base, modelo_respondio=mensaje.get("model"), id_respuesta=mensaje.get("id"), salida=texto, json=j,
                problema=problema, uso=mensaje.get("usage"))


def ultimas(sal):
    """Última fila guardada de cada texto (si una petición falló y se repitió, cuenta la más reciente)."""
    ult = {}
    if sal.exists():
        for l in sal.read_text(encoding="utf-8").splitlines():
            if l.strip():
                r = json.loads(l)
                ult[r["id"]] = r
    return ult


def guardar(sal, filas):
    with sal.open("a", encoding="utf-8") as f:
        for fila in filas:
            f.write(json.dumps(fila, ensure_ascii=False) + "\n")


def enviar_directo(clave, a, base, pendientes, sistema, plantilla, sal):
    """Una petición tras otra; la caché de 5 minutos se mantiene porque las peticiones son seguidas."""
    for n, (ident, ant, reg, pos) in enumerate(pendientes, 1):
        b = dict(base, id=ident, via="directo", fecha=ahora())
        try:
            r = api(clave, "POST", "/messages", peticion(a.modelo, sistema, plantilla, ant, reg, pos, "5m"))
            fila = fila_de_respuesta(b, r)
        except Exception as e:
            fila = dict(b, salida=None, json=None, problema=f"error: {e}")
        guardar(sal, [fila])
        if n % 25 == 0:
            print(f"  {n}/{len(pendientes)}")
        time.sleep(a.pausa)
    return True


def enviar_lotes(clave, a, base, pendientes, sistema, plantilla, sal):
    """Crea el lote o, si ya existe, consulta su estado y descarga los resultados. Devuelve True si terminó."""
    estado_f = sal.with_suffix(".lote.json")
    if estado_f.exists():
        estado = json.loads(estado_f.read_text(encoding="utf-8"))
    else:
        if not pendientes:
            return True
        # Crea el lote con todas las peticiones pendientes (caché de 1 hora, porque el lote puede tardar)
        req = [{"custom_id": ident, "params": peticion(a.modelo, sistema, plantilla, ant, reg, pos, "1h")}
               for ident, ant, reg, pos in pendientes]
        r = api(clave, "POST", "/messages/batches", {"requests": req})
        estado = {"id": r["id"], "creado": ahora(), "peticiones": len(req), "modelo": a.modelo}
        estado_f.write_text(json.dumps(estado, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Lote creado: {r['id']} con {len(req)} peticiones.")
    # Consulta el estado hasta que termine (con --esperar) o una sola vez
    while True:
        r = api(clave, "GET", f"/messages/batches/{estado['id']}")
        print(f"Lote {estado['id']}: {r['processing_status']} · {r['request_counts']}")
        if r["processing_status"] == "ended":
            break
        if not a.esperar:
            print("Vuelve a correr el mismo comando más tarde para descargar los resultados.")
            return False
        time.sleep(60)
    # Descarga los resultados y los guarda; los que fallaron se vuelven a pedir en la siguiente ejecución
    filas = []
    for l in api(clave, "GET", r["results_url"], crudo=True).splitlines():
        if not l.strip():
            continue
        res = json.loads(l)
        b = dict(base, id=res["custom_id"], via="lote", id_lote=estado["id"], fecha=ahora())
        if res["result"]["type"] == "succeeded":
            filas.append(fila_de_respuesta(b, res["result"]["message"]))
        else:
            detalle = res["result"].get("error", res["result"]["type"])
            filas.append(dict(b, salida=None, json=None, problema=f"error: {detalle}"))
    guardar(sal, filas)
    estado_f.rename(estado_f.with_name(estado_f.stem + f".{estado['id']}.terminado.json"))
    print(f"Resultados descargados: {len(filas)}.")
    return True


INSTRUCCIONES_AGENTE = """Eres un codificador independiente. Tus instrucciones de codificación son el MENSAJE DE SISTEMA de abajo,
que incluye el libro de códigos completo: aplícalo tal cual. Trabajas A CIEGAS: lee solo este archivo y el archivo de
grupo que se te indique; no abras ningún otro archivo ni uses conocimiento externo sobre los casos.

El archivo de grupo es un JSON con una lista de unidades; cada una tiene id, anterior, registro y posterior. Codifica
cada unidad de forma independiente, como si fuera la única: lo que hayas decidido en otra unidad no cuenta.

SALIDA: escribe con la herramienta Write el archivo de salida que se te indique, en formato JSON Lines: una línea por
unidad, en el mismo orden, con el objeto JSON del FORMATO DE SALIDA más el campo "id" al principio, por ejemplo
{"id": "M001", "t1": "si", "t2": "no", "t3": "no", "codigo": "generica", "criterio_judicial": "no", "duda": null}
Al terminar responde solo cuántas líneas escribiste.

=== MENSAJE DE SISTEMA ===

"""


def preparar_agentes(a, lista, sistema, plantilla):
    """Divide los textos en grupos fijos (en el orden de la lista) y escribe las instrucciones y los archivos de grupo."""
    d = AQUI / "data/clasificacion" / f"agentes_{a.modo}_corrida{a.corrida}"
    d.mkdir(parents=True, exist_ok=True)
    (d / "instrucciones.txt").write_text(INSTRUCCIONES_AGENTE + sistema + "\n", encoding="utf-8")
    grupos = [lista[k:k + a.tam_grupo] for k in range(0, len(lista), a.tam_grupo)]
    for g, grupo in enumerate(grupos, 1):
        datos = [{"id": i, "anterior": ant or "(no hay)", "registro": reg, "posterior": pos or "(no hay)"}
                 for i, ant, reg, pos in grupo]
        (d / f"grupo_{g:02d}.json").write_text(json.dumps(datos, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{len(grupos)} grupos de hasta {a.tam_grupo} textos en {d.relative_to(AQUI)}; cada agente escribe "
          f"grupo_NN.salida.jsonl.")


def recoger_agentes(a, base, sal):
    """Lee las salidas de los agentes, las valida con la regla del libro y las guarda en el formato de la API."""
    d = AQUI / "data/clasificacion" / f"agentes_{a.modo}_corrida{a.corrida}"
    filas = []
    for f in sorted(d.glob("grupo_*.salida.jsonl")):
        for l in f.read_text(encoding="utf-8").splitlines():
            if not l.strip():
                continue
            try:
                obj = json.loads(l)
                ident = obj.pop("id")
            except (ValueError, KeyError):
                continue
            texto = json.dumps(obj, ensure_ascii=False)
            j, problema = leer_json(texto)
            filas.append(dict(base, id=ident, via="agente", grupo=f.name.split(".")[0], fecha=ahora(),
                              modelo_respondio=a.modelo + " (subagente de Claude Code)", salida=texto, json=j,
                              problema=problema, uso=None))
    guardar(sal, filas)
    print(f"Recogidas {len(filas)} salidas de {d.relative_to(AQUI)}.")


def main():
    # Lee el modo, la corrida, el modelo y la forma de envío de la línea de comandos
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("modo", choices=["muestra", "todo"])
    ap.add_argument("--corrida", type=int, default=1)
    ap.add_argument("--modelo", default="claude-opus-5-5")
    ap.add_argument("--lotes", action="store_true", help="envía por la Message Batches API (mitad de precio)")
    ap.add_argument("--esperar", action="store_true", help="con --lotes, consulta cada minuto hasta que termine")
    ap.add_argument("--pausa", type=float, default=0.5, help="envío directo: segundos entre peticiones")
    ap.add_argument("--simular", action="store_true", help="arma las peticiones sin enviarlas")
    ap.add_argument("--agentes", choices=["preparar", "recoger"],
                    help="sin API: prepara grupos para subagentes de Claude Code o recoge sus salidas")
    ap.add_argument("--tam-grupo", type=int, default=25, help="con --agentes preparar: textos por agente")
    a = ap.parse_args()
    clave = os.environ.get("ANTHROPIC_API_KEY", "")
    if not a.simular and not a.agentes and not clave:
        sys.exit("Falta la variable de entorno ANTHROPIC_API_KEY.")

    # Prepara el prompt, la lista de textos y el archivo de salida; pendientes = sin salida o con error
    sistema, plantilla = partes_del_prompt()
    lista = textos(a.modo)
    sal = AQUI / "data/clasificacion" / f"{a.modo}_corrida{a.corrida}.jsonl"
    ult = ultimas(sal)
    pendientes = [t for t in lista if t[0] not in ult or str(ult[t[0]].get("problema", "")).startswith("error")]
    print(f"{a.modo}, corrida {a.corrida}: {len(lista)} textos, {len(lista) - len(pendientes)} ya clasificados, "
          f"{len(pendientes)} pendientes")
    if a.agentes == "preparar":
        preparar_agentes(a, lista, sistema, plantilla)
        return
    if a.simular:
        p = peticion(a.modelo, sistema, plantilla, *pendientes[0][1:], "1h" if a.lotes else "5m") if pendientes else None
        if p:
            print(json.dumps(p, ensure_ascii=False)[:900])
        print(f"Simulación: se habrían enviado {len(pendientes)} peticiones ({'lote' if a.lotes else 'directo'}).")
        return
    sal.parent.mkdir(parents=True, exist_ok=True)
    base = {"modo": a.modo, "corrida": a.corrida, "modelo_pedido": a.modelo, "temperatura": TEMPERATURA,
            "max_tokens": MAX_TOKENS, "prompt_sha256": hashlib.sha256(PROMPT.read_bytes()).hexdigest()}

    # Clasifica por la vía elegida (o recoge lo que escribieron los subagentes)
    if a.agentes == "recoger":
        base.update(temperatura="no controlada (subagente)", max_tokens=None)
        recoger_agentes(a, base, sal)
    else:
        enviar = enviar_lotes if a.lotes else enviar_directo
        if not enviar(clave, a, base, pendientes, sistema, plantilla, sal):
            return

    # Escribe el CSV de códigos (id_muestra, codigo, criterio_judicial) que lee alfa.py y resume el uso de tokens
    ult = ultimas(sal)
    with sal.with_suffix(".csv").open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["id_muestra", "codigo", "criterio_judicial", "problema"])
        for ident, *_ in lista:
            r = ult.get(ident, {})
            j = r.get("json") or {}
            w.writerow([ident, j.get("codigo", ""), j.get("criterio_judicial") or "", r.get("problema", "sin salida")])
    uso = {}
    for r in ult.values():
        for k, v in (r.get("uso") or {}).items():
            if isinstance(v, int):
                uso[k] = uso.get(k, 0) + v
    con_problema = sum(1 for r in ult.values() if r.get("problema"))
    faltan = len(lista) - len(ult)
    print(f"Listo: {len(ult)} textos con salida en {sal.name}; {con_problema} con algún problema (se revisan a mano); "
          f"{faltan} sin salida.\nUso de tokens: {uso}")


if __name__ == "__main__":
    main()
