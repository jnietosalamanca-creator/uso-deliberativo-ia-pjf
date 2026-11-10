# Instrucciones para codificar el piloto (codificador 2)

Eres el segundo codificador de un análisis de contenido sobre los usos de inteligencia artificial que los órganos
del Poder Judicial de la Federación declaran en sus sentencias. Codificas a ciegas y por tu cuenta.

## Reglas de trabajo
1. Lee SOLO los archivos de esta carpeta (`instrucciones.md`, `fichas.json` y `fichas/`). No abras ningún otro
   archivo del equipo, no busques otras codificaciones y no uses internet.
2. Codifica cada ficha con el libro de códigos de abajo. Cada ficha es UN uso; si trae un aviso (uso institucional,
   versión del machote), síguelo.
3. Cada valor se respalda con una **cita textual exacta**, copiada carácter por carácter de la ficha (puede ser un
   fragmento de 5 a 40 palabras). No parafrasees ni corrijas la cita.
4. Lo que la sentencia no dice se codifica como «no declara» o el valor equivalente que prevé el libro; no infieras.
5. Reglas de pase: `p_norma`, `p_hechos`, `p_metodo` y `p_limites` solo si `prompt` es `completo` o `parcial`
   (si no, déjalos vacíos); `recalculo` solo si `tarea_numerica` = `si` (si no, `no_aplica`).
   `herramienta`: escribe el nombre como lo da la sentencia, o `no_declara`.
   `recalculo`: no rehagas cuentas largas; si la sentencia no da datos y método suficientes, `no_recalculable`.
6. Usa exactamente los códigos del libro (por ejemplo `calculo_garantia`, `no_transcrito`), sin acentos ni espacios.

## Formato de salida
Escribe UN archivo, en la ruta que te indique quien te encarga la tarea, en formato JSON Lines (un objeto por
renglón, uno por ficha, en el orden de `fichas.json`):

{"unidad": "...", "sentencia": "...", "valores": {"tarea": "...", ...}, "citas": {"tarea": "...", ...}, "nota": "..."}

`valores` lleva los 23 campos del libro (secciones 2 a 6) que apliquen; `citas` lleva la cita de cada valor que
pusiste; `nota` es breve (dudas, casos límite). No escribas nada más en ese archivo.

---

# Libro de códigos: usos de IA declarados por el órgano

Versión: 1.0 (27-oct-2026), fijada al cerrar el piloto (antes: 0.3 y 0.2 del 26-oct-2026, 0.1 del 15-oct-2026). Sustituye como libro central al de voz, categoría y figura (`libro_de_codigos.md`), que queda como antecedente.

- 27-oct-2026 (v1.0, decisión del autor al cerrar el piloto): `verificable` deja de codificarse como juicio global (en el piloto, el autor y el agente lo entendieron distinto: alfa 0.02–0.13); el nivel de replicabilidad se **calcula** a partir de componentes (sección 6 bis, `exploracion/nivel_replicabilidad.py`). Campo nuevo `resultado` (no piloteado). Campos declarados tentativos: ver «Confiabilidad».
- 26-oct-2026 (v0.3): reglas de la segunda ronda del piloto, decididas por Claude por delegación expresa del autor: `calculo_garantia` abarca cualquier garantía, caución o fianza que fije el órgano; `c_informa` pasa a `previo` · `en_sentencia` · `no`; `respuesta_ia` solo es `completa` o `parcial` si la sentencia atribuye el texto a la IA; la cita de un valor negativo es el pasaje que declara el uso. Ver «Reglas de decisión».
- 26-oct-2026 (v0.2): reglas que salieron del piloto (desacuerdos entre el autor y el agente codificador): valores nuevos `accesibilidad` (tarea) y `no_aplica` (fundamentación y motivación); definiciones de `calculo_garantia`, `sintesis_ciudadana`, `resumen`, `analisis_prueba`, `justifica`, `p_hechos`, `p_limites` y de los valores de `verificable`. Ver «Reglas de decisión».

Objeto: los usos de inteligencia artificial que el propio órgano declara en el texto de sus sentencias, evaluados con los elementos mínimos de la jurisprudencia II.2o.C. J/2 K (12a.) y con el deber de fundar y motivar.

- **Unidad de muestreo:** la sentencia. No se muestrea: se analizan todas las que declaran un uso propio.
- **Unidad de análisis:** cada uso declarado. Una sentencia puede tener varios; cada uno lleva su `id_uso`.
- **Unidad de contexto:** la sentencia completa y el recorte de la página del PDF original.
- **Regla general:** cada valor se respalda con la cita textual que lo sostiene (campo `cita_*`). Lo que la sentencia no dice se codifica como «no declara»; no se infiere. Para un valor negativo («no», «no declara», «no transcrito», «falta», «ninguno») se cita el pasaje donde la sentencia declara el uso, que es donde ese dato tendría que aparecer.

> Pendiente: cotejar la redacción de los cuatro elementos con el texto oficial de la tesis (Gaceta del SJF, registro digital 2031640). La de abajo sigue la descripción publicada del criterio.

## 0. Cribado: ¿hay uso propio declarado?

| Código | Definición |
|---|---|
| `si` | El órgano, o su personal, dice que usó una herramienta de IA para una tarea del asunto. |
| `no` | No hay uso propio: cita la tesis sin usar IA, relata el uso de una parte, la IA es objeto del litigio o solo se nombra. |
| `duda` | No se puede decidir con la sentencia completa; anotar por qué en `nota`. |

Solo los `si` pasan a los apartados 1 a 7.

## 1. Identificación (de los metadatos del OAJ; no se codifica a mano)

`id_sentencia`, `id_uso`, `fecha`, `organo`, `tipo_organo`, `circuito`, `materia`.

## 2. El uso

| Campo | Valores |
|---|---|
| `tarea` | `calculo_garantia` (cualquier garantía, caución o fianza que fije el órgano; si no es la de la suspensión en amparo, anotarlo en `nota`) · `otra_cuantificacion` (reparación, indemnización, incrementos y otras cuentas) · `sintesis_ciudadana` (texto en lenguaje llano para las partes o el público; incluye lectura fácil) · `resumen` (resumen técnico, p. ej., de la carátula) · `accesibilidad` (versión en audio u otro formato accesible) · `busqueda` · `traduccion` · `analisis_prueba` (evaluar la fiabilidad de una prueba o de un hecho del expediente) · `redaccion` · `otra` (describir en `nota`) |
| `tarea_numerica` | `si` · `no` |
| `herramienta` | texto libre, como la nombra la sentencia (p. ej., ChatGPT); `no_declara` |
| `version_declarada` | `si` · `no` |
| `fecha_consulta_declarada` | `si` · `no` |
| `fundamento_uso` | `jurisprudencia_II2oC` (cualquiera de las cuatro tesis) · `otra_norma_o_instrumento` · `ninguno` |

## 3. Elementos mínimos de la jurisprudencia II.2o.C. J/2 K

| Elemento | Qué exige | Valores |
|---|---|---|
| `a_proporcionalidad` | Usar la IA solo en la medida necesaria y adecuada; para razonamientos numéricos o tareas repetitivas, sin sustituir el razonamiento jurídico. | `cumple` (tarea numérica o repetitiva) · `justifica` (no lo es, pero el órgano argumenta por qué la IA es necesaria y adecuada para esa tarea; invocar beneficios generales del formato no basta) · `no_cumple` |
| `b_datos` | Proteger los datos personales de las partes. | `declara` (dice qué hizo para protegerlos) · `no_declara` |
| `c_informa` | Informar a las partes del uso de la IA. | `previo` (informa a las partes antes de resolver o les da oportunidad de manifestarse) · `en_sentencia` (solo lo declara en la resolución) · `no` |
| `c_metodologia` | Explicar la metodología. | `si` · `no` |
| `c_datos_entrada` | Explicar los datos de entrada. | `si` · `no` |
| `c_resultado` | Explicar cómo se llegó al resultado. | `si` · `no` |
| `resultado` | ¿La sentencia dice qué produjo la IA (la cifra, el texto, el audio, la respuesta)? Campo nuevo en la v1.0, no piloteado. | `si` · `no` |
| `d_supervision` | La IA como auxiliar; la decisión es del juzgador. | `verifica` (contrasta o revisa el resultado) · `declara` (solo afirma que decide él) · `no_declara` |

## 4. El prompt

| Campo | Valores |
|---|---|
| `prompt` | `completo` · `parcial` · `no_transcrito` |
| `respuesta_ia` | `completa` (la sentencia atribuye a la IA el texto transcrito, completo) · `parcial` (atribuye a la IA un fragmento) · `no_transcrita` (no transcribe la respuesta, o lo que parece salida de la IA no se le atribuye) |

Si el prompt está transcrito (completo o parcial), se codifica qué contiene:

| Campo | Pregunta | Valores |
|---|---|---|
| `p_norma` | ¿Da la premisa normativa (el fundamento)? | `si` · `no` |
| `p_hechos` | ¿Trae los hechos o datos del caso, o declara que se adjunta el documento del caso? (Un prompt plantilla que solo los pide es `no`.) | `si` · `no` |
| `p_metodo` | ¿Pide un método o pasos (la adecuación entre norma y hechos)? | `si` · `no` |
| `p_limites` | ¿Restringe al modelo (fuentes, alcance, no inventar) o le pide verificar el resultado? (Pedirle que explique su método es `p_metodo`.) | `si` · `no` |

## 5. Fundamentación y motivación del tramo apoyado en la IA

El tramo es la parte de la resolución que usa lo que produjo la IA.

| Campo | Valores |
|---|---|
| `fundamentacion` | `suficiente` · `indebida` (cita una norma que no aplica) · `falta` (no cita norma) · `no_aplica` (el resultado de la IA no forma parte del razonamiento) |
| `motivacion` | `suficiente` · `indebida` (razones que no se adecuan al caso) · `falta` (no expresa razones) · `no_aplica` (el resultado de la IA no forma parte del razonamiento) |

## 6. Verificabilidad

| Campo | Pregunta | Valores |
|---|---|---|
| `recalculo` | Si la tarea es numérica: al rehacer la cuenta con los datos y el método de la sentencia… | `coincide` · `no_coincide` (anotar la diferencia) · `no_recalculable` · `no_aplica` |

No se vuelven a correr los prompts en los modelos actuales: no son los mismos y no prueba nada. Se rehace la aritmética.

## 6 bis. Nivel de replicabilidad (calculado, no se codifica)

Se asigna el nivel más alto cuyos requisitos se cumplen todos, con los valores ya codificados:

| Nivel | Nombre | Requisitos |
|---|---|---|
| 0 | Mención del uso | No cumple los del nivel 1 |
| 1 | Resultado sin respaldo | `herramienta` ≠ `no_declara`, `tarea` codificada y `resultado` = `si` |
| 2 | Respaldo parcial | Nivel 1 y, además, `c_datos_entrada` = `si` o `c_metodologia` = `si` (no ambos) |
| 3 | Revisable | Nivel 1 y, además, `c_datos_entrada` = `si` y `c_metodologia` = `si` |
| 4 | Reproducible | Nivel 3 y, además, `prompt` ≠ `no_transcrito`, `respuesta_ia` ≠ `no_transcrita`, y `version_declarada` = `si` o `fecha_consulta_declarada` = `si` |

Los componentes se publican junto con el nivel, para que quien prefiera otra agregación pueda hacerla. `verificable` (v0.1 a v0.3) puede conservarse como dato descriptivo, pero no entra al alfa ni al nivel.

## 7. Campos libres

- `cita_*`: la cita textual que respalda cada valor.
- `nota`: dudas y casos límite.

## Reglas de decisión

Del piloto, segunda ronda (26-oct-2026, v0.3; decididas por Claude por delegación del autor):
- `calculo_garantia` abarca cualquier garantía, caución o fianza que fije el órgano (suspensión en amparo, medida cautelar, inscripción de la demanda, etc.). Si no es la suspensión en amparo, se anota en `nota`, para distinguir después los usos fuera del ámbito de la tesis II.2o.C. J/1 K.
- `c_informa`: `previo` si el órgano informa a las partes del uso antes de resolver o les da oportunidad de manifestarse; `en_sentencia` si solo lo declara en la resolución; `no` si no lo informa. Toda sentencia que declara el uso es, al menos, `en_sentencia`.
- `respuesta_ia`: `completa` o `parcial` solo si la sentencia atribuye a la IA el texto, la tabla o el cálculo transcrito (p. ej., «la respuesta dada por cada plataforma fue»). Lo que parece salida de la IA pero no se le atribuye es `no_transcrita`, con nota.
- Cita de los valores negativos: se cita el pasaje donde la sentencia declara el uso; ningún valor queda sin cita.

Del piloto, primera ronda (26-oct-2026, v0.2):
- Fundamentación y motivación: se juzga solo el tramo que usa el resultado de la IA; la norma o las razones citadas en otra parte de la sentencia no cuentan. Si el resultado de la IA no forma parte del razonamiento (síntesis ciudadana, audio, lectura fácil), el valor es `no_aplica`.
- Tarea: `calculo_garantia` es solo la garantía de la suspensión; reparación, indemnización o incrementos van en `otra_cuantificacion`. `sintesis_ciudadana` se dirige a las partes o al público en lenguaje llano (incluye lectura fácil); `resumen` es técnico (carátula). Audio u otro formato accesible: `accesibilidad`. Evaluar con la IA la fiabilidad de una prueba o de un hecho del expediente (p. ej., Google Maps para medir distancias): `analisis_prueba`.
- `p_hechos` = `si` solo si el prompt trae los datos del caso o declara que se adjunta el documento del caso; un prompt plantilla que pide los datos al usuario es `no` (anotarlo en `nota`).
- `p_limites` = `si` solo si el prompt restringe al modelo (fuentes, alcance, no inventar) o le pide verificar; pedirle que explique su método es `p_metodo`.
- `verificable`: `si`, se puede rehacer o cotejar el resultado completo; `parcial`, falta algún elemento (montos testados) o se puede cotejar la fuente con el resultado pero no el proceso (síntesis o audio cuyo texto de origen está en la sentencia); `no`, no se puede cotejar nada.
- `a_proporcionalidad` = `justifica` solo si el órgano argumenta por qué la IA es necesaria y adecuada para esa tarea; invocar beneficios generales del formato (accesibilidad, transparencia) sin decir por qué hace falta la IA es `no_cumple`.

Anteriores:

- [por llenar con los primeros casos]
- Un uso que la sentencia atribuye a la IA de una parte no es uso propio (va a `no` en el cribado).
- Citar la tesis para justificar un cálculo que no se hizo con IA no es uso propio.
- Votos (24-oct-2026): los votos concurrentes o particulares no son la voz del órgano. Si comentan un uso declarado en la sentencia, se leen como contexto de ese uso y no se cuentan aparte; si un voto declara un uso que la sentencia no menciona, se anota como caso límite. Caso: 38079611_9 (voto concurrente en el AD 213/2025), contexto de 38079611.
- Uso institucional repetido (23-oct-2026): si un mismo órgano declara la misma tarea, con la misma herramienta y el mismo texto base (machote), en varias sentencias, se cuenta como **un solo uso**. Se registran el número de sentencias, la primera y la última fecha, y las versiones del machote. Se codifica una vez; si las versiones difieren en lo que exponen (p. ej., una transcribe el prompt y otra no), el nivel de replicabilidad se registra para cada versión, con cuántas sentencias tiene cada una. Casos: UI-01, la síntesis en lenguaje ciudadano del Juzgado Segundo de Distrito en Materia Administrativa especializado en Competencia Económica, Radiodifusión y Telecomunicaciones (`exploracion/consolidar_usos.py`; corrección del 26-oct-2026: UI-01 tiene una sola versión, porque las 196 sentencias transcriben la instrucción; 137 la rotulan «(en inglés: prompt)» y 59 no, lo que no cambia lo que exponen); UI-03, la nota sobre el resumen de hechos y la síntesis de la carátula elaborados con ChatGPT del Décimo Tribunal Colegiado en Materia Civil del Primer Circuito, identificada después de la verificación (`exploracion/unidades_de_conteo.py`); UI-04, el audio generado con IA a partir del texto de la sentencia del Primer Tribunal Colegiado en Materias Penal y Administrativa del Décimo Séptimo Circuito (2 sentencias, identificado al codificar el piloto, 24-oct-2026). UI-06: la nota al pie «Resolución que es elaborada con la asistencia de una inteligencia artificial que tiene como única finalidad sintetizar documentos complejos…» del Juzgado Primero de Distrito en el Estado de Guanajuato (3 sentencias; cambia solo el nombre de la secretaria; señalado por el agente al codificar el piloto y verificado en el texto, 26-oct-2026). Si una sentencia del machote declara además otro uso, ese otro uso se cuenta aparte.
- Uso institucional con método aplicado a cada caso (23-oct-2026): cuando el machote es un método (p. ej., un prompt estandarizado para calcular una garantía) y cada sentencia lo aplica a sus propios datos, también se cuenta como **un solo uso**; los datos, el resultado y el recálculo se registran **por sentencia** dentro del uso, y las variantes del método se anotan en cada sentencia. Caso: UI-02, el cálculo de garantías del Segundo Tribunal Colegiado en Materia Civil del Segundo Circuito (variantes: prompt estandarizado conforme a P./J. 71/2014, promedio de tres herramientas, prompt para rentas). Se define después de la verificación manual, sobre los usos propios verificados (`exploracion/unidades_de_conteo.py`). UI-05: el Juzgado Segundo de Distrito en Materia Civil y de Trabajo en el Estado de Nuevo León adopta el mismo método («con el objeto de hacer verificable el cálculo del monto de la garantía…»); como es otro órgano, es otro uso institucional (2 sentencias, identificado al codificar el piloto, 24-oct-2026).

## Confiabilidad

Un segundo codificador codifica todo el universo con este libro. El acuerdo se mide con el alfa de Krippendorff por campo (0.80 o más, suficiente; entre 0.667 y 0.80, tentativo). Al fijar la v1.0 (27-oct-2026), y con base en el piloto (12 usos; autor frente a un agente de Claude Opus 5.5 en tres rondas), quedan declarados **tentativos**: `c_datos_entrada`, `d_supervision`, `b_datos`, `p_limites` (solo 5 usos con prompt), `version_declarada` (casi sin variación), `respuesta_ia`, `herramienta` (diferencias de escritura) y `resultado` (no piloteado). Su confiabilidad se mide en la codificación definitiva. Para el cribado, se revisa además una muestra aleatoria de las sentencias que el filtro no marcó y se reporta cuántos usos se le escaparon.
