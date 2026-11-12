
from pathlib import Path
import argparse
import json
import os
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parent.parent

PROCESAMIENTO = ROOT / "scripts" / "procesamiento"
MONGODB = ROOT / "scripts" / "mongodb"
DATOS_MONGODB = ROOT / "data" / "mongodb"

DB_TEST = "EUSKADI_VIVIENDA_BIGDATA_TEST"

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

TAREAS_IMPORTACION = [
    "importar_municipios.py",
    "importar_anuncios.py",
    "importar_alquiler.py",
    "importar_salarios.py",
    "importar_economia.py",
]

RECUENTOS_ESPERADOS = {
    "municipios": 252,
    "anuncios": 2952,
    "mercado_alquiler": 3,
    "salarios": 120,
    "economia_juvenil": 148,
}


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
    print(
        f">>> OK: {script} ({duracion:.2f} segundos)",
        flush=True
    )


def ejecutar_procesamiento():
    for tarea in TAREAS_PROCESAMIENTO:
        ejecutar(PROCESAMIENTO, tarea)


def ejecutar_analisis():
    entorno = os.environ.copy()
    entorno["MPLBACKEND"] = "Agg"

    for tarea in TAREAS_ANALISIS:
        ejecutar(MONGODB, tarea, entorno)


def entorno_test():
    entorno = os.environ.copy()
    entorno["DATABASE_NAME"] = DB_TEST

    # Evitar que una URI alternativa apunte a otro servidor.
    uri = entorno.get(
        "MONGODB_URI",
        "mongodb://localhost:27017/"
    )

    if uri not in (
        "mongodb://localhost:27017",
        "mongodb://localhost:27017/"
    ):
        raise RuntimeError(
            "La fase MongoDB solo admite MongoDB local."
        )

    entorno["MONGODB_URI"] = "mongodb://localhost:27017/"
    return entorno


def verificar_json_municipios():
    archivo = DATOS_MONGODB / "municipios_mongodb.json"

    with open(archivo, encoding="utf-8") as f:
        municipios = json.load(f)

    if not isinstance(municipios, list):
        raise RuntimeError("El JSON de municipios no es una lista.")

    if len(municipios) != 252:
        raise RuntimeError(
            f"Se esperaban 252 municipios y hay {len(municipios)}."
        )

    ids = [m["_id"] for m in municipios]

    if len(set(ids)) != len(ids):
        raise RuntimeError("Existen IDs municipales duplicados.")

    for municipio in municipios:
        codigo = municipio["_id"]

        if (
            not isinstance(codigo, str)
            or len(codigo) != 5
            or not codigo.isdigit()
        ):
            raise RuntimeError(
                f"Codigo INE incorrecto: {codigo}"
            )

    print("Validacion inicial: 252 municipios correctos.")


def verificar_recuentos(db, etapa):
    print(f"\n=== VERIFICACION: {etapa} ===")

    for nombre, esperado in RECUENTOS_ESPERADOS.items():
        obtenido = db[nombre].count_documents({})

        print(f"{nombre}: {obtenido} / {esperado}")

        if obtenido != esperado:
            raise RuntimeError(
                f"Recuento incorrecto en {nombre}: "
                f"{obtenido} en lugar de {esperado}"
            )

    print("Todos los recuentos son correctos.")


def ejecutar_mongodb():
    from pymongo import MongoClient

    entorno = entorno_test()

    if entorno["DATABASE_NAME"] != DB_TEST:
        raise RuntimeError("Base de datos no autorizada.")

    print("\n======================================")
    print("AUTOMATIZACION MONGODB")
    print("Base de datos:", DB_TEST)
    print("======================================")

    with MongoClient(
        entorno["MONGODB_URI"],
        serverSelectionTimeoutMS=5000
    ) as client:

        client.admin.command("ping")
        db = client[DB_TEST]

        # Comprobar que la base de pruebas ya esta preparada.
        verificar_recuentos(db, "ANTES DE IMPORTAR")

        # Validar el JSON municipal.
        verificar_json_municipios()

        # Ejecutar validacion informativa existente.
        ejecutar(
            MONGODB,
            "validar_municipios.py",
            entorno
        )

        # Importar las cinco colecciones.
        for tarea in TAREAS_IMPORTACION:
            ejecutar(MONGODB, tarea, entorno)

        # Comprobar que la importacion conserva los recuentos.
        verificar_recuentos(db, "DESPUES DE IMPORTAR")

        # Auditar estructura y referencias.
        ejecutar(
            MONGODB,
            "revisar_colecciones.py",
            entorno
        )

        # Limpieza y transformacion con PyMongo.
        ejecutar(
            MONGODB,
            "limpiar_datos.py",
            entorno
        )

        # Verificar resultados de limpieza.
        anuncios = db["anuncios"]

        procesados = anuncios.count_documents({
            "limpieza": {"$exists": True}
        })

        print("\nAnuncios con campo limpieza:", procesados)

        if procesados != 2952:
            raise RuntimeError(
                "No todos los anuncios tienen datos de limpieza."
            )

        verificar_recuentos(db, "DESPUES DE LIMPIEZA")

        # Consultas principales.
        ejecutar(
            MONGODB,
            "consultas_ra3.py",
            entorno
        )

    print("\nAUTOMATIZACION MONGODB FINALIZADA")


def main():
    parser = argparse.ArgumentParser(
        description="Orquestador EUSKADI_VIVIENDA_BIGDATA"
    )

    parser.add_argument(
        "--fase",
        choices=["procesamiento", "analisis", "mongodb"],
        required=True
    )

    args = parser.parse_args()
    inicio = time.perf_counter()

    try:
        if args.fase == "procesamiento":
            ejecutar_procesamiento()

        elif args.fase == "analisis":
            ejecutar_analisis()

        elif args.fase == "mongodb":
            ejecutar_mongodb()

    except (
        subprocess.CalledProcessError,
        FileNotFoundError,
        RuntimeError,
        OSError,
        ValueError,
        KeyError
    ) as error:
        print(f"\nERROR: {error}", file=sys.stderr)
        sys.exit(1)

    print("\n======================================")
    print(f"FASE {args.fase.upper()} FINALIZADA")
    print(
        f"Tiempo total: "
        f"{time.perf_counter() - inicio:.2f} segundos"
    )
    print("======================================")


if __name__ == "__main__":
    main()
