
from pathlib import Path
import argparse
import os
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parent.parent

PROCESAMIENTO = ROOT / "scripts" / "procesamiento"
MONGODB = ROOT / "scripts" / "mongodb"

TAREAS_PROCESAMIENTO = [
    "normalizar_municipios.py",
    "integrar_eustat_ine.py",
    "integrar_alquiler_emal.py",
    "integrar_compraventa_municipios.py",
    "procesar_salarios_juventud.py",
    "calcular_esfuerzo_alquiler.py",
    "calcular_esfuerzo_compra.py",
    "integrar_indicadores_finales.py",
]

TAREAS_ANALISIS = [
    "tabla_5_indicadores.py",
    "01_esfuerzo_provincias_crea_grafico.py",
    "02_precios_compraventa_crea_grafico.py",
    "03_alquiler_vs_compra_crea_grafico.py",
    "04_municipios_asequibles_crea_grafico.py",
]


def ejecutar(carpeta, script, entorno=None):
    ruta = carpeta / script

    if not ruta.is_file():
        raise FileNotFoundError(f"No se encuentra: {ruta}")

    print(f"\n>>> Ejecutando: {script}", flush=True)
    inicio = time.perf_counter()

    subprocess.run(
        [sys.executable, str(ruta)],
        cwd=ROOT,
        check=True,
        env=entorno
    )

    duracion = time.perf_counter() - inicio
    print(f">>> OK: {script} ({duracion:.2f} segundos)", flush=True)


def ejecutar_procesamiento():
    for tarea in TAREAS_PROCESAMIENTO:
        ejecutar(PROCESAMIENTO, tarea)


def ejecutar_analisis():
    # Evita que los gráficos bloqueen la automatización.
    entorno = os.environ.copy()
    entorno["MPLBACKEND"] = "Agg"

    for tarea in TAREAS_ANALISIS:
        ejecutar(MONGODB, tarea, entorno)


def main():
    parser = argparse.ArgumentParser(
        description="Orquestador EUSKADI_VIVIENDA_BIGDATA"
    )

    parser.add_argument(
        "--fase",
        choices=["procesamiento", "analisis"],
        required=True
    )

    args = parser.parse_args()
    inicio = time.perf_counter()

    try:
        if args.fase == "procesamiento":
            ejecutar_procesamiento()
        elif args.fase == "analisis":
            ejecutar_analisis()

    except (subprocess.CalledProcessError, FileNotFoundError) as error:
        print(f"\nERROR: {error}", file=sys.stderr)
        sys.exit(1)

    print("\n======================================")
    print(f"FASE {args.fase.upper()} FINALIZADA")
    print(f"Tiempo total: {time.perf_counter() - inicio:.2f} segundos")
    print("======================================")


if __name__ == "__main__":
    main()
