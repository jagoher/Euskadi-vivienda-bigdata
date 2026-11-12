
import json
import sys

from pymongo import UpdateOne
from pymongo.errors import (
    BulkWriteError,
    PyMongoError
)

from database import conectar, cerrar_conexion
from config import MONGODB_DIR, COLLECTIONS


ARCHIVO = MONGODB_DIR / "municipios_mongodb.json"


def importar_municipios():

    print("\n=== IMPORTACION DE MUNICIPIOS ===")

    # 1. Lectura del archivo
    try:
        with open(ARCHIVO, "r", encoding="utf-8") as f:
            municipios = json.load(f)

    except FileNotFoundError:
        print(f"ERROR: No existe el archivo: {ARCHIVO}")
        return False

    except PermissionError:
        print("ERROR: Sin permisos para leer el archivo.")
        return False

    except json.JSONDecodeError as e:
        print(f"ERROR: JSON incorrecto: {e}")
        return False

    except OSError as e:
        print(f"ERROR de lectura: {e}")
        return False

    # 2. Validación de estructura
    if not isinstance(municipios, list) or not municipios:
        print("ERROR: Se esperaba una lista no vacía.")
        return False

    ids = []

    for numero, municipio in enumerate(municipios, start=1):

        if not isinstance(municipio, dict):
            print(f"ERROR: Documento {numero} no es un objeto.")
            return False

        codigo = municipio.get("_id")

        if (
            not isinstance(codigo, str)
            or len(codigo) != 5
            or not codigo.isdigit()
        ):
            print(f"ERROR: Código INE inválido en documento {numero}.")
            return False

        if not isinstance(municipio.get("vivienda"), dict):
            print(f"ERROR: Falta vivienda en documento {numero}.")
            return False

        if not isinstance(municipio.get("indicadores"), dict):
            print(f"ERROR: Faltan indicadores en documento {numero}.")
            return False

        ids.append(codigo)

    if len(ids) != len(set(ids)):
        print("ERROR: Existen identificadores duplicados.")
        return False

    print(f"JSON validado: {len(municipios)} municipios.")

    # 3. Conexión con MongoDB
    db = None

    try:
        db = conectar()

        if db is None:
            print("ERROR: No se pudo conectar con MongoDB.")
            return False

        coleccion = db[COLLECTIONS["municipios"]]

        # 4. Preparar operaciones repetibles
        operaciones = [
            UpdateOne(
                {"_id": municipio["_id"]},
                {
                    "$set": {
                        clave: valor
                        for clave, valor in municipio.items()
                        if clave != "_id"
                    }
                },
                upsert=True
            )
            for municipio in municipios
        ]

        # 5. Importación
        resultado = coleccion.bulk_write(
            operaciones,
            ordered=True
        )

        total = coleccion.count_documents({})

        print("\n=== RESULTADO ===")
        print("Procesados:", len(municipios))
        print("Insertados:", resultado.upserted_count)
        print("Actualizados:", resultado.modified_count)
        print("Sin cambios:", resultado.matched_count - resultado.modified_count)
        print("Total en colección:", total)

        print("\nImportación finalizada correctamente.")
        return True

    except BulkWriteError as e:
        print("\nERROR durante la importación masiva.")

        for error in e.details.get("writeErrors", [])[:5]:
            print(
                f"Operación {error.get('index')}: "
                f"{error.get('errmsg')}"
            )

        print("ATENCIÓN: Algunos documentos pueden haberse guardado.")
        return False

    except PyMongoError as e:
        print(f"\nERROR de MongoDB: {e}")
        print("ATENCIÓN: Comprueba si hubo escrituras parciales.")
        return False

    except (KeyError, TypeError, ValueError) as e:
        print(f"\nERROR de configuración o datos: {e}")
        return False

    finally:
        cerrar_conexion()


if __name__ == "__main__":
    correcto = importar_municipios()
    sys.exit(0 if correcto else 1)

