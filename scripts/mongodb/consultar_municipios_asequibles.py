
import os
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.errors import PyMongoError

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI")
DATABASE_NAME = os.getenv("DATABASE_NAME")

client = None

try:
    # Comprobar variables de entorno
    if not MONGODB_URI or not DATABASE_NAME:
        raise ValueError("Faltan variables en el archivo .env")

    # Conexión
    client = MongoClient(
        MONGODB_URI,
        serverSelectionTimeoutMS=5000
    )

    client.admin.command("ping")

    db = client[DATABASE_NAME]

    if "municipios" not in db.list_collection_names():
        raise ValueError("La colección municipios no existe")

    coleccion = db["municipios"]

    # Consulta
    filtro = {
        "indicadores.esfuerzo_alquiler_pct": {
            "$type": "number",
            "$lte": 30
        }
    }

    proyeccion = {
        "_id": 0,
        "nombre": 1,
        "indicadores.esfuerzo_alquiler_pct": 1
    }

    resultados = list(
        coleccion.find(filtro, proyeccion)
        .sort("indicadores.esfuerzo_alquiler_pct", 1)
    )

    # Mostrar resultados
    print("\nMUNICIPIOS CON ESFUERZO DE ALQUILER <= 30 %")
    print("-" * 65)

    if not resultados:
        print("No se encontraron municipios.")

    for municipio in resultados:
        nombre = municipio.get("nombre", "Desconocido")
        esfuerzo = municipio.get(
            "indicadores", {}
        ).get("esfuerzo_alquiler_pct")

        if esfuerzo is None:
            continue

        print(f"{nombre:<45} {esfuerzo:>6.2f} %")

    print("-" * 65)
    print(f"Total: {len(resultados)} municipios")

except (PyMongoError, ValueError) as error:
    print(f"ERROR: {error}")

finally:
    if client is not None:
        client.close()
