
import json
import math
import sys

from pymongo import UpdateOne
from pymongo.errors import BulkWriteError, PyMongoError

from config import MONGODB_DIR, COLLECTIONS
from database import conectar, cerrar_conexion


ARCHIVO = MONGODB_DIR / "salarios_juveniles_euskadi.json"


def importar_salarios():

    print("\n=== IMPORTACION SALARIOS JUVENILES ===")

    # 1. Leer archivo
    try:
        with open(ARCHIVO, encoding="utf-8") as f:
            salarios = json.load(f)

    except json.JSONDecodeError as e:
        print(f"ERROR: JSON incorrecto: {e}")
        return False

    except (OSError, UnicodeError) as e:
        print(f"ERROR de lectura: {e}")
        return False

    # 2. Validar estructura
    if not isinstance(salarios, list) or not salarios:
        print("ERROR: Se esperaba una lista no vacía.")
        return False

    operaciones = []
    ids = set()
    dimensiones = set()

    for numero, registro in enumerate(salarios, start=1):

        if not isinstance(registro, dict):
            print(f"ERROR: Registro {numero} incorrecto.")
            return False

        anyo = registro.get("anyo")
        dimension = registro.get("dimension")
        categoria = registro.get("categoria")
        salario = registro.get("salario_neto_mensual")

        if type(anyo) is not int or not 1900 <= anyo <= 2100:
            print(f"ERROR: Año inválido en registro {numero}.")
            return False

        if dimension not in ("edad", "sexo", "territorio"):
            print(f"ERROR: Dimensión inválida en registro {numero}.")
            return False

        if not isinstance(categoria, str) or not categoria.strip():
            print(f"ERROR: Categoría inválida en registro {numero}.")
            return False

        # Se permiten salarios nulos si la fuente no aporta el dato.
        if salario is not None and (
            isinstance(salario, bool)
            or not isinstance(salario, (int, float))
            or not math.isfinite(salario)
            or salario < 0
        ):
            print(f"ERROR: Salario inválido en registro {numero}.")
            return False

        identificador = f"{anyo}|{dimension}|{categoria}"

        if identificador in ids:
            print(f"ERROR: Registro duplicado: {identificador}")
            return False

        ids.add(identificador)
        dimensiones.add(dimension)

        operaciones.append(
            UpdateOne(
                {"_id": identificador},
                {
                    "$set": {
                        "anyo": anyo,
                        "dimension": dimension,
                        "categoria": categoria,
                        "salario_neto_mensual": salario
                    }
                },
                upsert=True
            )
        )

    print("Registros validados:", len(salarios))
    print("Dimensiones:", ", ".join(sorted(dimensiones)))

    # 3. Importar a MongoDB
    try:
        db = conectar()

        if db is None:
            print("ERROR: No se pudo conectar con MongoDB.")
            return False

        coleccion = db[COLLECTIONS["salarios"]]

        resultado = coleccion.bulk_write(
            operaciones,
            ordered=True
        )

        print("\n=== RESULTADO ===")
        print("Procesados:", len(salarios))
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
        print("ERROR durante la importación masiva.")
        for error in e.details.get("writeErrors", [])[:5]:
            print(error.get("errmsg"))
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
    correcto = importar_salarios()
    sys.exit(0 if correcto else 1)
