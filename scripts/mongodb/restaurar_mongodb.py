
from pathlib import Path
from pymongo import MongoClient
from bson import json_util

BASE = Path(__file__).resolve().parents[2]
BACKUP = BASE / "backup_mongodb"

# Base de pruebas: NO modifica la original
DB_DESTINO = "EUSKADI_VIVIENDA_BIGDATA_TEST"

COLECCIONES = [
    "municipios",
    "anuncios",
    "mercado_alquiler",
    "salarios",
    "economia_juvenil"
]


def restaurar():
    cliente = MongoClient(
        "mongodb://localhost:27017/",
        serverSelectionTimeoutMS=3000
    )

    try:
        cliente.admin.command("ping")
        db = cliente[DB_DESTINO]

        # Evitar sobrescribir una base existente
        existentes = set(db.list_collection_names())
        if existentes:
            print("ERROR: La base de pruebas ya contiene colecciones.")
            print("No se ha modificado ningún dato.")
            return

        # Validar todos los archivos antes de escribir
        datos = {}

        for nombre in COLECCIONES:
            ruta = BACKUP / f"{nombre}.json"

            if not ruta.is_file():
                print(f"ERROR: Falta {ruta}")
                return

            documentos = json_util.loads(
                ruta.read_text(encoding="utf-8")
            )

            if not isinstance(documentos, list):
                print(f"ERROR: Formato incorrecto en {nombre}")
                return

            datos[nombre] = documentos

        # Restaurar documentos
        for nombre, documentos in datos.items():
            coleccion = db[nombre]

            if documentos:
                coleccion.insert_many(documentos)
            else:
                db.create_collection(nombre)

            print(
                f"{nombre}: "
                f"{coleccion.count_documents({})} documentos"
            )

        # Recuperar índices secundarios
        ruta_metadata = BACKUP / "metadata.json"

        if ruta_metadata.is_file():
            metadata = json_util.loads(
                ruta_metadata.read_text(encoding="utf-8")
            )

            for nombre in COLECCIONES:
                indices = metadata["colecciones"][nombre]["indices"]

                for indice in indices:
                    if indice["name"] == "_id_":
                        continue

                    opciones = {
                        k: v for k, v in indice.items()
                        if k not in ("v", "key", "ns")
                    }

                    db[nombre].create_index(
                        list(indice["key"].items()),
                        **opciones
                    )

        total = sum(
            db[n].count_documents({}) for n in COLECCIONES
        )

        print("\nRESTAURACION COMPLETADA")
        print("Base de datos:", DB_DESTINO)
        print("Total documentos:", total)

    finally:
        cliente.close()


if __name__ == "__main__":
    restaurar()
