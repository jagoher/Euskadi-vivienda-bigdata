
import os
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.errors import PyMongoError

# ==========================================
# CONFIGURACIÓN
# ==========================================

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI")
DATABASE_NAME = os.getenv("DATABASE_NAME")

client = None

try:
    # Comprobar variables de entorno
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

    if "municipios" not in db.list_collection_names():
        raise ValueError("La colección 'municipios' no existe")

    coleccion = db["municipios"]

    # ==========================================
    # PIPELINE 1: ESFUERZO POR PROVINCIA
    # ==========================================

    pipeline = [
        {
            "$match": {
                "indicadores.esfuerzo_alquiler_pct": {
                    "$type": "number"
                }
            }
        },
        {
            "$group": {
                "_id": "$provincia",
                "municipios": {"$sum": 1},
                "esfuerzo_medio": {
                    "$avg": "$indicadores.esfuerzo_alquiler_pct"
                },
                "superan_30": {
                    "$sum": {
                        "$cond": [
                            {
                                "$gt": [
                                    "$indicadores.esfuerzo_alquiler_pct",
                                    30
                                ]
                            },
                            1,
                            0
                        ]
                    }
                }
            }
        },
        {
            "$project": {
                "_id": 0,
                "provincia": "$_id",
                "municipios": 1,
                "superan_30": 1,
                "esfuerzo_medio": {
                    "$round": ["$esfuerzo_medio", 2]
                },
                "porcentaje_superan": {
                    "$round": [
                        {
                            "$multiply": [
                                {
                                    "$divide": [
                                        "$superan_30",
                                        "$municipios"
                                    ]
                                },
                                100
                            ]
                        },
                        2
                    ]
                }
            }
        },
        {
            "$sort": {
                "esfuerzo_medio": -1
            }
        }
    ]

    # ==========================================
    # EJECUTAR AGREGACIÓN
    # ==========================================

    resultados = list(coleccion.aggregate(pipeline))

    # ==========================================
    # MOSTRAR RESULTADOS
    # ==========================================

    print("\n=== ESFUERZO DE ALQUILER POR PROVINCIA ===\n")

    if not resultados:
        print("No se encontraron datos.")
    else:
        for provincia in resultados:
            print(f"Provincia: {provincia['provincia']}")
            print(f"Municipios analizados: {provincia['municipios']}")
            print(f"Esfuerzo medio: {provincia['esfuerzo_medio']:.2f} %")
            print(f"Superan el 30 %: {provincia['superan_30']}")
            print(
                f"Porcentaje que supera el 30 %: "
                f"{provincia['porcentaje_superan']:.2f} %"
            )
            print("-" * 50)

        total = sum(p["municipios"] for p in resultados)
        print(f"\nTotal de municipios analizados: {total}")

# ==========================================
# CONTROL DE ERRORES
# ==========================================

except (PyMongoError, ValueError, KeyError, TypeError) as error:
    print(f"ERROR: {error}")

finally:
    if client is not None:
        client.close()
