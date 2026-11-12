
from pymongo import MongoClient

URI = "mongodb://localhost:27017/"
DB_NAME = "EUSKADI_VIVIENDA_BIGDATA_TEST"


def limpiar_datos():
    if DB_NAME != "EUSKADI_VIVIENDA_BIGDATA_TEST":
        raise RuntimeError("Solo se permite trabajar en TEST")

    with MongoClient(URI, serverSelectionTimeoutMS=5000) as client:
        client.admin.command("ping")
        db = client[DB_NAME]
        anuncios = db["anuncios"]

        total = anuncios.count_documents({})
        print("=== LIMPIEZA RA1 ===")
        print("Base:", DB_NAME)
        print("Anuncios iniciales:", total)

        if total != 2952:
            raise RuntimeError("Cantidad inesperada de anuncios")

        # 1. NULOS: normalizar campos opcionales.
        # No sustituimos los datos originales.
        r1 = anuncios.update_many(
            {},
            [{
                "$set": {
                    "limpieza.zona_normalizada": {
                        "$ifNull": ["$zona", "Sin especificar"]
                    },
                    "limpieza.descripcion_disponible": {
                        "$and": [
                            {"$eq": [{"$type": "$descripcion"}, "string"]},
                            {"$ne": ["$descripcion", ""]}
                        ]
                    },
                    "limpieza.superficie_disponible": {
                        "$and": [
                            {"$isNumber": "$caracteristicas.m2"},
                            {"$gt": ["$caracteristicas.m2", 0]}
                        ]
                    }
                }
            }]
        )
        print("1. Nulos - modificados:", r1.modified_count)

        # 2. DUPLICADOS: marcar registros para revisión.
        # No se borra ningún anuncio.
        r2 = anuncios.update_many(
            {},
            [{
                "$set": {
                    "limpieza.revisar_duplicado": {
                        "$eq": [
                            "$calidad.posible_duplicado_ampliado",
                            True
                        ]
                    },
                    "limpieza.grupo_revision": {
                        "$ifNull": [
                            "$calidad.grupo_duplicado",
                            None
                        ]
                    }
                }
            }]
        )
        print("2. Duplicados - modificados:", r2.modified_count)

        # 3. FORMATOS: normalizar identificadores y nombres.
        # Se conservan los campos originales.
        r3 = anuncios.update_many(
            {},
            [{
                "$set": {
                    "limpieza.municipio_id_normalizado": {
                        "$toString": "$municipio_id"
                    },
                    "limpieza.municipio_normalizado": {
                        "$trim": {
                            "input": {
                                "$ifNull": ["$municipio", ""]
                            }
                        }
                    }
                }
            }]
        )
        print("3. Formatos - modificados:", r3.modified_count)

        # 4. TRANSFORMACION: calcular precio por m2.
        # Si la superficie no es valida, queda en null.
        r4 = anuncios.update_many(
            {},
            [{
                "$set": {
                    "limpieza.precio_m2": {
                        "$cond": [
                            {
                                "$and": [
                                    {"$isNumber": "$precio"},
                                    {"$isNumber": "$caracteristicas.m2"},
                                    {"$gt": ["$caracteristicas.m2", 0]}
                                ]
                            },
                            {
                                "$round": [
                                    {
                                        "$divide": [
                                            "$precio",
                                            "$caracteristicas.m2"
                                        ]
                                    },
                                    2
                                ]
                            },
                            None
                        ]
                    }
                }
            }]
        )
        print("4. Precio/m2 - modificados:", r4.modified_count)

        print("\n=== VERIFICACION ===")
        print("Anuncios finales:", anuncios.count_documents({}))
        print(
            "Zonas normalizadas:",
            anuncios.count_documents({
                "limpieza.zona_normalizada": "Sin especificar"
            })
        )
        print(
            "Duplicados para revisar:",
            anuncios.count_documents({
                "limpieza.revisar_duplicado": True
            })
        )
        print(
            "Precios/m2 calculados:",
            anuncios.count_documents({
                "limpieza.precio_m2": {"$type": "number"}
            })
        )
        print(
            "Precios/m2 no disponibles:",
            anuncios.count_documents({
                "limpieza.precio_m2": None
            })
        )

        ejemplo = anuncios.find_one(
            {"limpieza.precio_m2": {"$type": "number"}},
            {
                "_id": 0,
                "municipio": 1,
                "precio": 1,
                "caracteristicas.m2": 1,
                "limpieza": 1
            }
        )
        print("\nEjemplo:", ejemplo)


if __name__ == "__main__":
    limpiar_datos()
