
import json
import sys

from pymongo import UpdateOne
from pymongo.errors import BulkWriteError, PyMongoError

from config import MONGODB_DIR, COLLECTIONS
from database import conectar, cerrar_conexion


ARCHIVO = MONGODB_DIR / "compraventa_euskadi_clasificado_v3.json"


def importar_anuncios():
    print("\n=== IMPORTACION DE ANUNCIOS ===")

    try:
        with open(ARCHIVO, encoding="utf-8") as f:
            anuncios = json.load(f)

    except (FileNotFoundError, PermissionError, OSError) as e:
        print(f"ERROR al leer el archivo: {e}")
        return False

    except json.JSONDecodeError as e:
        print(f"ERROR: JSON incorrecto: {e}")
        return False

    if not isinstance(anuncios, list) or not anuncios:
        print("ERROR: Se esperaba una lista no vacía.")
        return False

    ids = set()
    municipios = set()
    operaciones = []

    for numero, anuncio in enumerate(anuncios, start=1):

        if not isinstance(anuncio, dict):
            print(f"ERROR: Anuncio {numero} no es un objeto.")
            return False

        identificador = anuncio.get("id_portal")
        municipio_id = anuncio.get("municipio_id")
        precio = anuncio.get("precio")

        if not isinstance(identificador, str) or not identificador:
            print(f"ERROR: ID inválido en anuncio {numero}.")
            return False

        if identificador in ids:
            print(f"ERROR: ID duplicado: {identificador}")
            return False

        if (
            not isinstance(municipio_id, str)
            or len(municipio_id) != 5
            or not municipio_id.isdigit()
        ):
            print(f"ERROR: Código INE inválido en anuncio {numero}.")
            return False

        if (
            isinstance(precio, bool)
            or not isinstance(precio, (int, float))
            or precio <= 0
        ):
            print(f"ERROR: Precio inválido en anuncio {numero}.")
            return False

        ids.add(identificador)
        municipios.add(municipio_id)

        documento = {
            "_id": identificador,
            **{
                clave: valor
                for clave, valor in anuncio.items()
                if clave not in ("_id", "id_portal")
            },
            "id_portal": identificador
        }

        operaciones.append(
            UpdateOne(
                {"_id": identificador},
                {"$set": {
                    k: v for k, v in documento.items()
                    if k != "_id"
                }},
                upsert=True
            )
        )

    print("Anuncios validados:", len(anuncios))
    print("Municipios diferentes:", len(municipios))

    try:
        db = conectar()

        if db is None:
            print("ERROR: No se pudo conectar con MongoDB.")
            return False

        coleccion_municipios = db[COLLECTIONS["municipios"]]
        ids_municipios = set(
            coleccion_municipios.distinct("_id")
        )

        desconocidos = municipios - ids_municipios

        if desconocidos:
            print(
                "ERROR: Códigos INE sin municipio:",
                sorted(desconocidos)
            )
            return False

        coleccion = db[COLLECTIONS["anuncios"]]

        resultado = coleccion.bulk_write(
            operaciones,
            ordered=True
        )

        print("\n=== RESULTADO ===")
        print("Procesados:", len(anuncios))
        print("Insertados:", resultado.upserted_count)
        print("Actualizados:", resultado.modified_count)
        print(
            "Sin cambios:",
            resultado.matched_count - resultado.modified_count
        )
        print("Total en MongoDB:", coleccion.count_documents({}))

        print("\nImportación finalizada correctamente.")
        return True

    except BulkWriteError as e:
        print(f"ERROR de importación masiva: {e.details}")
        print("ATENCIÓN: Puede haber escrituras parciales.")
        return False

    except PyMongoError as e:
        print(f"ERROR de MongoDB: {e}")
        print("ATENCIÓN: Comprueba posibles escrituras parciales.")
        return False

    except (KeyError, TypeError, ValueError) as e:
        print(f"ERROR de configuración o datos: {e}")
        return False

    finally:
        cerrar_conexion()


if __name__ == "__main__":
    correcto = importar_anuncios()
    sys.exit(0 if correcto else 1)
