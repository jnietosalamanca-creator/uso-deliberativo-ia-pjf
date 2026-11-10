# Uso deliberativo de la inteligencia artificial en el Poder Judicial de la Federación: código y datos

Material complementario del artículo «Uso deliberativo de la inteligencia artificial en el Poder Judicial de la
Federación: el prompt en la sentencia y el control del resultado». Cada carpeta corresponde a un anexo del artículo.

| Carpeta | Anexo | Contenido |
|---|---|---|
| `anexo_A_corpus/` | A. Código del corpus | Protocolo de construcción y réplica del corpus (`PROTOCOLO.md`, del que se extrae el código), la lista original de sentencias (`metadata.jsonl`) y el manifiesto con la huella SHA-256 de cada documento (`manifiesto.csv`). |
| `anexo_B_cribado/` | B. Código del cribado | Las tres reglas del filtro (`universo_del_caso.py`), la consolidación de usos institucionales (`consolidar_usos.py`), la página de verificación manual (`armar_verificador.py`, `plantilla_verificador.html`, `pasar_verificacion.py`) y sus resultados (`usos_propios.csv`, `correcciones_verificacion.csv` y las decisiones de la verificación). |
| `anexo_C_agente/` | C. Código del agente codificador | Prompt de lanzamiento (`prompt.txt`), instrucciones y libro de códigos v1.0 (`insumos_v10/instrucciones.md`), las 17 fichas que recibió el agente, el programa de réplica (`replicar.py`), el cálculo del alfa de Krippendorff (`alfa.py`) y las codificaciones originales. Ver `LEEME.md`. |
| `anexos_D_E_recalculos/` | D y E. Recálculos | Recálculo sin IA de la garantía de la queja 212/2025 y del cómputo de caducidad del amparo directo 170/2026 (`recalculos.py`), con cada paso en `recalculos.md`. |

## Notas

- El corpus no se incluye: las sentencias son versiones públicas del Buscador de Sentencias del Órgano de
  Administración Judicial, y el Anexo A permite descargarlas de nuevo y comprobar, con el manifiesto, que son las mismas.
- Ningún paso del corpus ni del cribado usa un modelo de lenguaje para clasificar. `universo_del_caso.py` importa una
  función auxiliar de `clasificar_modelo.py`; la clasificación con modelo que ese archivo permite no se usó en el
  cribado del artículo.
- Los programas del cribado se escribieron para correr dentro de la carpeta de trabajo original; las rutas que usan
  se indican al inicio de cada archivo.
- El código se escribió con asistencia de Claude Code. El modelo de lenguaje fue, además, el segundo codificador del
  estudio; el artículo declara cada una de sus intervenciones (apartado 2, paso 7).
