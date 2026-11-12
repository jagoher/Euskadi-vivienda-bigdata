from pymongo import MongoClient
from pymongo.errors import (
    ServerSelectionTimeoutError,
    ConnectionFailure,
    ConfigurationError,
    PyMongoError
)

from config import MONGODB_URI, DATABASE_NAME


# --------------------------------------------------
# CONEXIÓN MONGODB
# --------------------------------------------------

client = None
db = None


def conectar():
    """
    Establece la conexión con MongoDB y comprueba
    que el servidor está disponible.
    """

    global client, db

    try:
        client = MongoClient(
            MONGODB_URI,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=5000
        )

        # Comprobación real de conexión
        client.admin.command("ping")

        # Seleccionar base de datos
        db = client[DATABASE_NAME]

        print("Conexión correcta con MongoDB.")
        print(f"Base de datos: {db.name}")

        return db

    except ServerSelectionTimeoutError:
        print("Error: no se encuentra el servidor MongoDB.")

    except ConnectionFailure:
        print("Error: no se ha podido establecer la conexión.")

    except ConfigurationError as e:
        print(f"Error de configuración: {e}")

    except PyMongoError as e:
        print(f"Error de MongoDB: {e}")

    except Exception as e:
        print(f"Error inesperado: {e}")

    cerrar_conexion()
    return None


def get_database():
    """
    Devuelve la base de datos.
    Si no existe conexión, intenta establecerla.
    """

    global db

    if db is None:
        return conectar()

    return db


def comprobar_conexion():
    """
    Comprueba si MongoDB sigue respondiendo.
    """

    try:
        if client is None:
            return False

        client.admin.command("ping")
        return True

    except PyMongoError as e:
        print(f"Error al comprobar la conexión: {e}")
        return False


def cerrar_conexion():
    """
    Cierra la conexión con MongoDB de forma segura.
    """

    global client, db

    if client is not None:
        client.close()

        client = None
        db = None

        print("Conexión cerrada.")
