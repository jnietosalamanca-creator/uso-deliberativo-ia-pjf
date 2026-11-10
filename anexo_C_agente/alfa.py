#!/usr/bin/env python3
"""Alfa de Krippendorff (datos nominales) con intervalo de confianza por bootstrap y matriz de confusión.

    python3 alfa.py CODIGOS_A.csv CODIGOS_B.csv [--campo codigo] [--libro v2-2026-10-03] [--remuestreos 10000] [--semilla 20261003]

Cada CSV tiene al menos las columnas id_muestra y el campo a comparar (una fila por unidad; si hay varias, cuenta
la última por orden de la columna ts, si existe). Se comparan sólo las unidades que ambos codificaron con un valor no
vacío en ese campo. --campo criterio_judicial mide la etapa 2 (sólo las unidades que ambos dejaron como genéricas).
--libro descarta las filas de otra versión del libro (si el CSV tiene la columna libro).

Alfa = 1 - Do / De, con la matriz de coincidencias de Krippendorff (Krippendorff, 2004; Hayes y
Krippendorff, 2007). Va de 0 a 1 (puede ser negativo si el desacuerdo supera al del azar). Umbrales del
protocolo: >= 0.80 confiable; 0.667-0.80 sólo conclusiones tentativas; < 0.667 no confiable.

Intervalo de confianza: bootstrap por remuestreo de UNIDADES con reemplazo (percentiles 2.5 y 97.5), con
semilla fija. Nota: no es el algoritmo de bootstrap de Hayes y Krippendorff (KALPHA), que remuestrea pares
de valores; si el protocolo exige ese, hay que reportarlo así.
Sólo usa la biblioteca estándar de Python.
"""
import argparse
import csv
import random
from collections import Counter, defaultdict


def alfa_nominal(unidades):
    """unidades: lista de listas con los valores asignados a cada unidad por los codificadores (None = falta).
    Devuelve el alfa nominal de Krippendorff, o None si no hay variación con qué calcularlo."""
    # Construye la matriz de coincidencias con las unidades que tienen al menos dos valores
    o = Counter()
    for valores in unidades:
        v = [x for x in valores if x is not None]
        m = len(v)
        if m < 2:
            continue
        for i in range(m):
            for j in range(m):
                if i != j:
                    o[(v[i], v[j])] += 1 / (m - 1)
    n_c = Counter()
    for (c, k), x in o.items():
        n_c[c] += x
    n = sum(n_c.values())
    if n <= 1:
        return None
    # Desacuerdo observado y esperado (nominal: distancia 1 si los valores difieren)
    d_o = sum(x for (c, k), x in o.items() if c != k) / n
    d_e = sum(n_c[c] * n_c[k] for c in n_c for k in n_c if c != k) / (n * (n - 1))
    return None if d_e == 0 else 1 - d_o / d_e


def bootstrap(pares, remuestreos, semilla):
    """Intervalo de confianza del 95 % remuestreando unidades con reemplazo."""
    rng = random.Random(semilla)
    valores = []
    for _ in range(remuestreos):
        a = alfa_nominal([pares[rng.randrange(len(pares))] for _ in pares])
        if a is not None:
            valores.append(a)
    valores.sort()
    if not valores:
        return None, None
    return valores[int(0.025 * len(valores))], valores[int(0.975 * len(valores)) - 1]


def leer(ruta, campo="codigo", libro=None):
    """Último valor del campo para cada unidad en un CSV con columnas id_muestra, el campo y, opcionalmente, ts y libro."""
    with open(ruta, encoding="utf-8-sig") as f:
        filas = list(csv.DictReader(f))
    # Descarta las filas de otra versión del libro y ordena por fecha para quedarse con la última
    if libro:
        filas = [r for r in filas if r.get("libro", libro) == libro]
    filas.sort(key=lambda r: r.get("ts", ""))
    ultimo = {r["id_muestra"]: (r.get(campo) or "").strip() for r in filas}
    return {k: v for k, v in ultimo.items() if v}


def main():
    # Lee los dos archivos de códigos de la línea de comandos
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("a")
    ap.add_argument("b")
    ap.add_argument("--campo", default="codigo")
    ap.add_argument("--libro", default=None)
    ap.add_argument("--remuestreos", type=int, default=10000)
    ap.add_argument("--semilla", type=int, default=20261003)
    x = ap.parse_args()
    A, B = leer(x.a, x.campo, x.libro), leer(x.b, x.campo, x.libro)
    # Compara sólo las unidades que ambos codificaron
    comunes = sorted(set(A) & set(B))
    pares = [[A[i], B[i]] for i in comunes]
    a = alfa_nominal(pares)
    lo, hi = bootstrap(pares, x.remuestreos, x.semilla)
    # Imprime alfa, intervalo, acuerdo simple y matriz de confusión
    print(f"Campo: {x.campo}" + (f" · libro {x.libro}" if x.libro else ""))
    print(f"Unidades comparadas: {len(comunes)}")
    print(f"Acuerdo simple: {sum(p == q for p, q in pares) / len(pares):.1%}")
    print(f"Alfa de Krippendorff (nominal): {a:.3f}" if a is not None else "Alfa: no calculable (sin variación)")
    if lo is not None:
        print(f"IC 95 % por bootstrap ({x.remuestreos} remuestreos de unidades, semilla {x.semilla}): [{lo:.3f}, {hi:.3f}]")
    cats = sorted({v for p in pares for v in p})
    m = defaultdict(int)
    for p, q in pares:
        m[(p, q)] += 1
    print("\nMatriz de confusión (filas: " + x.a + "; columnas: " + x.b + ")")
    print(" " * 14 + "".join(f"{c:>12}" for c in cats))
    for c in cats:
        print(f"{c:>14}" + "".join(f"{m[(c, k)]:>12}" for k in cats))


if __name__ == "__main__":
    main()
