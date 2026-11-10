# Corpus «inteligencia artificial» del Buscador de Sentencias del OAJ: protocolo de construcción y replicación

Entorno de prueba: MacBook Air, Apple Silicon (arm64), macOS 26.3 

Fecha de prueba: 02-10-2026.

Objetivo y alcance. Este documento describe el procedimiento para construir y replicar un corpus de sentencias que contienen la frase «inteligencia artificial», recuperadas del Buscador de Sentencias (SISE) del Órgano de Administración Judicial (OAJ). El procedimiento comprende cuatro fases: (1) listado de los asuntos que devuelve el buscador, (2) descarga de los documentos, (3) conversión a texto y (4) análisis de las menciones. El corte original se realizó el 29-sep-2026 y comprende 1,283 sentencias. Los pasos están redactados para que cualquier persona, sin formación en programación, pueda reproducir el resultado siguiéndolos en orden.

Nota sobre la elaboración del código. El código de los anexos se desarrolló con asistencia de una herramienta de inteligencia artificial generativa Claude Code Opus 5.5. Para que su funcionamiento pueda auditarse con independencia de esa herramienta, el código se publica íntegro, las versiones de todas las dependencias están fijadas (anexo requirements-lock.txt) y cada archivo va acompañado de su huella SHA-256.

## Requisitos y fuentes de obtención

| # | Componente | Fuente | Procedimiento de obtención | Versión usada |
|---|---|---|---|---|
| 1 | Herramientas de línea de comandos | Apple | xcode-select --install | la que ofrezca Apple |
| 2 | Homebrew (gestor de programas) | brew.sh | comando del paso 1.2 | 5.1.10 |
| 3 | Python 3.12 | Homebrew | brew install python@3.12 | 3.12.13 |
| 4 | Librerías de Python | PyPI (pypi.org) | pip install -r requirements-lock.txt | exactas, ver anexo requirements-lock.txt |
| 5 | Navegador Chromium para Playwright | Servidores de Playwright (Microsoft) | playwright install chromium | build 1243 (Chrome 153) |
| 6 | Credenciales genéricas de acceso y direcciones de la API | Sitio web del OAJ | extraer_credenciales.py (paso 4) | vigentes al 02-10-2026, ya escritas en sise.py |
| 7 | El código | Este protocolo (anexos) | comando del paso 3 | huellas SHA-256 en cada anexo |
| 8 | Lista original de sentencias (opcional) | Carpeta Anexo 1/SubAnexos | metadata.jsonl y manifiesto.csv (ya incluidos) | corte 29-sep-2026 |

El componente 6 es el único que no se distribuye por canales públicos de software: se trata de credenciales genéricas y anónimas que la aplicación web del buscador (ejusticia.cjf.gob.mx/BuscadorSISE/) entrega a cualquier visitante, y el OAJ puede modificarlas sin previo aviso. Por ello, el paso 4 consulta la página, extrae esos valores y los compara con los que contiene el código.

El componente 8 sólo es necesario para reproducir exactamente el corte original (29-sep-2026). Sus dos archivos (2 MB) se entregan en la carpeta Anexo 1/SubAnexos. Sin ellos, el paso 5 ejecuta una búsqueda nueva y recupera el universo de sentencias vigente en la fecha de ejecución.

**Contenido del Anexo 1.** La carpeta Anexo 1 contiene PROTOCOLO.docx (este documento); PROTOCOLO.md (el mismo protocolo en formato Markdown, del que el paso 3 extrae el código), y la carpeta SubAnexos con: raw/ (los 1,281 PDF del corte, tal como los publica el OAJ), txt/ (su conversión a texto limpio), manifiesto.csv (huella SHA-256, páginas, palabras y menciones de cada documento) y metadata.jsonl (los datos de las 1,283 sentencias del corte). Las carpetas raw/ y txt/ permiten consultar el corpus sin volver a descargarlo; no hacen falta para verificar una réplica, porque manifiesto.csv conserva sus huellas.

## Paso 1. Preparación del entorno de cómputo (una sola vez, ~15 min)

Abrir la aplicación Terminal y ejecutar cada comando por separado.

Las líneas en morado que comienzan con # son explicativas y no se copian: zsh, el intérprete predeterminado de macOS, no las reconoce como comentarios al escribirlas en la Terminal. Copiar únicamente el comando que aparece debajo de cada una.

1.1 Herramientas de línea de comandos de Apple (se abre una ventana; aceptar e instalar):

```bash
# Instala las herramientas de línea de comandos de Apple (compilador, git, make)
xcode-select --install
```

1.2 Homebrew (solicita la contraseña del usuario de macOS):

```bash
# Descarga y ejecuta el instalador oficial de Homebrew, el gestor de paquetes de macOS
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

Al concluir, Homebrew imprime dos líneas bajo «Next steps» para añadirlo a la variable PATH; deben ejecutarse. En Apple Silicon son:

```bash
# Añade Homebrew al PATH de forma permanente (~/.zprofile) y en la sesión actual
echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile && eval "$(/opt/homebrew/bin/brew shellenv)"
```

1.3 Python 3.12:

```bash
# Instala Python 3.12 mediante Homebrew
brew install python@3.12
```

Comprobación:

```bash
# Comprueba que Python 3.12 quedó instalado e imprime su versión
/opt/homebrew/bin/python3.12 --version
```

La salida esperada es Python 3.12.x.

## Paso 2. Creación del directorio de trabajo

```bash
# Crea la carpeta de trabajo (si no existe) y entra en ella
mkdir -p ~/sentencias-ia && cd ~/sentencias-ia
```

Colocar dentro de esa carpeta la carpeta Anexo 1 recibida y copiar de ella PROTOCOLO.md, la versión Markdown de este protocolo. El código se extrae de PROTOCOLO.md y no de este documento de Word, porque Word puede alterar espacios y renglones vacíos. El comando supone que la carpeta Anexo 1 está en Descargas; si está en otro lugar, sustituir ~/Downloads por esa ruta:

```bash
# Copia la carpeta Anexo 1 desde Descargas y extrae PROTOCOLO.md a la carpeta de trabajo
cp -R ~/Downloads/"Anexo 1" ~/sentencias-ia/ && cp ~/sentencias-ia/"Anexo 1"/PROTOCOLO.md ~/sentencias-ia/
```

A partir de aquí, todos los comandos se ejecutan dentro de ~/sentencias-ia.

## Paso 3. Extracción del código y verificación de integridad

Este comando lee los anexos de PROTOCOLO.md y genera cada archivo (sise.py, analisis.py, etc.) con su contenido exacto:

```bash
# Lee PROTOCOLO.md, localiza cada bloque marcado como «archivo:» y escribe el archivo con su contenido exacto
cd ~/sentencias-ia && /usr/bin/python3 -c 'import re,pathlib;t=pathlib.Path("PROTOCOLO.md").read_text(encoding="utf-8");[(pathlib.Path(n).write_text(c+"\n",encoding="utf-8"),print("creado",n)) for n,c in re.findall(r"<!-- archivo: (\S+) -->\n````[a-z]*\n(.*?)\n````",t,re.S)]'
```

Verificar la integridad de los archivos generados: el comando calcula la huella SHA-256 de cada uno y la busca en su anexo. Los seis deben aparecer como «coincide»:

```bash
# Calcula la huella SHA-256 de cada archivo y verifica que aparezca en PROTOCOLO.md
for f in sise.py analisis.py comparar.py obsidian.py extraer_credenciales.py requirements-lock.txt; do grep -q "$(shasum -a 256 "$f" | cut -c1-64)" PROTOCOLO.md && echo "coincide: $f" || echo "NO COINCIDE: $f"; done
```

Crear un entorno virtual de Python e instalar las versiones exactas de las librerías:

```bash
# Crea el entorno virtual .venv e instala las versiones fijadas en requirements-lock.txt
/opt/homebrew/bin/python3.12 -m venv .venv && .venv/bin/pip install -r requirements-lock.txt
```

Instalar el navegador que utiliza Playwright (sólo se requiere en el paso 4; ~100 MB):

```bash
# Descarga el navegador Chromium que usa Playwright (sólo para el paso 4)
.venv/bin/python -m playwright install chromium
```

## Paso 4. Verificación de los parámetros de acceso al servicio del OAJ

```bash
# Abre el buscador en un navegador automatizado y compara las credenciales con las de sise.py
.venv/bin/python extraer_credenciales.py
```

El script abre la página del buscador en un navegador sin interfaz gráfica (headless), ejecuta la búsqueda, solicita un documento y registra los parámetros que la página transmite al servidor. Resultado esperado:

```
 CLIENTE_APISISE.ClientID       igual
  CLIENTE_APISISE.ClientSecret   igual
  BASIC_LOGIN_DOC                igual
  URL_LOGIN_DOC                  igual
  URL_SENTENCIA                  igual
```

- **Si todos los valores aparecen como «igual», continuar con el** paso 5.
- **Si algún valor aparece como «DISTINTO», abrir sise.py, localizar la constante correspondiente (todas se encuentran al inicio del archivo) y sustituir su valor por el** que imprime el script.
- **Si aparece «no capturado» o un error, la página modificó su diseño. En ese caso, realizar la búsqueda manualmente** en Chrome con las herramientas de desarrollador abiertas (Cmd+Opción+I → pestaña *Network*), descargar una sentencia y localizar las peticiones a IdentityManager/token, por-sentencia/buscar, Login/Safe/System y wsSentenceFinder, que contienen los valores.
## Paso 5. Recolección, conversión a texto y análisis del corpus

Prueba piloto (1–3 min, 3 sentencias):

```bash
# Prueba piloto: lista, descarga y convierte a texto sólo 3 sentencias
.venv/bin/python sise.py todo --limite 3
```

La salida debe incluir token de apisise obtenido, página 1/52, tres PDF descargados y texto: 3 convertidos. A continuación, eliminar los datos de prueba:

```bash
# Elimina los datos de la prueba piloto
rm -rf data
```

**Verificación rápida (opcional, ~5 min)** — descarga 10 sentencias al azar del corte original y las compara con sus huellas antes de emprender la corrida completa de 3–4 h:

```bash
# Copia el corte original, descarga y convierte 10 sentencias al azar, calcula relevancia y compara
mkdir -p data && cp "Anexo 1/SubAnexos/metadata.jsonl" "Anexo 1/SubAnexos/manifiesto.csv" data/ && .venv/bin/python sise.py descargar --muestra 10 && .venv/bin/python sise.py texto --muestra 10 && .venv/bin/python analisis.py relevancia && .venv/bin/python comparar.py ~/sentencias-ia
```

El resultado debe mostrar «idéntico 10 (100.0% de los comparables)» en las secciones 2 y 3, y «palabras y menciones idénticas» en la sección 4. Después, eliminar la prueba:

```bash
# Elimina los datos de la verificación rápida
rm -rf data
```

**Opción A — replicación exacta del corte del 29-sep-2026** (requiere el componente 8):

```bash
# Opción A: copia el corte original y descarga/convierte exactamente esas sentencias (caffeinate evita el reposo)
mkdir -p data && cp "Anexo 1/SubAnexos/metadata.jsonl" "Anexo 1/SubAnexos/manifiesto.csv" data/ && caffeinate -i .venv/bin/python sise.py descargar && .venv/bin/python sise.py texto
```

**Opción B — búsqueda nueva** (universo vigente en la fecha de ejecución):

```bash
# Opción B: ejecuta la búsqueda completa desde cero (listar, descargar y convertir)
caffeinate -i .venv/bin/python sise.py todo
```

La ejecución tarda ~3–4 h, porque el programa espacia las peticiones entre 1.5 y 2 s para no sobrecargar el servidor público. El comando caffeinate impide que la Mac entre en reposo. Si el proceso se interrumpe, basta con ejecutar de nuevo el mismo comando: se reanuda a partir de los archivos ya obtenidos.

Análisis del corpus y generación de la bóveda de Obsidian:

```bash
# Calcula el índice de relevancia, genera el resumen del corpus y crea la bóveda de Obsidian
.venv/bin/python analisis.py relevancia && .venv/bin/python analisis.py resumen && .venv/bin/python obsidian.py
```

## Paso 6. Validación de la réplica

Con la opción A, comparar la réplica con las huellas del corpus original:

```bash
# Compara la réplica contra las huellas del corpus original
.venv/bin/python comparar.py ~/sentencias-ia
```

(Si el manifiesto original se encuentra en data/, comparar.py reporta cuántos PDF y textos coinciden byte a byte.)

Valores de referencia del corte original (29-sep-2026):

| Dato | Valor |
|---|---|
| Asuntos que reporta el buscador | 1,280 |
| Sentencias listadas (únicas) | 1,283 |
| PDF descargados | 1,281 (2 exigen solicitud de transparencia) |
| Palabras en total | 29.75 millones |
| Clase de mención: sustantiva / machote / sin menciones | 661 / 601 / 19 |

Con la opción B, el total será mayor (el 2-oct-2026 ya eran 1,291), pues el índice del buscador se actualiza continuamente.

Criterio de clasificación de menciones. Una mención se considera sustantiva cuando el párrafo que la contiene no corresponde a ninguno de los textos de formato (machotes) identificados en analisis.py, como el aviso de que la síntesis ciudadana fue creada con inteligencia artificial o las fórmulas sobre el uso de la videoconferencia. Una sentencia se clasifica como sustantiva si contiene al menos una mención de ese tipo; como machote, si todas sus menciones aparecen en textos de formato, y sin menciones, si no se detecta ninguno de los términos buscados.

## Solución de problemas frecuentes

| Síntoma | Causa | Solución |
|---|---|---|
| zsh: no such file or directory: .venv/bin/python | La terminal no está ubicada en el directorio del proyecto | cd ~/sentencias-ia |
| command not found: brew | No se ejecutó la configuración de PATH de Homebrew | Repetir el comando de 1.2 que empieza con echo 'eval |
| HTTP 401 repetido | Credenciales cambiadas | Paso 4 |
| VIGILANTE: petición colgada… reinicio el proceso | Una conexión dejó de responder | Comportamiento previsto: el proceso se cierra. Ejecutar de nuevo el comando para reanudar |
| el servicio no entregó documento: … Ley Federal de Transparencia | La versión pública sólo se entrega mediante solicitud de acceso a la información | Se registra en data/errores.csv; no es un fallo del programa |
| La huella SHA-256 de un archivo del paso 3 no coincide | El protocolo se alteró al copiarlo | Obtener de nuevo la versión original del protocolo |

## Anexos: código fuente

Cada anexo contiene un archivo completo. El comando del paso 3 los extrae automáticamente; no es necesario copiarlos a mano.

### Anexo · requirements-lock.txt

Versiones exactas de las librerías (componente 4). SHA-256: 4eedb7a8248047a5f682c45d99f838c94a47936da53f0a88826e1f5bb20a13fa

<!-- archivo: requirements-lock.txt -->
````text
certifi==2026.7.22
charset-normalizer==3.5.1
greenlet==3.5.6
idna==3.20
lxml==6.1.3
playwright==1.63.0
pyee==13.0.1
pymupdf==1.28.2
python-docx==1.2.0
requests==2.34.2
typing_extensions==4.16.0
urllib3==2.8.0
````

### Anexo · sise.py

Listado, descarga y conversión a texto de las sentencias. Las credenciales del OAJ se definen al inicio del archivo. SHA-256: 7bc58b28c89321b9d963788f5e64cb3c2d6595c6b5f9d5899abe5e911cd4f20a

<!-- archivo: sise.py -->
````python
#!/usr/bin/env python3
"""Descarga y convierte a texto las sentencias de una búsqueda del Buscador SISE (OAJ).

Uso:
    python sise.py listar     [--limite N]   # data/metadata.jsonl
    python sise.py descargar  [--limite N]   # data/raw/{id}.{ext}
    python sise.py texto      [--limite N]   # data/txt/{id}.txt  (+ data/sin_texto.csv)
    python sise.py todo       [--limite N]   # las tres fases seguidas
    python sise.py descargar --muestra 50 --semilla 2026   # muestra aleatoria reproducible

Requiere macOS o Linux (en Windows, usar WSL): el vigilante de peticiones usa SIGALRM.

Todas las fases se pueden reanudar: lo que ya existe se salta.
El servidor es público: todo es secuencial, con 1.5–2 s entre peticiones.
"""
import argparse
import base64
import csv
import json
import os
import threading
import random
import re
import signal
import sys
import time
from collections import Counter
from datetime import datetime
from pathlib import Path

import requests

BASE = Path(__file__).resolve().parent
DATA = BASE / "data"
RAW, TXT = DATA / "raw", DATA / "txt"
METADATA = DATA / "metadata.jsonl"
ERRORES = DATA / "errores.csv"
SIN_TEXTO = DATA / "sin_texto.csv"

FRASE = "inteligencia artificial"
TAM_PAGINA = 25

API = "https://apisise.cjf.gob.mx"
# Credenciales genéricas y anónimas que el propio SPA entrega a cualquier visitante.
CLIENTE_APISISE = {
    "ClientID": "CJF_DGETD_BSS_Gen",
    "ClientSecret": "NpyYcnNt62j8Et5+&J4gFnwgHAYV#Vzt",
    "data": {"IdPerspectiva": "EXT", "NombreUsuario": "generico", "idOrgano": "",
             "IdSistemaCredGen": "9", "IdEmpleado": "", "IdCargo": ""},
}
URL_LOGIN_DOC = "https://serviciossige.oaj.gob.mx/wsConfiguration/api/Login/Safe/System"
BASIC_LOGIN_DOC = "Basic QlNfU0lTRTpzQDVHXkZ2dWF+WypnWnhOdU1VK0JMdw=="
URL_SENTENCIA = "https://serviciosvistaee.cjf.gob.mx/wsSentenceFinder/api/Sentencia"

PAUSA = (1.5, 2.0)
REINTENTABLES = {429, 500, 502, 503, 504}
MAX_INTENTOS = 6


def log(msg):
    print(f"[{datetime.now():%H:%M:%S}] {msg}", flush=True)


def registrar_error(id_, etapa, detalle):
    nuevo = not ERRORES.exists()
    with ERRORES.open("a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if nuevo:
            w.writerow(["fecha", "id", "etapa", "detalle"])
        w.writerow([datetime.now().isoformat(timespec="seconds"), id_, etapa, str(detalle)[:500]])
    log(f"  ERROR {id_} [{etapa}]: {str(detalle)[:200]}")


def escribir_atomico(path: Path, contenido: bytes):
    """Escribe a un .part y renombra: un archivo a medias nunca cuenta como 'ya descargado'."""
    tmp = path.with_suffix(path.suffix + ".part")
    tmp.write_bytes(contenido)
    tmp.replace(path)


def exp_jwt(token):
    try:
        payload = token.split(".")[1]
        payload += "=" * (-len(payload) % 4)
        return int(json.loads(base64.urlsafe_b64decode(payload))["exp"])
    except Exception:
        return 0


class ErrorHTTP(Exception):
    pass


class PeticionColgada(Exception):
    pass


def _alarma(signum, frame):
    raise PeticionColgada("la petición excedió su tiempo total")


# ───────────────────────────── cliente HTTP ─────────────────────────────

class Cliente:
    def __init__(self):
        self.s = requests.Session()
        self.s.headers.update({
            "Origin": "https://ejusticia.cjf.gob.mx",
            "Referer": "https://ejusticia.cjf.gob.mx/",
            "User-Agent": "Mozilla/5.0 (investigacion academica; descarga secuencial)",
            "Accept": "application/json, text/plain, */*",
        })
        self._ultima = 0.0
        self._token = None
        self._token_exp = 0
        # vigilante: si una petición sigue en vuelo después de su límite, termina el proceso
        # (el envoltorio lo relanza y todo se reanuda). Hace falta porque a veces un socket
        # TLS se queda bloqueado sin timeout y ni la alarma lo interrumpe.
        self._en_vuelo = None
        threading.Thread(target=self._vigilar, daemon=True).start()

    def _vigilar(self):
        while True:
            time.sleep(15)
            v = self._en_vuelo
            if v and time.monotonic() - v[0] > v[1]:
                log(f"  VIGILANTE: petición colgada {int(time.monotonic() - v[0])}s en {v[2]}; reinicio el proceso")
                os._exit(75)

    def _pausa(self):
        falta = random.uniform(*PAUSA) - (time.monotonic() - self._ultima)
        if falta > 0:
            time.sleep(falta)

    def pedir(self, metodo, url, auth=None, timeout=60, **kw):
        """Petición con pausa, reintentos con espera creciente ante 429/5xx/red,
        y renovación del token de apisise si responde 401.

        auth: callable que devuelve el header Authorization (se evalúa en cada intento).
        """
        ultimo = None
        fijos = dict(kw.pop("headers", None) or {})
        for intento in range(MAX_INTENTOS):
            self._pausa()
            headers = dict(fijos)
            if auth:
                headers["Authorization"] = auth()
            # el timeout de requests es entre bytes, no total: un socket a medio morir puede
            # colgar la lectura indefinidamente; la alarma pone un tope duro por petición
            signal.signal(signal.SIGALRM, _alarma)
            signal.alarm(timeout * 2 + 30)
            self._en_vuelo = (time.monotonic(), timeout * 2 + 90, url.split("?")[0])
            try:
                r = self.s.request(metodo, url, headers=headers, timeout=(15, timeout), **kw)
            except (requests.ConnectionError, requests.Timeout, PeticionColgada) as e:
                ultimo = f"red: {e.__class__.__name__}"
                r = None
                self.s.close()  # descarta conexiones del pool que pudieran estar muertas
            finally:
                signal.alarm(0)
                self._en_vuelo = None
                self._ultima = time.monotonic()
            if r is not None:
                if r.status_code < 400:
                    return r
                ultimo = f"HTTP {r.status_code}"
                if r.status_code == 401 and auth is self.auth_apisise:
                    log("  token vencido/rechazado; renovando")
                    self._token = None
                elif r.status_code not in REINTENTABLES:
                    raise ErrorHTTP(f"{ultimo} en {url.split('?')[0]}: {r.text[:200]}")
            espera = min(5 * 2 ** intento, 300)
            if r is not None and r.headers.get("Retry-After", "").isdigit():
                espera = max(espera, int(r.headers["Retry-After"]))
            if intento < MAX_INTENTOS - 1:
                log(f"  {ultimo}; reintento {intento + 1} en {espera}s")
                time.sleep(espera)
        raise ErrorHTTP(f"{ultimo} tras {MAX_INTENTOS} intentos en {url.split('?')[0]}")

    # token de apisise (8 h); se renueva si faltan menos de 5 min o si llega un 401
    def auth_apisise(self):
        if not self._token or time.time() > self._token_exp - 300:
            self._pausa()
            signal.signal(signal.SIGALRM, _alarma)
            signal.alarm(150)
            self._en_vuelo = (time.monotonic(), 210, "token")
            try:
                r = self.s.put(f"{API}/IdentityManager/token/", json=CLIENTE_APISISE, timeout=(15, 60))
            finally:
                signal.alarm(0)
                self._en_vuelo = None
            self._ultima = time.monotonic()
            r.raise_for_status()
            self._token = r.json()["token"]
            self._token_exp = exp_jwt(self._token) or time.time() + 3600
            log("  token de apisise obtenido")
        return "Bearer " + self._token

    def buscar(self, pagina):
        filtro = {"ValorCondicion": FRASE, "CondicionOperador": 1, "IdTipoCampo": 1}
        body = {"FiltrosPrimarios": {"Contenido": filtro, "Tema": filtro},
                "Paginate": {"page": pagina, "size": TAM_PAGINA}}
        r = self.pedir("POST", f"{API}/bss/por-sentencia/buscar/", auth=self.auth_apisise, json=body)
        j = r.json()
        if not j.get("success"):
            raise ErrorHTTP(f"búsqueda sin éxito: {j.get('message')}")
        return j["data"]

    def sintesis(self, neun, sintesis_orden):
        r = self.pedir("POST", f"{API}/bss/sintesis/", auth=self.auth_apisise,
                       json={"AsuntoNeunId": neun, "SintesisOrden": sintesis_orden})
        j = r.json()
        return j.get("data") if j.get("success") else None

    def documento(self, rec):
        """Devuelve los bytes del documento: login por documento → Sentencia → URL o base64."""
        login = self.pedir("POST", URL_LOGIN_DOC, headers={"Authorization": BASIC_LOGIN_DOC}, json={
            "System": "5", "IdUser": "0", "IdPerspectiva": "EXT", "NombreUsuario": "Generico",
            "IdOrgano": "0", "Neun": str(rec["neun"]), "Modulo": "2",
            "SintesisOrden": str(rec["sintesis_orden"]), "NumeroOrden": str(rec["numero_orden"]),
        }).json()
        tok = login.get("token")
        if not tok:
            raise ErrorHTTP(f"login de documento sin token: {str(login)[:200]}")
        j = self.pedir("GET", URL_SENTENCIA, headers={"Authorization": "Bearer " + tok}).json()
        d = j.get("data") or {}
        if d.get("fileBase64"):
            return base64.b64decode(d["fileBase64"]), d.get("sNombreArchivo")
        if d.get("sURLVesionPublica"):
            r = self.pedir("GET", d["sURLVesionPublica"], timeout=180)
            return r.content, r.headers.get("content-disposition")
        raise ErrorHTTP(f"el servicio no entregó documento: {str(j)[:300]}")


# ───────────────────────────── fase 1: listado ─────────────────────────────

def cargar_metadata():
    if not METADATA.exists():
        return []
    return [json.loads(l) for l in METADATA.read_text(encoding="utf-8").splitlines() if l.strip()]


def fecha_iso(ddmmyyyy):
    try:
        return datetime.strptime(ddmmyyyy, "%d-%m-%Y").date().isoformat()
    except (TypeError, ValueError):
        return ddmmyyyy


def fase_listar(cli, limite=None):
    DATA.mkdir(exist_ok=True)
    existentes = cargar_metadata()
    # clave estable de un documento: un NEUN puede tener varias sentencias (NumeroOrden)
    por_clave = {(r["neun"], r["numero_orden"], r["sintesis_orden"]): r["id"] for r in existentes}
    ids_usados = {r["id"] for r in existentes}
    log(f"metadata existente: {len(existentes)} registros")

    filas, pagina, total = [], 1, None
    while True:
        data = cli.buscar(pagina)
        pag = data["paginate"]
        total = pag["total_hits"]
        filas += data["datosTabla"]
        log(f"página {pagina}/{pag['total_pages']} — {len(filas)}/{total} filas")
        if (limite and len(filas) >= limite) or not pag.get("next_page"):
            break
        pagina += 1
    if limite:
        filas = filas[:limite]

    nuevos = 0
    with METADATA.open("a", encoding="utf-8") as f:
        for i, x in enumerate(filas):
            neun = x["AsuntoNeunId"]
            clave = (neun, x.get("NumeroOrden"), x.get("SintesisOrden"))
            if clave in por_clave:
                continue
            id_ = str(neun) if str(neun) not in ids_usados else f"{neun}_{x.get('NumeroOrden')}"
            sint = x.get("Sintesis") or ""
            if len(sint) >= 250:  # el listado la trunca a 250 caracteres
                try:
                    sint = cli.sintesis(neun, x.get("SintesisOrden")) or sint
                except ErrorHTTP as e:
                    registrar_error(id_, "sintesis", e)
            dg = x.get("DatosGenerales") or {}
            rec = {
                "id": id_, "neun": neun, "expediente": x.get("NumeroAlias"),
                "organo": x.get("OrganoNombreOficial") or dg.get("NombreOrgano"),
                "titular": dg.get("Titular"), "tipo_organo": x.get("OrganoTipo"),
                "circuito": x.get("CircuitoRegion"), "especialidad_organo": x.get("EspecialidadOrgano"),
                "tipo_asunto": x.get("TipoAsunto"), "materia": x.get("Materia"),
                "fecha": fecha_iso(x.get("FechaDeLaSentencia")), "tema": x.get("Tema"),
                "sintesis": sint, "numero_orden": x.get("NumeroOrden"),
                "sintesis_orden": x.get("SintesisOrden"), "coincidencia": x.get("highlight"),
            }
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            f.flush()
            por_clave[clave] = id_
            ids_usados.add(id_)
            nuevos += 1
            if nuevos % 25 == 0:
                log(f"  {i + 1}/{len(filas)} asuntos procesados")
    repetidos = len(filas) - len({(x["AsuntoNeunId"], x.get("NumeroOrden"), x.get("SintesisOrden")) for x in filas})
    log(f"listado: total del buscador {total}; filas leídas {len(filas)}; nuevas {nuevos}; "
        f"filas duplicadas en el listado {repetidos}")


# ───────────────────────────── fase 2: descarga ─────────────────────────────

def extension(contenido: bytes, pista=None):
    if contenido[:4] == b"%PDF":
        return "pdf"
    if contenido[:2] == b"PK":
        return "docx"
    if contenido[:4] == b"\xd0\xcf\x11\xe0":
        return "doc"
    if contenido[:5] == b"{\\rtf":
        return "rtf"
    m = re.search(r"\.(\w{2,5})\W*$", pista or "")
    return m.group(1).lower() if m else None


def ya_descargado(id_):
    return any(p.suffix != ".part" for p in RAW.glob(f"{id_}.*"))


def seleccionar(limite=None, muestra=None, semilla=None):
    """Registros a procesar: todos, los primeros N (--limite) o una muestra aleatoria
    reproducible (--muestra N --semilla S): la misma semilla da la misma muestra."""
    recs = cargar_metadata()
    if muestra:
        recs = random.Random(semilla).sample(recs, min(muestra, len(recs)))
    elif limite:
        recs = recs[:limite]
    return recs


def fase_descargar(cli, limite=None, muestra=None, semilla=None):
    RAW.mkdir(parents=True, exist_ok=True)
    recs = seleccionar(limite, muestra, semilla)
    pendientes = [r for r in recs if not ya_descargado(r["id"])]
    log(f"descarga: {len(recs)} en metadata, {len(recs) - len(pendientes)} ya estaban, {len(pendientes)} pendientes")
    ok = 0
    for i, rec in enumerate(pendientes, 1):
        try:
            contenido, pista = cli.documento(rec)
            ext = extension(contenido, pista)
            if not ext or contenido[:1] == b"<":
                raise ErrorHTTP(f"respuesta no es un documento (inicio: {contenido[:40]!r})")
            escribir_atomico(RAW / f"{rec['id']}.{ext}", contenido)
            ok += 1
            log(f"{i}/{len(pendientes)} {rec['id']}.{ext} ({len(contenido) / 1e6:.1f} MB)")
        except (ErrorHTTP, requests.RequestException, ValueError, KeyError) as e:
            registrar_error(rec["id"], "descarga", e)
    log(f"descarga terminada: {ok} nuevas, {len(pendientes) - ok} con error")


# ───────────────────────────── fase 3: texto ─────────────────────────────

LEYENDA = re.compile(r"versi[oó]n\s+p[uú]blica|clasificad|confidencial|reservad|transparencia|suprimi|testad",
                     re.I)
NUM_PAGINA = re.compile(r"^(p[aá]g(ina)?\.?\s*)?#+(\s*(de|/)\s*#+)?$", re.I)
FIN_ORACION = re.compile(r"[.:;!?)\]»”\"]$")


def _norm(s):
    return re.sub(r"\s+", " ", re.sub(r"\d+", "#", s.lower())).strip()


def _lineas_visuales(pagina):
    """Reagrupa los spans de la página en renglones visuales por su altura (y).

    Los PDF de Word con texto justificado traen cada palabra como un renglón aparte;
    agruparlas por coordenada y reconstruye el renglón real.
    """
    import pymupdf
    d = pagina.get_text("dict", flags=pymupdf.TEXT_PRESERVE_WHITESPACE | pymupdf.TEXT_MEDIABOX_CLIP)
    spans, verticales = [], []
    for b in d["blocks"]:
        if b.get("type") != 0:
            continue
        for l in b["lines"]:
            horizontal = abs(l["dir"][1]) < 0.1 and l["dir"][0] > 0
            for s in l["spans"]:
                if not s["text"].strip():
                    continue
                if horizontal:
                    spans.append(s)
                else:
                    verticales.append(s["text"])
    spans.sort(key=lambda s: ((s["bbox"][1] + s["bbox"][3]) / 2, s["bbox"][0]))
    renglones = []
    for s in spans:
        cy = (s["bbox"][1] + s["bbox"][3]) / 2
        if renglones and abs(cy - renglones[-1]["cy"]) <= max(2.5, 0.35 * s["size"]):
            renglones[-1]["spans"].append(s)
        else:
            renglones.append({"cy": cy, "spans": [s]})
    lineas = []
    for r in renglones:
        ss = sorted(r["spans"], key=lambda s: s["bbox"][0])
        tam = max(s["size"] for s in ss)
        base = max(s["bbox"][3] for s in ss)
        texto = ""
        for j, s in enumerate(ss):
            t = s["text"]
            # llamadas de nota al pie en superíndice → [n]
            if t.strip().isdigit() and s["size"] <= 0.8 * tam and s["bbox"][3] < base - 0.2 * tam:
                t = f"[{t.strip()}]"
            elif j and s["bbox"][0] - ss[j - 1]["bbox"][2] > 0.15 * s["size"] \
                    and not texto.endswith(" ") and not t.startswith(" "):
                texto += " "
            texto += t
        texto = re.sub(r"\s+", " ", texto).strip()
        if texto:
            n = sum(len(s["text"]) for s in ss) or 1
            lineas.append({
                "texto": texto,
                "x0": min(s["bbox"][0] for s in ss), "x1": max(s["bbox"][2] for s in ss),
                "y0": min(s["bbox"][1] for s in ss), "y1": base,
                "tam": sum(s["size"] * len(s["text"]) for s in ss) / n,
            })
    vert = re.sub(r"\s+", " ", " ".join(verticales)).strip()
    return lineas, vert


HEX = re.compile(r"(?:\b[0-9a-f]{2}\b[ .:]?){8,}", re.I)
SELLO = re.compile(r"Datos estampillados:\s*\S+|Número de serie:\s*[0-9a-f.:]+", re.I)


def limpiar_firma(parrafo):
    """Quita los volcados hexadecimales de la evidencia de firma electrónica (FIREL):
    conserva quién firmó y cuándo, que sí sirve para el análisis."""
    sin_hex = SELLO.sub("", HEX.sub(" ", parrafo))
    return re.sub(r"\s{2,}", " ", sin_hex).strip()


RUIDO_FIRMA = re.compile(r"\bOCSP\b|\bTSP\b|RSA-SHA|Autoridad Certificadora|Archivo Firmado", re.I)


# Marcas inequívocas de la evidencia de firma electrónica (FIREL). Hay al menos tres formatos
# (2017 "Sha256withRSA", 2021 "RSA - SHA256" sin encabezado, 2026 "RSA-SHA256"), así que no se
# depende del encabezado sino de estas marcas, que no aparecen en prosa.
MARCA_FIRMA = re.compile(
    r"Algoritmo:\s*(RSA|Sha256)|Status:\s*(Bien|OK)\s+V[aá]lid|Revocaci[oó]n:?\s*(Bien|OK)\s+No"
    r"|FIRMA\s+(No\.?|#)\s*[Ss]erie|Archivo Firmado:|Firmante\(s\):|Evidencia Criptogr[aá]fica\s*[-–]\s*Transacci"
    r"|\bOCSP\b|\bTSP\b", re.I)
FIRMANTE = re.compile(r"Firmante\s+Nombre:\s*(.+?)\s+Validez", re.I)
CADENA = re.compile(r"Cadena\s+(?:de\s+)?[Ff]irma:\s*(.+)", re.S)
ENCABEZADO_EV = re.compile(r"EVIDENCIA CRIPTOGR[ÁA]FICA\s*[-–]\s*TRANSACCI", re.I)


def compactar_evidencia(parrafos):
    """Reduce cada bloque de evidencia de firma electrónica a un renglón con los firmantes.

    Esos bloques dicen 'Algoritmo: RSA…' y ensuciarían el índice con falsos 'algoritmo'.
    Se conserva íntegra la certificación de versión pública, que suele venir dentro de
    'Cadena firma:', y el texto de la sentencia que haya quedado pegado antes del bloque."""
    salida, i = [], 0
    while i < len(parrafos):
        if not MARCA_FIRMA.search(parrafos[i]):
            salida.append(parrafos[i])
            i += 1
            continue
        j = i
        while j < len(parrafos) and (MARCA_FIRMA.search(parrafos[j]) or FIRMANTE.search(parrafos[j])
                                     or re.match(r"^[\d/:TZ .()-]*(UTC|CDMX|M[eé]xico)", parrafos[j])):
            j += 1
        bloque = parrafos[i:j]
        while salida and re.match(r"^\S*\.p7m\b|^Autoridad Certificadora|^Archivo Firmado", salida[-1]):
            salida.pop()  # renglones del encabezado de la evidencia que quedaron antes de la 1a marca
        # texto de la sentencia pegado antes de la primera marca (p. ej. el último renglón de firmas)
        primero = bloque[0]
        corte = min(m.start() for m in (ENCABEZADO_EV.search(primero), MARCA_FIRMA.search(primero),
                                        FIRMANTE.search(primero)) if m)
        antes = primero[:corte].strip()
        if len(antes) > 3 and not re.fullmatch(r"[\d\s]+", antes):
            salida.append(antes)
        unido = " ".join(bloque)
        nombres = list(dict.fromkeys(n.strip() for n in FIRMANTE.findall(unido)))
        if nombres:
            salida.append("[FIRMA ELECTRÓNICA] Firmantes: " + "; ".join(nombres))
        for b in bloque:
            c = CADENA.search(b)
            if c and len(c.group(1)) > 60 and LEYENDA.search(c.group(1)) and not FIRMANTE.search(c.group(1)):
                salida.append(c.group(1).strip())
        i = j
    return salida


def _moda(valores):
    return Counter(valores).most_common(1)[0][0] if valores else 0


def pdf_a_texto(path):
    """Devuelve (texto, páginas, páginas_sin_texto)."""
    import pymupdf
    doc = pymupdf.open(path)
    paginas = []
    for pg in doc:
        lineas, vert = _lineas_visuales(pg)
        paginas.append({"lineas": lineas, "vert": vert, "alto": pg.rect.height})
    n = len(paginas)
    sin_texto = sum(1 for p in paginas if sum(len(l["texto"]) for l in p["lineas"]) < 40)
    if not n:
        return "", 0, 0

    # — encabezados y pies repetidos: primeros/últimos renglones dentro del 18% superior/inferior
    def zona(p):
        ls = p["lineas"]
        arriba = [l for l in ls[:4] if l["y1"] < p["alto"] * 0.18]
        abajo = [l for l in ls[-4:] if l["y0"] > p["alto"] * 0.82]
        return arriba + abajo

    cuenta = Counter()
    for p in paginas:
        cuenta.update({_norm(l["texto"]) for l in zona(p)})
        if p["vert"]:
            cuenta[_norm(p["vert"])] += 1
    umbral = max(2, 0.3 * n)
    repetidos = {k for k, c in cuenta.items() if n >= 3 and c >= umbral}
    leyenda_vista = set()

    def quitar(texto_norm):
        """Quita encabezados/pies repetidos y números de página, pero conserva
        una vez las leyendas de versión pública aunque se repitan en cada hoja."""
        if NUM_PAGINA.match(texto_norm):
            return True
        if texto_norm in repetidos:
            if LEYENDA.search(texto_norm) and texto_norm not in leyenda_vista:
                leyenda_vista.add(texto_norm)
                return False
            return True
        return False

    # — márgenes e interlineado por tamaño de letra: el cuerpo (p. ej. 14 pt) y las
    #   transcripciones/tesis citadas (p. ej. 12 pt, más sangradas) tienen geometrías distintas
    todas = [l for p in paginas for l in p["lineas"]]
    chars = Counter()
    for l in todas:
        chars[round(l["tam"])] += len(l["texto"])
    comunes = [t for t, c in chars.items() if c >= 0.1 * sum(chars.values())] or [max(chars, key=chars.get)]
    min_comun = min(comunes)
    geo = {}
    for tam in chars:
        grupo = [l for l in todas if round(l["tam"]) == tam]
        saltos = []
        for p in paginas:
            ls = [l for l in p["lineas"] if round(l["tam"]) == tam]
            saltos += [b["y0"] - a["y0"] for a, b in zip(ls, ls[1:]) if 0 < b["y0"] - a["y0"] < 3.5 * tam]
        izq = _moda([round(l["x0"]) for l in grupo])
        der = sorted(l["x1"] for l in grupo)[int(len(grupo) * 0.9)]
        geo[tam] = {"izq": izq, "der": der,
                    "inter": sorted(saltos)[len(saltos) // 2] if len(saltos) >= 3 else tam * 1.5}

    parrafos, notas, actual = [], [], None
    for p in paginas:
        ls = [l for l in p["lineas"] if not (l in zona(p) and quitar(_norm(l["texto"])))]
        # notas al pie: letra más chica que cualquier tamaño común, en la mitad inferior,
        # debajo del último renglón de texto normal
        ult_cuerpo = max((l["y1"] for l in ls if l["tam"] >= min_comun - 0.5), default=0)
        cuerpo_pg = []
        for l in ls:
            if l["tam"] < min_comun - 0.5 and l["y0"] > p["alto"] * 0.5 and l["y0"] >= ult_cuerpo - 1:
                if notas and not re.match(r"^\[?\d+\]?\s", l["texto"]):
                    notas[-1] += " " + l["texto"]
                else:
                    notas.append(l["texto"])
            else:
                cuerpo_pg.append(l)
        prev = None
        for l in cuerpo_pg:
            t = l["texto"]
            g = geo[round(l["tam"])]
            sangria = l["x0"] > g["izq"] + 15
            if actual is None:
                actual = t
            else:
                if prev is None:  # primer renglón de una hoja nueva
                    nuevo = bool(FIN_ORACION.search(actual)) and (t[:1].isupper() or sangria)
                else:
                    gp = geo[round(prev["tam"])]
                    nuevo = (abs(l["tam"] - prev["tam"]) > 1.5
                             or l["y0"] - prev["y0"] > 1.45 * gp["inter"]
                             or (sangria and prev["x0"] <= gp["izq"] + 15)  # sangría de 1er renglón
                             or (prev["x1"] < gp["der"] - 0.15 * (gp["der"] - gp["izq"])
                                 and bool(FIN_ORACION.search(actual))))
                if actual in ("•", "-", "–", "*"):  # viñeta suelta: se pega al renglón siguiente
                    nuevo = False
                if nuevo:
                    parrafos.append(actual)
                    actual = t
                elif re.search(r"[a-záéíóúñ]-$", actual) and t[:1].islower():
                    actual = actual[:-1] + t  # palabra partida con guion
                elif re.search(r"\S-$", actual):
                    actual += t  # guion real al final del renglón (FII-C-5, ****-SPA)
                else:
                    actual += " " + t
            prev = l
        if p["vert"] and not quitar(_norm(p["vert"])):
            notas.append(p["vert"])
    if actual:
        parrafos.append(actual)
    parrafos = compactar_evidencia([limpiar_firma(x) for x in parrafos])
    texto = "\n\n".join(x for x in parrafos if x)
    if notas:
        notas = list(dict.fromkeys(x for x in map(limpiar_firma, notas) if x and not RUIDO_FIRMA.search(x) and not MARCA_FIRMA.search(x)))
        texto += "\n\n[NOTAS AL PIE Y TEXTO MARGINAL]\n\n" + "\n".join(notas)
    return texto, n, sin_texto


def docx_a_texto(path):
    import docx
    from docx.table import Table
    from docx.text.paragraph import Paragraph
    d = docx.Document(str(path))
    partes = []
    for el in d.element.body.iterchildren():
        tag = el.tag.rsplit("}", 1)[-1]
        if tag == "p":
            t = Paragraph(el, d).text.strip()
            if t:
                partes.append(t)
        elif tag == "tbl":
            for fila in Table(el, d).rows:
                celdas = []
                for c in fila.cells:
                    ct = c.text.strip()
                    if ct and (not celdas or celdas[-1] != ct):  # celdas combinadas se repiten
                        celdas.append(ct)
                if celdas:
                    partes.append(" | ".join(celdas))
    # las leyendas de versión pública a veces van en el encabezado de Word
    leyendas = []
    for sec in d.sections:
        for p in sec.header.paragraphs + sec.footer.paragraphs:
            t = p.text.strip()
            if t and LEYENDA.search(t) and t not in leyendas:
                leyendas.append(t)
    texto = "\n\n".join(partes)
    if leyendas:
        texto += "\n\n[LEYENDAS DE ENCABEZADO/PIE]\n\n" + "\n".join(leyendas)
    return texto


def fase_texto(limite=None, muestra=None, semilla=None):
    TXT.mkdir(parents=True, exist_ok=True)
    recs = seleccionar(limite, muestra, semilla)
    marcados = set()
    if SIN_TEXTO.exists():
        with SIN_TEXTO.open(encoding="utf-8") as f:
            marcados = {r["id"] for r in csv.DictReader(f)}
    hechos = saltados = 0
    for rec in recs:
        id_ = rec["id"]
        if (TXT / f"{id_}.txt").exists() or id_ in marcados:
            saltados += 1
            continue
        archivos = [p for p in RAW.glob(f"{id_}.*") if p.suffix != ".part"]
        if not archivos:
            continue  # no descargado (ya quedó en errores.csv)
        a = archivos[0]
        try:
            ext = a.suffix.lower()
            if ext == ".pdf":
                texto, pags, pags_vacias = pdf_a_texto(a)
                if len(texto.strip()) < 40 * max(pags, 1) or pags_vacias > pags / 2:
                    nuevo = not SIN_TEXTO.exists()
                    with SIN_TEXTO.open("a", newline="", encoding="utf-8") as f:
                        w = csv.writer(f)
                        if nuevo:
                            w.writerow(["id", "archivo", "paginas", "paginas_sin_texto", "caracteres"])
                        w.writerow([id_, a.name, pags, pags_vacias, len(texto.strip())])
                    marcados.add(id_)
                    log(f"  {id_}: sin capa de texto ({pags_vacias}/{pags} páginas vacías)")
                    continue
            elif ext == ".docx":
                texto = docx_a_texto(a)
            else:
                raise ValueError(f"formato no soportado: {ext}")
            escribir_atomico(TXT / f"{id_}.txt", texto.encode("utf-8"))
            hechos += 1
        except Exception as e:
            registrar_error(id_, "texto", f"{e.__class__.__name__}: {e}")
    log(f"texto: {hechos} convertidos, {saltados} ya existían o marcados, sin texto total: {len(marcados)}")


# ───────────────────────────── CLI ─────────────────────────────

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("fase", choices=["listar", "descargar", "texto", "todo"])
    ap.add_argument("--limite", type=int, help="procesar sólo los primeros N asuntos (prueba)")
    ap.add_argument("--muestra", type=int, help="descargar/texto: N asuntos al azar de metadata.jsonl")
    ap.add_argument("--semilla", type=int, default=2026, help="semilla de la muestra (por omisión 2026)")
    a = ap.parse_args()
    cli = Cliente()
    if a.fase in ("listar", "todo"):
        fase_listar(cli, a.limite)
    if a.fase in ("descargar", "todo"):
        fase_descargar(cli, a.limite, a.muestra, a.semilla)
    if a.fase in ("texto", "todo"):
        fase_texto(a.limite, a.muestra, a.semilla)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit("\ninterrumpido; vuelve a correrlo para reanudar")
````

### Anexo · analisis.py

Índice de relevancia, clasificación de menciones y resumen. SHA-256: 58d4c4392edd85061c11ccc4c258b7e70eeb2b96235cd7e92eee11a79f4aa360

<!-- archivo: analisis.py -->
````python
#!/usr/bin/env python3
"""Índice de relevancia y resumen del corpus descargado con sise.py.

    python analisis.py relevancia   # data/relevancia.csv + data/menciones/{id}.txt
    python analisis.py resumen      # imprime el resumen y lo guarda en data/resumen.md
"""
import csv
import json
import re
import sys
import unicodedata
from collections import Counter
from pathlib import Path

from sise import DATA, ERRORES, RAW, SIN_TEXTO, TXT, cargar_metadata

MENCIONES = DATA / "menciones"
RELEVANCIA = DATA / "relevancia.csv"
RESUMEN = DATA / "resumen.md"

# Se buscan sobre el texto en minúsculas y sin acentos, salvo "IA", que va sobre el original:
# en minúsculas "ia" aparece dentro de miles de palabras (materia, justicia…).
FRASE = re.compile(r"\binteli-?\s*gencia\s*-?\s*artificial\b")  # tolera palabras pegadas o partidas por el PDF
OTROS = {
    "IA": (re.compile(r"\bI\.?A\.?(?![\wÁÉÍÓÚÑ])"), False),
    "algoritmo": (re.compile(r"\balgoritm\w*"), True),               # algoritmo(s), algorítmico(a)(s)
    "sistemas automatizados": (re.compile(r"\bsistemas?\s+automatizad[oa]s?\b"), True),
    "ChatGPT": (re.compile(r"\bchat\s?-?gpt\b"), True),
}
CONTEXTO = 500

# Párrafos de machote que mencionan la IA sin discutirla (se buscan sobre texto normalizado).
# Una mención es "sustantiva" si su párrafo no es ninguno de estos.
MACHOTES = {
    "aviso_sintesis_IA": re.compile(r"sintesis (en lenguaje ciudadano |ciudadana )?(fue )?creada\s*con inteligencia"
                                    r"|primera sintesis fue creada|creada\s*con inteligencia artificial"),
    "machote_videoconferencia": re.compile(r"identidad de los intervinientes|uso adecuado de la videoconferencia"
                                           r"|susceptibles de alteracion"),
    "lista_carreras": re.compile(r"ingenier[oa] en inteligencia artificial.*(licenciatura|ingenier[oa]) en"
                                 r"|(licenciatura|ingenier[oa]) en .*ingenier[oa] en inteligencia artificial"),
    "cita_ley_movilidad": re.compile(r"agencia de movilidad|optimizacion mediante algoritmos|vias publicas del estado"),
}


def clasificar(norm, matches):
    """Devuelve (tipo_mencion, menciones_sustantivas) según el párrafo de cada mención."""
    tipos, sustantivas = set(), 0
    for m in matches:
        a = norm.rfind("\n\n", 0, m.start()) + 2
        b = norm.find("\n\n", m.end())
        parrafo = norm[max(a, 0):b if b >= 0 else len(norm)]
        t = next((k for k, rx in MACHOTES.items() if rx.search(parrafo)), None)
        if t:
            tipos.add(t)
        else:
            sustantivas += 1
    if not matches:
        return "sin_menciones", 0
    if sustantivas:
        return "sustantiva", sustantivas
    return "+".join(sorted(tipos)), 0


def normalizar(texto):
    """Minúsculas y sin acentos conservando la longitud, para que los índices de las
    coincidencias sirvan directo sobre el texto original."""
    out = []
    for c in texto:
        b = unicodedata.normalize("NFD", c.lower())[0]
        out.append(b if len(b) == 1 else c)
    return "".join(out)


def ventana(texto, ini, fin, ancho=CONTEXTO):
    """~ancho caracteres alrededor de la coincidencia, dentro de su párrafo y sin cortar palabras."""
    p_ini = texto.rfind("\n\n", 0, ini) + 2 if texto.rfind("\n\n", 0, ini) >= 0 else 0
    p_fin = texto.find("\n\n", fin)
    p_fin = len(texto) if p_fin < 0 else p_fin
    sobra = max(0, ancho - (fin - ini)) // 2
    a, b = max(p_ini, ini - sobra), min(p_fin, fin + sobra)
    # si el párrafo es corto de un lado, aprovecha el espacio del otro
    if a == p_ini:
        b = min(p_fin, a + ancho)
    elif b == p_fin:
        a = max(p_ini, b - ancho)
    while a > p_ini and not texto[a - 1].isspace():
        a -= 1
    while b < p_fin and not texto[b].isspace():
        b += 1
    frag = re.sub(r"\s+", " ", texto[a:b]).strip()
    return ("…" if a > p_ini else "") + frag + ("…" if b < p_fin else "")


def fragmentos(texto, norm, matches):
    """Párrafo de cada mención con uno de contexto antes y otro después; une los que se enciman."""
    limites, pos = [], 0
    for p in texto.split("\n\n"):
        limites.append((pos, pos + len(p)))
        pos += len(p) + 2
    idx = []
    for m in matches:
        k = next(i for i, (a, b) in enumerate(limites) if a <= m.start() <= b)
        idx.append(k)
    rangos = []
    for k in sorted(set(idx)):
        a, b = max(0, k - 1), min(len(limites) - 1, k + 1)
        if rangos and a <= rangos[-1][1] + 1:
            rangos[-1][1] = b
        else:
            rangos.append([a, b])
    out = []
    for a, b in rangos:
        n = sum(1 for k in idx if a <= k <= b)
        out.append((a, b, n, texto[limites[a][0]:limites[b][1]]))
    return out


def fase_relevancia():
    MENCIONES.mkdir(parents=True, exist_ok=True)
    sin_texto = set()
    if SIN_TEXTO.exists():
        with SIN_TEXTO.open(encoding="utf-8") as f:
            sin_texto = {r["id"] for r in csv.DictReader(f)}
    campos = ["NEUN", "tipo_asunto", "materia", "fecha", "total_palabras", "menciones_inteligencia_artificial",
              "menciones_IA", "menciones_algoritmo", "menciones_sistemas_automatizados", "menciones_ChatGPT",
              "primer_parrafo", "tipo_mencion", "menciones_sustantivas", "id", "expediente", "organo", "circuito", "estado"]
    filas = []
    for rec in cargar_metadata():
        id_ = rec["id"]
        fila = {"NEUN": rec["neun"], "tipo_asunto": rec["tipo_asunto"], "materia": rec["materia"],
                "fecha": rec["fecha"], "id": id_, "expediente": rec["expediente"], "organo": rec["organo"],
                "circuito": rec["circuito"]}
        ruta = TXT / f"{id_}.txt"
        if not ruta.exists():
            fila["estado"] = "sin_texto" if id_ in sin_texto else (
                "sin_descarga" if not any(RAW.glob(f"{id_}.*")) else "sin_convertir")
            filas.append(fila)
            continue
        texto = ruta.read_text(encoding="utf-8")
        norm = normalizar(texto)
        ms = list(FRASE.finditer(norm))
        fila.update({
            "estado": "ok", "total_palabras": len(texto.split()),
            "menciones_inteligencia_artificial": len(ms),
            "primer_parrafo": ventana(texto, ms[0].start(), ms[0].end()) if ms else "",
        })
        fila["tipo_mencion"], fila["menciones_sustantivas"] = clasificar(norm, ms)
        for nombre, (rx, sobre_norm) in OTROS.items():
            fila["menciones_" + nombre.replace(" ", "_")] = len(rx.findall(norm if sobre_norm else texto))
        filas.append(fila)

        destino = MENCIONES / f"{id_}.txt"
        if ms:
            frs = fragmentos(texto, norm, ms)
            cab = (f"NEUN {rec['neun']} · Exp. {rec['expediente']} · {rec['tipo_asunto']} · {rec['fecha']}\n"
                   f"{rec['organo']}\n"
                   f"{len(ms)} menciones de «inteligencia artificial» en {len(frs)} fragmentos\n")
            cuerpo = "\n\n".join(
                f"=== Fragmento {i} de {len(frs)} · párrafos {a + 1}–{b + 1} · {n} mención(es) ===\n\n{t}"
                for i, (a, b, n, t) in enumerate(frs, 1))
            destino.write_text(cab + "\n" + cuerpo + "\n", encoding="utf-8")
        elif destino.exists():
            destino.unlink()

    with RELEVANCIA.open("w", newline="", encoding="utf-8-sig") as f:  # -sig: Excel respeta acentos
        w = csv.DictWriter(f, fieldnames=campos)
        w.writeheader()
        w.writerows(filas)
    c = Counter(f["estado"] for f in filas)
    print(f"relevancia.csv: {len(filas)} filas ({dict(c)}); "
          f"{sum(1 for f in filas if f.get('menciones_inteligencia_artificial'))} archivos en menciones/")


def fase_resumen():
    meta = cargar_metadata()
    with RELEVANCIA.open(encoding="utf-8-sig") as f:
        rel = list(csv.DictReader(f))
    ok = [r for r in rel if r["estado"] == "ok"]
    errores = []
    if ERRORES.exists():
        with ERRORES.open(encoding="utf-8") as f:
            errores = list(csv.DictReader(f))
    ids_desc = {p.stem for p in RAW.glob("*.*") if p.suffix != ".part"}
    fallidas = {e["id"] for e in errores if e["etapa"] == "descarga"} - ids_desc
    exts = Counter(p.suffix.lower() for p in RAW.glob("*.*") if p.suffix != ".part")
    palabras = sum(int(r["total_palabras"]) for r in ok)
    chars = sum((TXT / f"{r['id']}.txt").stat().st_size for r in ok)  # bytes ≈ caracteres (+acentos)
    tokens = round(chars / 4)
    n_ia = [int(r["menciones_inteligencia_artificial"]) for r in ok]
    buckets = {"0 (sólo en metadatos o texto no recuperado)": sum(1 for n in n_ia if n == 0),
               "1": sum(1 for n in n_ia if n == 1),
               "2–5": sum(1 for n in n_ia if 2 <= n <= 5),
               "6 o más": sum(1 for n in n_ia if n >= 6)}
    top = sorted(ok, key=lambda r: -int(r["menciones_inteligencia_artificial"]))[:20]
    otros = {k: sum(1 for r in ok if int(r["menciones_" + k.replace(" ", "_")]) > 0) for k in OTROS}

    L = ["# Resumen del corpus «inteligencia artificial» (Buscador SISE)", "",
         f"- Asuntos en metadata: **{len(meta)}**",
         f"- Documentos descargados: **{len(ids_desc)}** ({', '.join(f'{v} {k}' for k, v in exts.items())})",
         f"- Descargas fallidas: **{len(fallidas)}**" + (f" ({', '.join(sorted(fallidas))})" if fallidas else ""),
         f"- Sin capa de texto (pendientes de OCR): **{sum(1 for r in rel if r['estado'] == 'sin_texto')}**",
         f"- Convertidos a texto: **{len(ok)}**",
         f"- Tamaño del corpus: **{palabras:,} palabras**, ~**{tokens:,} tokens** "
         f"(estimado a 4 caracteres por token; en español legal la cifra real puede variar ±20 %)",
         "", "## Sentencias por número de menciones de «inteligencia artificial»", "",
         "| Menciones | Sentencias |", "|---|---:|"]
    L += [f"| {k} | {v} |" for k, v in buckets.items()]
    tipos = Counter(r["tipo_mencion"] for r in ok)
    L += ["", "## ¿Qué clase de mención es?", "",
          "Una mención es *sustantiva* si su párrafo no es un machote conocido. Una sentencia cuenta como "
          "sustantiva si tiene al menos una mención así.", "",
          "| Tipo | Sentencias |", "|---|---:|"]
    L += [f"| {k} | {v} |" for k, v in tipos.most_common()]
    L += ["", "Sentencias que mencionan al menos una vez los otros términos: "
          + "; ".join(f"{k}: {v}" for k, v in otros.items()), "",
          "## Las 20 con más menciones", "",
          "| # | NEUN | Expediente | Tipo de asunto | Órgano | Fecha | Menciones | Sustantivas | Palabras |",
          "|---:|---|---|---|---|---|---:|---:|---:|"]
    L += [f"| {i} | {r['id']} | {r['expediente']} | {r['tipo_asunto']} | {r['organo']} | {r['fecha']} | "
          f"{r['menciones_inteligencia_artificial']} | {r['menciones_sustantivas']} | {int(r['total_palabras']):,} |"
          for i, r in enumerate(top, 1)]
    md = "\n".join(L) + "\n"
    RESUMEN.write_text(md, encoding="utf-8")
    print(md)


if __name__ == "__main__":
    fase = sys.argv[1] if len(sys.argv) > 1 else ""
    if fase == "relevancia":
        fase_relevancia()
    elif fase == "resumen":
        fase_resumen()
    else:
        sys.exit(__doc__)
````

### Anexo · extraer_credenciales.py

Paso 4: consulta el sitio del OAJ y verifica las credenciales. SHA-256: 42dde7e97c17cdd7dcd3abf8988dd934bae3c693bc58960d3185009eea96831e

<!-- archivo: extraer_credenciales.py -->
````python
#!/usr/bin/env python3
"""Va al Buscador de Sentencias con un navegador automatizado, hace una búsqueda, pide un
documento y extrae las credenciales públicas que la página usa. Compara con las de sise.py.

    python extraer_credenciales.py

Si algo sale DISTINTO, copia el valor nuevo a la constante indicada en sise.py.
"""
import asyncio
import json
import re
from pathlib import Path

from playwright.async_api import async_playwright

URL = "https://ejusticia.cjf.gob.mx/BuscadorSISE/"


async def capturar():
    vistos = {}
    async with async_playwright() as p:
        b = await p.chromium.launch()
        ctx = await b.new_context(accept_downloads=True)
        pg = await ctx.new_page()

        def on_req(req):
            u = req.url
            if "IdentityManager/token/" in u and req.method == "PUT":
                vistos["token_body"] = json.loads(req.post_data)
            elif "por-sentencia/buscar/" in u:
                vistos["buscar_body"] = json.loads(req.post_data)
            elif "Login/Safe/System" in u:
                vistos["login_url"] = u.split("?")[0]
                vistos["login_auth"] = req.headers.get("authorization")
                vistos["login_body"] = json.loads(req.post_data)
            elif "wsSentenceFinder" in u:
                vistos["sentencia_url"] = u.split("?")[0]
        pg.on("request", on_req)

        await pg.goto(URL, wait_until="networkidle")
        await pg.get_by_text("Búsqueda por Término").click()
        await pg.fill("input[formcontrolname=contenido]", "inteligencia artificial")
        await pg.select_option("select[formcontrolname=tipoBusqueda]", label="Frase exacta")
        await pg.get_by_role("button", name="Buscar").click()
        await pg.wait_for_load_state("networkidle")
        await pg.wait_for_timeout(3000)
        celda = pg.locator("td").filter(has_text="Coincidencia").first
        try:
            async with pg.expect_download(timeout=30000):
                await celda.locator("img, i, svg, a, button, span").last.click()
        except Exception:
            await pg.wait_for_timeout(5000)
        await b.close()
    return vistos


def main():
    v = asyncio.run(capturar())
    codigo = (Path(__file__).resolve().parent / "sise.py").read_text(encoding="utf-8")
    actual = {
        "CLIENTE_APISISE.ClientID": re.search(r'"ClientID": "([^"]+)"', codigo).group(1),
        "CLIENTE_APISISE.ClientSecret": re.search(r'"ClientSecret": "([^"]+)"', codigo).group(1),
        "BASIC_LOGIN_DOC": re.search(r'BASIC_LOGIN_DOC = "([^"]+)"', codigo).group(1),
        "URL_LOGIN_DOC": re.search(r'URL_LOGIN_DOC = "([^"]+)"', codigo).group(1),
        "URL_SENTENCIA": re.search(r'URL_SENTENCIA = "([^"]+)"', codigo).group(1),
    }
    encontrado = {
        "CLIENTE_APISISE.ClientID": v.get("token_body", {}).get("ClientID"),
        "CLIENTE_APISISE.ClientSecret": v.get("token_body", {}).get("ClientSecret"),
        "BASIC_LOGIN_DOC": v.get("login_auth"),
        "URL_LOGIN_DOC": v.get("login_url"),
        "URL_SENTENCIA": v.get("sentencia_url"),
    }
    print("Constante en sise.py            Estado")
    for k in actual:
        e = encontrado[k]
        estado = "no capturado" if e is None else ("igual" if e == actual[k] else f"DISTINTO → nuevo valor: {e}")
        print(f"  {k:30} {estado}")
    if "buscar_body" in v:
        print("\nCuerpo de la búsqueda que usa la página:", json.dumps(v["buscar_body"], ensure_ascii=False))
    if "token_body" in v:
        print("Datos del token:", json.dumps(v["token_body"].get("data"), ensure_ascii=False))


if __name__ == "__main__":
    main()
````

### Anexo · comparar.py

Compara una réplica contra las huellas del corpus original (data/manifiesto.csv). SHA-256: 5fece3c964e963e96d5cd98ab41095717d73147e94caa6c9bc91aec5563b67a9

<!-- archivo: comparar.py -->
````python
#!/usr/bin/env python3
"""Compara una réplica independiente contra el corpus original.

    python comparar.py RUTA_DE_LA_REPLICA          # la carpeta que contiene data/

Niveles de comparación:
  1. Cobertura    ¿aparecen las mismas sentencias (id)?
  2. Fuente       ¿los PDF son idénticos byte a byte? (SHA-256 contra data/manifiesto.csv)
  3. Extracción   ¿el texto limpio es idéntico? Si no, ¿qué tan parecido? (Jaccard de 5-gramas de palabras)
  4. Medición     ¿coinciden metadatos y conteos de menciones?

Escribe el detalle en RUTA_DE_LA_REPLICA/comparacion.csv.
"""
import csv
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

ORIGINAL = Path(__file__).resolve().parent / "data"
CAMPOS_META = ["neun", "expediente", "organo", "circuito", "tipo_asunto", "materia", "fecha", "tema", "sintesis"]


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def meta(d):
    return {json.loads(l)["id"]: json.loads(l) for l in (d / "metadata.jsonl").read_text(encoding="utf-8").splitlines() if l}


def rel(d):
    p = d / "relevancia.csv"
    return {r["id"]: r for r in csv.DictReader(p.open(encoding="utf-8-sig"))} if p.exists() else {}


def jaccard(a, b, n=5):
    def sh(t):
        w = t.split()
        return {" ".join(w[i:i + n]) for i in range(max(1, len(w) - n + 1))}
    A, B = sh(a), sh(b)
    return len(A & B) / len(A | B) if A | B else 1.0


def main(replica):
    R = Path(replica).expanduser().resolve() / "data"
    if not (R / "metadata.jsonl").exists():
        sys.exit(f"No encuentro {R / 'metadata.jsonl'}")
    mo, mr = meta(ORIGINAL), meta(R)
    ro, rr = rel(ORIGINAL), rel(R)
    pm = next((p for p in (ORIGINAL / "manifiesto.csv", R / "manifiesto.csv") if p.exists()), None)
    if not pm:
        sys.exit("Falta manifiesto.csv (huellas del corpus original) en data/")
    man = {r["id"]: r for r in csv.DictReader(pm.open(encoding="utf-8"))}
    comunes = sorted(set(mo) & set(mr))
    print("1. COBERTURA")
    print(f"   original {len(mo)} · réplica {len(mr)} · en ambos {len(comunes)} · "
          f"sólo original {len(set(mo) - set(mr))} · sólo réplica {len(set(mr) - set(mo))}")
    # por NEUN también, por si el sufijo _NumeroOrden se asignó distinto
    no, nr = {m["neun"] for m in mo.values()}, {m["neun"] for m in mr.values()}
    print(f"   NEUN distintos: original {len(no)} · réplica {len(nr)} · en ambos {len(no & nr)}")

    filas, c = [], Counter()
    for i in comunes:
        f = {"id": i}
        # PDF y texto se comparan contra las huellas del manifiesto original: no hacen falta
        # los archivos originales (p. ej. después de formatear la Mac)
        ref = man.get(i, {})
        pr, tr = R / "raw" / f"{i}.pdf", R / "txt" / f"{i}.txt"
        if not pr.exists() or not ref.get("pdf_sha256"):
            f["pdf"] = "no comparable"
        else:
            f["pdf"] = "idéntico" if sha(pr) == ref["pdf_sha256"] else "distinto"
        c["pdf:" + f["pdf"]] += 1
        if not tr.exists() or not ref.get("txt_sha256"):
            f["txt"], f["similitud"] = "no comparable", ""
        elif sha(tr) == ref["txt_sha256"]:
            f["txt"], f["similitud"] = "idéntico", 1.0
        else:
            to = ORIGINAL / "txt" / f"{i}.txt"  # si el texto original existe en otra carpeta, mide el parecido
            sim = round(jaccard(to.read_text(encoding="utf-8"), tr.read_text(encoding="utf-8")), 4) \
                if to.exists() and to.resolve() != tr.resolve() else ""
            f["txt"], f["similitud"] = "distinto", sim
        c["txt:" + f["txt"]] += 1
        if rr.get(i, {}).get("estado") == "ok" and ref.get("menciones_ia"):
            for k_rel, k_man in (("total_palabras", "palabras"), ("menciones_inteligencia_artificial", "menciones_ia")):
                if rr[i].get(k_rel) != ref[k_man]:
                    f["manifiesto_" + k_man] = f"{ref[k_man]} → {rr[i].get(k_rel)}"
                    c["man:" + k_man] += 1
        dif = [k for k in CAMPOS_META if str(mo[i].get(k)) != str(mr[i].get(k))]
        f["metadatos_distintos"] = ";".join(dif)
        for k in dif:
            c["meta:" + k] += 1
        if i in ro and i in rr:
            for k in ("total_palabras", "menciones_inteligencia_artificial", "menciones_IA", "menciones_algoritmo",
                      "menciones_ChatGPT", "tipo_mencion"):
                if ro[i].get(k) != rr[i].get(k):
                    f[k] = f"{ro[i].get(k)} → {rr[i].get(k)}"
                    c["rel:" + k] += 1
        filas.append(f)

    n = len(comunes) or 1
    print("\n2. FUENTE (PDF)")
    for k in sorted(k for k in c if k.startswith("pdf:")):
        base = sum(v for kk, v in c.items() if kk[:4] == k[:4] and "no comparable" not in kk) or 1
        print(f"   {k[4:]:22} {c[k]:5}" + ("" if "no comparable" in k else f"  ({c[k] / base:.1%} de los comparables)"))
    print("\n3. EXTRACCIÓN (texto limpio)")
    for k in sorted(k for k in c if k.startswith("txt:")):
        base = sum(v for kk, v in c.items() if kk[:4] == k[:4] and "no comparable" not in kk) or 1
        print(f"   {k[4:]:22} {c[k]:5}" + ("" if "no comparable" in k else f"  ({c[k] / base:.1%} de los comparables)"))
    sims = [f["similitud"] for f in filas if f["txt"] == "distinto"]
    if sims:
        sims.sort()
        print(f"   similitud de los distintos: mín {sims[0]} · mediana {sims[len(sims) // 2]} · máx {sims[-1]}")
    print("\n4. MEDICIÓN")
    meta_dif = {k[5:]: v for k, v in c.items() if k.startswith("meta:")}
    print("   metadatos que difieren:", meta_dif or "ninguno")
    rel_dif = {k[4:]: v for k, v in c.items() if k.startswith("rel:")}
    print("   índice que difiere:    ", rel_dif or "ninguno" if rr else "(la réplica no tiene relevancia.csv)")
    man_dif = {k[4:]: v for k, v in c.items() if k.startswith("man:")}
    print("   vs. manifiesto original:", man_dif or "palabras y menciones idénticas" if rr else "(sin relevancia.csv)")

    salida = Path(replica).expanduser().resolve() / "comparacion.csv"
    cols = sorted({k for f in filas for k in f}, key=lambda k: (k != "id", k))
    with salida.open("w", newline="", encoding="utf-8-sig") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        w.writerows(filas)
    print(f"\nDetalle por sentencia: {salida}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])
````

### Anexo · obsidian.py

Genera la bóveda de Obsidian. SHA-256: 5cd6a642862ac661148dc050f3a9e450b3037ef6151f782b1ceb638c5ada8baf

<!-- archivo: obsidian.py -->
````python
#!/usr/bin/env python3
"""Genera una bóveda de Obsidian a partir del corpus: una nota por sentencia, enlazada a
notas-eje de órgano, circuito, tipo de asunto, clase de mención y términos.

    python obsidian.py            # crea/actualiza ./boveda  (ábrela en Obsidian: "Open folder as vault")
"""
import csv
import json
import re
import shutil
from collections import Counter, defaultdict
from pathlib import Path

from sise import DATA, cargar_metadata

BOVEDA = Path(__file__).resolve().parent / "boveda"
MENCIONES = DATA / "menciones"

MACHOTES = {
    "aviso_sintesis_IA": ("Aviso - síntesis ciudadana hecha con IA",
                          "El juzgado avisa que la «síntesis en lenguaje ciudadano» se redactó con inteligencia "
                          "artificial. Es una mención sobre el *uso* de IA por el propio órgano, no sobre el litigio."),
    "machote_videoconferencia": ("Machote - videoconferencia y voces alteradas con IA",
                                 "Párrafo reutilizado en materia penal: el juzgador debe asegurarse de la identidad de "
                                 "quienes intervienen por videoconferencia porque la IA puede alterar voz y rostro."),
    "lista_carreras": ("Machote - lista de carreras (Ing. en IA)",
                       "Listados de carreras universitarias que incluyen «Ingeniero en Inteligencia Artificial»."),
    "cita_ley_movilidad": ("Machote - ley de movilidad y plataformas",
                           "Transcripción de una ley de movilidad (Querétaro) que regula plataformas de transporte "
                           "con «algoritmos tecnológicos, inteligencia artificial»."),
}
SUSTANTIVA = ("Mención sustantiva", "Al menos una mención de «inteligencia artificial» fuera de los machotes conocidos: "
                                    "la sentencia probablemente discute o usa la IA de fondo.")
TERMINOS = {"menciones_ChatGPT": "ChatGPT", "menciones_algoritmo": "Algoritmo",
            "menciones_sistemas_automatizados": "Sistemas automatizados", "menciones_IA": "Sigla IA"}


def nombre(s):
    """Nombre de archivo válido en Obsidian (sin / \\ : # ^ [ ] |)."""
    s = re.sub(r"[\\/]", "-", str(s or "Sin dato"))
    s = re.sub(r'[:#^\[\]|*"<>?]', "", s)
    return re.sub(r"\s+", " ", s).strip()[:150]


def yaml_str(s):
    return json.dumps(s if s is not None else "", ensure_ascii=False)


def main():
    meta = {r["id"]: r for r in cargar_metadata()}
    with (DATA / "relevancia.csv").open(encoding="utf-8-sig") as f:
        rel = {r["id"]: r for r in csv.DictReader(f)}
    if BOVEDA.exists():
        for sub in ("Sentencias", "Órganos", "Circuitos", "Tipos de asunto", "Clase de mención", "Términos"):
            shutil.rmtree(BOVEDA / sub, ignore_errors=True)
    for sub in ("Sentencias", "Órganos", "Circuitos", "Tipos de asunto", "Clase de mención", "Términos"):
        (BOVEDA / sub).mkdir(parents=True, exist_ok=True)

    ejes = defaultdict(Counter)  # tipo de eje -> nombre -> n.º de sentencias
    for id_, m in meta.items():
        r = rel.get(id_, {})
        if r.get("estado") != "ok":
            continue
        organo, circuito, tipo = nombre(m["organo"]), nombre(m["circuito"]), nombre(m["tipo_asunto"])
        clase = r["tipo_mencion"]
        clases = [MACHOTES[c][0] for c in clase.split("+") if c in MACHOTES]
        if clase == "sustantiva":
            clases = [SUSTANTIVA[0]]
        terminos = [t for col, t in TERMINOS.items() if int(r.get(col) or 0) > 0]
        ejes["Órganos"][organo] += 1
        ejes["Circuitos"][circuito] += 1
        ejes["Tipos de asunto"][tipo] += 1
        for c in clases:
            ejes["Clase de mención"][c] += 1
        for t in terminos:
            ejes["Términos"][t] += 1

        tags = [f"mencion/{'sustantiva' if clase == 'sustantiva' else 'machote' if clases else 'ninguna'}"]
        tags.append("anio/" + (m["fecha"] or "sd")[:4])
        fm = "\n".join([
            "---",
            f"neun: {m['neun']}", f"expediente: {yaml_str(m['expediente'])}",
            f"organo: {yaml_str(m['organo'])}", f"circuito: {yaml_str(m['circuito'])}",
            f"tipo_asunto: {yaml_str(m['tipo_asunto'])}", f"materia: {yaml_str(m['materia'])}",
            f"fecha: {m['fecha']}", f"palabras: {r['total_palabras']}",
            f"menciones_ia: {r['menciones_inteligencia_artificial']}",
            f"menciones_sustantivas: {r['menciones_sustantivas']}", f"tipo_mencion: {clase}",
            "tags: [" + ", ".join(tags) + "]",
            "---",
        ])
        cuerpo = [
            f"# {m['tipo_asunto']} {m['expediente']}",
            "",
            f"**Órgano:** [[{organo}]] · **Circuito:** [[{circuito}]] · **Tipo:** [[{tipo}]] · **Fecha:** {m['fecha']}",
            f"**Mención:** " + " · ".join(f"[[{c}]]" for c in clases)
            + (" · **Términos:** " + " · ".join(f"[[{t}]]" for t in terminos) if terminos else ""),
            "",
            f"**Tema:** {m['tema'] or '—'}",
            "",
            "## Síntesis", "", (m["sintesis"] or "—").strip(),
            "",
            "## Menciones de «inteligencia artificial»", "",
        ]
        frag = MENCIONES / f"{id_}.txt"
        if frag.exists():
            texto = frag.read_text(encoding="utf-8").split("\n", 3)[-1]  # sin la cabecera
            texto = re.sub(r"^=== (.+?) ===$", r"### \1", texto, flags=re.M)
            # resalta la frase para que se vea en la lectura
            texto = re.sub(r"(?i)(inteligencia\s+artificial)", r"==\1==", texto)
            cuerpo.append(texto.strip())
        else:
            cuerpo.append("_La frase no aparece en el texto extraído._")
        cuerpo += ["", f"[Texto completo](file://{DATA / 'txt' / (id_ + '.txt')}) · "
                       f"[PDF](file://{DATA / 'raw' / (id_ + '.pdf')})"]
        (BOVEDA / "Sentencias" / f"{id_}.md").write_text(fm + "\n\n" + "\n".join(cuerpo) + "\n", encoding="utf-8")

    # notas-eje: descripción + conteo (la lista de sentencias la dan los backlinks de Obsidian)
    descr = {v[0]: v[1] for v in MACHOTES.values()}
    descr[SUSTANTIVA[0]] = SUSTANTIVA[1]
    for carpeta, cuenta in ejes.items():
        for n, c in cuenta.items():
            txt = [f"# {n}", "", f"**{c} sentencias** del corpus.", ""]
            if n in descr:
                txt += [descr[n], ""]
            txt += ["Las sentencias aparecen en el panel de *backlinks* y en la vista de grafo."]
            (BOVEDA / carpeta / f"{n}.md").write_text("\n".join(txt) + "\n", encoding="utf-8")

    # nota de inicio
    resumen = (DATA / "resumen.md").read_text(encoding="utf-8") if (DATA / "resumen.md").exists() else ""
    top_org = ejes["Órganos"].most_common(10)
    inicio = ["# Inicio — corpus «inteligencia artificial»", "",
              "Mapa de la bóveda: cada nota en *Sentencias* se enlaza a su órgano, circuito, tipo de asunto, "
              "clase de mención y términos. Abre la **vista de grafo** (Ctrl/Cmd+G): los colores ya están "
              "configurados (verde = mención sustantiva, gris = sólo machote).", "",
              "## Clases de mención", ""]
    inicio += [f"- [[{n}]] — {c}" for n, c in ejes["Clase de mención"].most_common()]
    inicio += ["", "## Órganos con más sentencias", ""] + [f"- [[{n}]] — {c}" for n, c in top_org]
    inicio += ["", "## Términos", ""] + [f"- [[{n}]] — {c}" for n, c in ejes["Términos"].most_common()]
    inicio += ["", "---", "", resumen]
    (BOVEDA / "Inicio.md").write_text("\n".join(inicio), encoding="utf-8")

    # configuración del grafo: grupos de color
    cfg = BOVEDA / ".obsidian"
    cfg.mkdir(exist_ok=True)
    rgb = lambda h: int(h.lstrip("#"), 16)
    grafo = {
        "colorGroups": [
            {"query": "tag:#mencion/sustantiva", "color": {"a": 1, "rgb": rgb("#2e9e6b")}},
            {"query": "tag:#mencion/machote", "color": {"a": 1, "rgb": rgb("#9a9a9a")}},
            {"query": 'path:"Clase de mención"', "color": {"a": 1, "rgb": rgb("#e0663d")}},
            {"query": "path:Órganos", "color": {"a": 1, "rgb": rgb("#3d7be0")}},
            {"query": "path:Términos", "color": {"a": 1, "rgb": rgb("#b44be0")}},
            {"query": "path:Circuitos", "color": {"a": 1, "rgb": rgb("#d9b100")}},
            {"query": 'path:"Tipos de asunto"', "color": {"a": 1, "rgb": rgb("#00a3b4")}},
        ],
        "showTags": False, "showAttachments": False, "hideUnresolved": True,
        "nodeSizeMultiplier": 1.2, "lineSizeMultiplier": 0.5,
        "centerStrength": 0.45, "repelStrength": 12, "linkStrength": 1, "linkDistance": 180,
    }
    (cfg / "graph.json").write_text(json.dumps(grafo, indent=2), encoding="utf-8")
    n_notas = sum(1 for _ in BOVEDA.rglob("*.md"))
    print(f"bóveda en {BOVEDA}: {n_notas} notas "
          f"({sum(ejes['Órganos'].values())} sentencias, {len(ejes['Órganos'])} órganos, "
          f"{len(ejes['Circuitos'])} circuitos, {len(ejes['Tipos de asunto'])} tipos de asunto)")


if __name__ == "__main__":
    main()
````
