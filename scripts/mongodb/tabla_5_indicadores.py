
import os
from pathlib import Path

from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.errors import PyMongoError


# ==========================================
# CONFIGURACIÓN
# ==========================================

RAIZ = Path(__file__).resolve().parents[2]

load_dotenv(RAIZ / ".env")

MONGODB_URI = os.getenv("MONGODB_URI")
DATABASE_NAME = os.getenv("DATABASE_NAME")

client = None

try:
    if not MONGODB_URI or not DATABASE_NAME:
        raise ValueError("Faltan variables en el archivo .env")

    # ==========================================
    # CONEXIÓN A MONGODB
    # ==========================================

    client = MongoClient(
        MONGODB_URI,
        serverSelectionTimeoutMS=5000
    )

    client.admin.command("ping")

    db = client[DATABASE_NAME]

    colecciones = db.list_collection_names()

    if not {"municipios", "anuncios"}.issubset(colecciones):
        raise ValueError(
            "Faltan las colecciones municipios o anuncios"
        )

    # ==========================================
    # PIPELINE DE AGREGACIÓN
    # ==========================================

    pipeline = [

        # 1. Municipios con datos de alquiler y salario
        {
            "$match": {
                "indicadores.eustat_alquiler_medio_2024": {
                    "$type": "number",
                    "$gt": 0
                },
                "indicadores.salario_neto_mensual": {
                    "$type": "number",
                    "$gt": 0
                },
                "indicadores.esfuerzo_alquiler_pct": {
                    "$type": "number"
                }
            }
        },

        # 2. Relacionar municipios con anuncios válidos
        {
            "$lookup": {
                "from": "anuncios",
                "let": {"codigo_ine": "$_id"},
                "pipeline": [
                    {
                        "$match": {
                            "$expr": {
                                "$eq": [
                                    "$municipio_id",
                                    "$$codigo_ine"
                                ]
                            },
                            "operacion": "venta",
                            "precio": {"$gt": 0},
                            "calidad.precio_no_valido": {"$ne": True},
                            "calidad.posible_duplicado": {"$ne": True},
                            "calidad.posible_duplicado_ampliado": {"$ne": True}
                        }
                    },
                    {
                        "$group": {
                            "_id": None,
                            "precio_medio": {"$avg": "$precio"},
                            "num_anuncios": {"$sum": 1}
                        }
                    }
                ],
                "as": "compraventa"
            }
        },

        # 3. Solo municipios con compraventa
        {
            "$unwind": "$compraventa"
        },

        # 4. Seleccionar y calcular indicadores
        {
            "$project": {
                "_id": 0,
                "municipio": "$nombre",
                "provincia": 1,

                "alquiler_mensual": {
                    "$round": [
                        "$indicadores.eustat_alquiler_medio_2024",
                        2
                    ]
                },

                "salario_neto": {
                    "$round": [
                        "$indicadores.salario_neto_mensual",
                        2
                    ]
                },

                "esfuerzo_alquiler": {
                    "$round": [
                        "$indicadores.esfuerzo_alquiler_pct",
                        2
                    ]
                },

                "precio_compraventa": {
                    "$round": [
                        "$compraventa.precio_medio",
                        2
                    ]
                },

                "anios_compra": {
                    "$round": [
                        {
                            "$divide": [
                                "$compraventa.precio_medio",
                                {
                                    "$multiply": [
                                        "$indicadores.salario_neto_mensual",
                                        12
                                    ]
                                }
                            ]
                        },
                        2
                    ]
                },

                "num_anuncios": "$compraventa.num_anuncios"
            }
        },

        # 5. Ordenar por esfuerzo de alquiler
        {
            "$sort": {
                "esfuerzo_alquiler": -1
            }
        }
    ]

    # ==========================================
    # EJECUTAR CONSULTA
    # ==========================================

    resultados = list(
        db.municipios.aggregate(pipeline)
    )

    if not resultados:
        raise ValueError("La consulta no ha devuelto resultados")

    # ==========================================
    # MOSTRAR TABLA
    # ==========================================

    encabezado = (
        f"{'Municipio':<23}"
        f"{'Alquiler €':>12}"
        f"{'Salario €':>12}"
        f"{'Esfuerzo %':>13}"
        f"{'Compra €':>15}"
        f"{'Años':>9}"
    )

    print("\nTABLA DE CINCO INDICADORES")
    print("=" * len(encabezado))
    print(encabezado)
    print("-" * len(encabezado))

    for r in resultados:
        print(
            f"{r['municipio'][:22]:<23}"
            f"{r['alquiler_mensual']:>12,.2f}"
            f"{r['salario_neto']:>12,.2f}"
            f"{r['esfuerzo_alquiler']:>13.2f}"
            f"{r['precio_compraventa']:>15,.2f}"
            f"{r['anios_compra']:>9.2f}"
        )

    print("-" * len(encabezado))
    print(f"Total de municipios: {len(resultados)}")

except (PyMongoError, ValueError, KeyError) as error:
    print(f"ERROR: {error}")

finally:
    if client is not None:
        client.close()
