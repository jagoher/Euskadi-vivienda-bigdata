
from pymongo.errors import PyMongoError

from database import conectar, cerrar_conexion
from config import COLLECTIONS


def analizar_esfuerzo():
    db = None

    try:
        db = conectar()

        if db is None:
            print("ERROR: No se pudo conectar.")
            return

        pipeline = [
            {
                "$match": {
                    "indicadores.esfuerzo_alquiler_pct": {
                        "$ne": None
                    }
                }
            },
            {
                "$group": {
                    "_id": "$provincia",
                    "municipios": {"$sum": 1},
                    "superan_30": {
                        "$sum": {
                            "$cond": [
                                {"$eq": [
                                    "$indicadores.supera_30_pct",
                                    True
                                ]},
                                1,
                                0
                            ]
                        }
                    },
                    "esfuerzo_medio": {
                        "$avg": "$indicadores.esfuerzo_alquiler_pct"
                    }
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "provincia": "$_id",
                    "municipios": 1,
                    "superan_30": 1,
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
                    },
                    "esfuerzo_medio": {
                        "$round": ["$esfuerzo_medio", 2]
                    }
                }
            },
            {"$sort": {"esfuerzo_medio": -1}}
        ]

        print("\n=== ESFUERZO DE ALQUILER POR PROVINCIA ===")

        for resultado in db[COLLECTIONS["municipios"]].aggregate(pipeline):
            print(resultado)

    except PyMongoError as e:
        print(f"ERROR de MongoDB: {e}")

    finally:
        cerrar_conexion()


if __name__ == "__main__":
    analizar_esfuerzo()
