
import json
import math
import sys

from pymongo import UpdateOne
from pymongo.errors import BulkWriteError, PyMongoError

from config import MONGODB_DIR, COLLECTIONS
from database import conectar, cerrar_conexion


ARCHIVO = MONGODB_DIR / "economia_juvenil_euskadi.json"


def importar_economia():

    print("\n=== IMPORTACION ECONOMIA JUVENIL ===")

    # 1. Leer JSON
    try:
        with open(ARCHIVO, encoding="utf-8") as f:
            registros = json.load(f)

    except json.JSONDecodeError as e:
        print(f"ERROR: JSON incorrecto: {e}")
        return False

    except (OSError, UnicodeError) as e:
        print(f"ERROR de lectura: {e}")
        return False

    # 2. Validar estructura
    if not isinstance(registros, list) or not registros:
        print("ERROR: Se esperaba una lista no vacía.")
        return False

    ids = set()
    indicadores = set()
    operaciones = []

    for numero, registro in enumerate(registros, start=1):

        if not isinstance(registro, dict):
            print(f"ERROR: Registro {numero} incorrecto.")
            return False

        anyo = registro.get("anyo")
        indicador = registro.get("indicador")
        categoria = registro.get("categoria")
        valor = registro.get("valor")
        unidad = registro.get("unidad")

        if type(anyo) is not int or not 1900 <= anyo <= 2100:
            print(f"ERROR: Año inválido en registro {numero}.")
            return False

        if not isinstance(indicador, str) or not indicador.strip():
            print(f"ERROR: Indicador inválido en registro {numero}.")
            return False

        if not isinstance(categoria, str) or not categoria.strip():
            print(f"ERROR: Categoría inválida en registro {numero}.")
            return False

        if not isinstance(unidad, str) or not unidad.strip():
            print(f"ERROR: Unidad inválida en registro {numero}.")
            return False

        # Se permiten valores nulos en la fuente.
        if valor is not None:
            if (
                isinstance(valor, bool)
                or not isinstance(valor, (int, float))
                or not math.isfinite(valor)
                or valor < 0
            ):
                print(f"ERROR: Valor inválido en registro {numero}.")
                return False

            if unidad == "porcentaje" and valor > 100:
                print(f"ERROR: Porcentaje superior a 100 en registro {numero}.")
                return False

        identificador = f"{anyo}|{indicador}|{categoria}"

        if identificador in ids:
            print(f"ERROR: Registro duplicado: {identificador}")
            return False

        ids.add(identificador)
        indicadores.add(indicador)

        operaciones.append(
            UpdateOne(
                {"_id": identificador},
                {
                    "$set": {
                        "anyo": anyo,
                        "indicador": indicador,
                        "categoria": categoria,
                        "valor": valor,
                        "unidad": unidad
                    }
                },
                upsert=True
            )
        )

    print("Registros validados:", len(registros))
    print("Indicadores:", ", ".join(sorted(indicadores)))

    # 3. Importar en MongoDB
    try:
        db = conectar()

        if db is None:
            print("ERROR: No se pudo conectar con MongoDB.")
            return False

        coleccion = db[COLLECTIONS["economia"]]

        resultado = coleccion.bulk_write(
            operaciones,
            ordered=True
        )

        print("\n=== RESULTADO ===")
        print("Procesados:", len(registros))
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
    correcto = importar_economia()
    sys.exit(0 if correcto else 1)
