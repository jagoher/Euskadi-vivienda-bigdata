
from pymongo import MongoClient, ReturnDocument
from pymongo.errors import PyMongoError

# ==========================================
# 1. CONFIGURACION
# ==========================================

URI = "mongodb://localhost:27017/"
DB_NAME = "EUSKADI_VIVIENDA_BIGDATA_TEST"

# Proteccion: trabajar exclusivamente en TEST
if DB_NAME != "EUSKADI_VIVIENDA_BIGDATA_TEST":
    raise RuntimeError("Solo se permite trabajar en TEST")

COLECCION = "pruebas_atomicas_ra3"
ID_PRUEBA = "RA3_ATOMICA_001"

client = None
coleccion = None

try:

    # ==========================================
    # 2. CONEXION
    # ==========================================

    client = MongoClient(
        URI,
        serverSelectionTimeoutMS=5000
    )

    client.admin.command("ping")

    db = client[DB_NAME]
    coleccion = db[COLECCION]

    print("==========================================")
    print("RA3 - PRUEBA DE ATOMICIDAD EN MONGODB")
    print("==========================================")
    print("Base de datos:", DB_NAME)
    print("Coleccion:", COLECCION)

    # ==========================================
    # 3. JUSTIFICACION TECNICA
    # ==========================================

    print("\n=== JUSTIFICACION ===")

    print("El modelo utiliza documentos independientes.")
    print("Los anuncios y municipios se relacionan")
    print("mediante referencias utilizando el codigo INE.")
    print("La operacion de esta prueba modifica un unico documento.")
    print("MongoDB garantiza atomicidad a nivel de documento.")
    print("No se necesita una transaccion multidocumento.")

    # ==========================================
    # 4. CREAR DOCUMENTO DE PRUEBA
    # ==========================================

    # Inicializamos siempre el documento a cero
    # para que la prueba sea reproducible.

    coleccion.replace_one(
        {"_id": ID_PRUEBA},
        {
            "_id": ID_PRUEBA,
            "tipo": "PRUEBA_RA3",
            "contador": 0
        },
        upsert=True
    )

    print("\n=== ANTES DE LA OPERACION ===")

    inicial = coleccion.find_one({
        "_id": ID_PRUEBA
    })

    print(inicial)

    assert inicial is not None
    assert inicial["contador"] == 0

    # ==========================================
    # 5. OPERACION ATOMICA
    # ==========================================

    print("\n=== EJECUTANDO OPERACION ATOMICA ===")

    resultado = coleccion.find_one_and_update(
        {
            "_id": ID_PRUEBA,
            "tipo": "PRUEBA_RA3"
        },
        {
            "$inc": {
                "contador": 1
            }
        },
        return_document=ReturnDocument.AFTER
    )

    # ==========================================
    # 6. VERIFICAR RESULTADO
    # ==========================================

    print("\n=== DESPUES DE LA OPERACION ATOMICA ===")

    print(resultado)

    assert resultado is not None
    assert resultado["contador"] == 1

    print("\nVERIFICACION DE ATOMICIDAD: CORRECTA")
    print("Contador inicial: 0")
    print("Contador final: 1")
    print("Documento actualizado de forma atomica.")

    # ==========================================
    # 7. VERIFICACION EN MONGODB
    # ==========================================

    verificacion = coleccion.find_one({
        "_id": ID_PRUEBA
    })

    assert verificacion is not None
    assert verificacion["contador"] == 1

    print("\nVERIFICACION EN BASE DE DATOS: CORRECTA")

    # ==========================================
    # 8. LIMPIEZA
    # ==========================================

    eliminacion = coleccion.delete_one({
        "_id": ID_PRUEBA,
        "tipo": "PRUEBA_RA3"
    })

    print("\n=== LIMPIEZA ===")
    print("Documentos eliminados:", eliminacion.deleted_count)

    assert eliminacion.deleted_count == 1

    restante = coleccion.find_one({
        "_id": ID_PRUEBA
    })

    assert restante is None

    print("Documento de prueba eliminado correctamente.")

    # ==========================================
    # 9. RESULTADO FINAL
    # ==========================================

    print("\n==========================================")
    print("RESULTADO FINAL")
    print("==========================================")
    print("Conexion: CORRECTA")
    print("Operacion atomica: CORRECTA")
    print("Incremento del contador: CORRECTO")
    print("Verificacion: CORRECTA")
    print("Limpieza: CORRECTA")
    print("\nPRUEBA RA3 SUPERADA")

except PyMongoError as error:

    print("\nERROR DE MONGODB:")
    print(error)

except (AssertionError, KeyError) as error:

    print("\nERROR EN LA VERIFICACION:")
    print(error)

finally:

    if client is not None:
        client.close()
        print("\nConexion MongoDB cerrada.")
