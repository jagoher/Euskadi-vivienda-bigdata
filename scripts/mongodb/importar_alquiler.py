
import json
import sys

from pymongo import UpdateOne
from pymongo.errors import BulkWriteError, PyMongoError

from config import MONGODB_DIR, COLLECTIONS
from database import conectar, cerrar_conexion


ARCHIVO = MONGODB_DIR / "alquiler_euskadi_provincias.json"


def importar_alquiler():

    print("\n=== IMPORTACION MERCADO DE ALQUILER ===")

    # 1. Leer JSON
    try:
        with open(ARCHIVO, encoding="utf-8") as f:
            datos = json.load(f)

    except (OSError, UnicodeError) as e:
        print(f"ERROR al leer archivo: {e}")
        return False

    except json.JSONDecodeError as e:
        print(f"ERROR: JSON incorrecto: {e}")
        return False

    # 2. Validar estructura principal
    if (
        not isinstance(datos, list)
        or len(datos) != 1
        or not isinstance(datos[0], dict)
    ):
        print("ERROR: Estructura principal incorrecta.")
        return False

    provincias = datos[0].get("provincias")

    if not isinstance(provincias, list) or not provincias:
        print("ERROR: No hay provincias válidas.")
        return False

    operaciones = []
    ids = set()
    total_trimestres = 0

    # 3. Validar provincias y series
    for provincia in provincias:

        if not isinstance(provincia, dict):
            print("ERROR: Provincia incorrecta.")
            return False

        codigo = provincia.get("territorio_id")
        nombre = provincia.get("nombre")
        serie = provincia.get("serie")

        if (
            not isinstance(codigo, str)
            or len(codigo) != 2
            or not codigo.isdigit()
            or not isinstance(nombre, str)
            or not nombre.strip()
            or not isinstance(serie, list)
            or not serie
        ):
            print(f"ERROR: Provincia inválida: {nombre}")
            return False

        if codigo in ids:
            print(f"ERROR: Provincia duplicada: {codigo}")
            return False

        ids.add(codigo)
        periodos = set()

        for registro in serie:

            if not isinstance(registro, dict):
                print(f"ERROR: Registro incorrecto en {nombre}")
                return False

            anyo = registro.get("anyo")
            trimestre = registro.get("trimestre")

            if (
                type(anyo) is not int
                or type(trimestre) is not int
                or trimestre not in (1, 2, 3, 4)
            ):
                print(f"ERROR: Periodo inválido en {nombre}")
                return False

            periodo = (anyo, trimestre)

            if periodo in periodos:
                print(f"ERROR: Trimestre duplicado: {nombre} {periodo}")
                return False

            periodos.add(periodo)

            for campo in ("presion", "oferta", "precio"):
                valor = registro.get(campo)

                # Se permiten nulos en la fuente original
                if valor is not None and (
                    isinstance(valor, bool)
                    or not isinstance(valor, (int, float))
                    or valor < 0
                ):
                    print(f"ERROR: {campo} inválido en {nombre}")
                    return False

        total_trimestres += len(serie)

        operaciones.append(
            UpdateOne(
                {"_id": codigo},
                {
                    "$set": {
                        "territorio_id": codigo,
                        "nombre": nombre,
                        "serie": serie,
                        "fuente": datos[0].get("fuente")
                    }
                },
                upsert=True
            )
        )

    print("Provincias validadas:", len(provincias))
    print("Registros trimestrales:", total_trimestres)

    # 4. Importar a MongoDB
    try:
        db = conectar()

        if db is None:
            print("ERROR: No se pudo conectar.")
            return False

        coleccion = db[COLLECTIONS["alquiler"]]

        resultado = coleccion.bulk_write(
            operaciones,
            ordered=True
        )

        print("\n=== RESULTADO ===")
        print("Procesados:", len(provincias))
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
        return False

    except (KeyError, TypeError, ValueError) as e:
        print(f"ERROR de configuración o datos: {e}")
        return False

    finally:
        cerrar_conexion()


if __name__ == "__main__":
    correcto = importar_alquiler()
    sys.exit(0 if correcto else 1)
