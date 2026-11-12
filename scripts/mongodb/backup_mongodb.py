
from pathlib import Path
from datetime import datetime
import json
import sys

from pymongo import MongoClient
from bson import json_util

BASE = Path(__file__).resolve().parents[2]
DESTINO = BASE / "backup_mongodb"
DB_NAME = "EUSKADI_VIVIENDA_BIGDATA"

COLECCIONES = [
    "municipios",
    "anuncios",
    "mercado_alquiler",
    "salarios",
    "economia_juvenil"
]

def main():
    DESTINO.mkdir(exist_ok=True)

    cliente = MongoClient(
        "mongodb://localhost:27017/",
        serverSelectionTimeoutMS=3000
    )

    try:
        cliente.admin.command("ping")
        db = cliente[DB_NAME]
        resumen = {}

        for nombre in COLECCIONES:
            coleccion = db[nombre]
            ruta = DESTINO / f"{nombre}.json"

            documentos = list(coleccion.find({}))

            with ruta.open("w", encoding="utf-8") as f:
                f.write(json_util.dumps(
                    documentos,
                    ensure_ascii=False,
                    indent=2
                ))

            resumen[nombre] = {
                "documentos": len(documentos),
                "indices": list(coleccion.list_indexes())
            }

            print(f"{nombre}: {len(documentos)} documentos")

        metadata = {
            "base_datos": DB_NAME,
            "fecha": datetime.now().isoformat(),
            "colecciones": resumen
        }

        with (DESTINO / "metadata.json").open(
            "w", encoding="utf-8"
        ) as f:
            f.write(json_util.dumps(
                metadata,
                ensure_ascii=False,
                indent=2
            ))

        print("\nBACKUP COMPLETADO")
        print("Carpeta:", DESTINO)
        print("Total:", sum(
            x["documentos"] for x in resumen.values()
        ))

    finally:
        cliente.close()

if __name__ == "__main__":
    main()
