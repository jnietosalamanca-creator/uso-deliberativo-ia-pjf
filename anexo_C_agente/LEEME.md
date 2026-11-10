# Réplica del agente codificador

Paquete para que otra persona repita lo que hizo el «codificador 2» del artículo: un agente de Claude que codifica
las sentencias con el libro de códigos v1.0, sin ver los códigos del autor. No depende del resto del proyecto.

El agente no es un programa propio: es Claude Code con un prompt fijo. Lo que define al agente es esto:

| Pieza | Archivo |
|---|---|
| Prompt de lanzamiento, idéntico al original salvo las rutas | `prompt.txt` |
| Reglas de trabajo y libro de códigos v1.0 | `insumos_v10/instrucciones.md` |
| Las 17 fichas (14 vigentes; 3 resultaron no ser uso propio) | `insumos_v10/fichas/` y `fichas.json` |
| Modelo | `claude-opus-5-5` |
| Preparación, lanzamiento, revisión y comparación | `replicar.py` |
| Resultados originales, para comparar | `originales/` |

## Requisitos

- Python 3.9 o superior (solo biblioteca estándar).
- [Claude Code](https://claude.com/claude-code) instalado, con sesión iniciada (`claude`, luego `/login`).
- Acceso al modelo `claude-opus-5-5`. Si ya no está disponible, la réplica debe reportar el modelo que usó.

## Pasos

Todos los comandos se corren desde esta carpeta (`replica_agente/`); si no, Python no encuentra `replicar.py`.

Primero una prueba barata con una sola ficha, para confirmar que la instalación funciona:

```bash
python3 replicar.py preparar prueba --prueba
```

```bash
python3 replicar.py correr prueba
```

```bash
python3 replicar.py revisar prueba
```

Después, dos corridas completas e independientes (en la original, unos 10 minutos cada una):

```bash
python3 replicar.py preparar 1
```

```bash
python3 replicar.py correr 1
```

```bash
python3 replicar.py revisar 1
```

Repite esos tres pasos con `2`. Luego compara:

```bash
python3 replicar.py comparar ~/replica_agente_trabajo/corrida_1/replica_corrida1.csv ~/replica_agente_trabajo/corrida_2/replica_corrida2.csv
```

```bash
python3 replicar.py comparar originales/agente_corrida1.csv ~/replica_agente_trabajo/corrida_1/replica_corrida1.csv
```

```bash
python3 replicar.py comparar originales/autor.csv ~/replica_agente_trabajo/corrida_1/replica_corrida1.csv
```

`revisar` reporta fichas faltantes, valores fuera del libro, faltantes por regla de pase, citas que no aparecen
literalmente en la sentencia, el modelo que respondió y cualquier ruta fuera de la carpeta de trabajo.

## Qué se puede esperar

No saldrá idéntico. El modelo no es determinista: las dos corridas originales tampoco coincidieron entre sí
(ver `originales/consistencia_corrida1_vs_2.csv`). Replicar aquí significa repetir el procedimiento y medir cuánto
se parece el resultado, campo por campo.

## En qué difiere del original

| | Original (oct-2026) | Esta réplica |
|---|---|---|
| Forma de lanzarlo | Subagente `general-purpose` dentro de una sesión de Claude Code 2.1.295 | Claude Code en modo `-p --restricted` |
| Ceguera | Por instrucción, comprobada después en los registros | Técnica: carpeta aparte, archivos confinados a ella |
| Herramientas | Con `Bash`: lectura de fichas y unos 10 cálculos auxiliares en Python | `Read`, `Write`, `Grep`, `Glob`, sin comandos |
| Contexto del usuario | Recibió un índice de memoria de 5 líneas, ajeno a la codificación | Ninguno |

Quitar `Bash` es deliberado: el agente lee texto de terceros y no debe poder ejecutar comandos. El costo es que no
puede hacer cuentas con Python, lo que puede afectar `recalculo`. Ese campo debe mirarse con cuidado al comparar.

## Comprobaciones hechas

- `prompt.txt`, con las rutas originales, es idéntico a los dos prompts lanzados.
- `revisar`, aplicado a la salida original de la corrida 1, da 0 problemas y el mismo CSV que `recoger.py`.
- `comparar` reproduce exactas las tablas de `originales/`: corrida 1 contra 2 y autor contra corrida 1.
- **Sin probar todavía:** una corrida del modelo de punta a punta con este paquete. La prueba llegó hasta el
  arranque de Claude Code (modelo y herramientas correctos) y paró por falta de sesión iniciada.

## Antes de compartirlo

Las corridas envían el texto de las sentencias a Anthropic. `originales/` trae los códigos del autor: es lo que
permite comparar, pero compartirlo es decisión del autor.
