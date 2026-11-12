
from pymongo import MongoClient

# ==========================================
# CONFIGURACIÓN
# ==========================================

URI = "mongodb://localhost:27017/"
DB_NAME = "EUSKADI_VIVIENDA_BIGDATA_TEST"

# Protección: trabajar únicamente en TEST
if DB_NAME != "EUSKADI_VIVIENDA_BIGDATA_TEST":
    raise RuntimeError("Solo se permite trabajar en TEST")

client = MongoClient(URI, serverSelectionTimeoutMS=5000)
client.admin.command("ping")

db = client[DB_NAME]
coleccion = db["pruebas_crud_ra3"]

print("=== RA3 - CRUD CON PYMONGO ===")
print("Base de datos:", DB_NAME)

# ==========================================
# 1. CREATE - INSERTAR DOCUMENTO
# ==========================================

documento = {
    "_id": "RA3_PRUEBA_001",
    "municipio": "Bilbao",
    "precio": 180000,
    "operacion": "venta",
    "tipo": "PRUEBA_RA3"
}

print("\n=== CREATE ===")

existente = coleccion.find_one({"_id": documento["_id"]})

if existente is None:
    resultado = coleccion.insert_one(documento)
    print("ID insertado:", resultado.inserted_id)
else:
    print("El documento de prueba ya existe. No se inserta de nuevo.")

# Verificar la inserción
guardado = coleccion.find_one({"_id": documento["_id"]})
print("Documento guardado:", guardado)

# ==========================================
# 2. READ - CONSULTAR DOCUMENTO
# ==========================================

print("\n=== READ ===")

consulta = coleccion.find_one({
    "_id": "RA3_PRUEBA_001"
})

print("Documento encontrado:", consulta)


# ==========================================
# 3. UPDATE - ACTUALIZAR DOCUMENTO
# ==========================================

print("\n=== UPDATE ===")

resultado = coleccion.update_one(
    {"_id": "RA3_PRUEBA_001"},
    {"$set": {"precio": 195000}}
)

print("Documentos encontrados:", resultado.matched_count)
print("Documentos modificados:", resultado.modified_count)

# Verificar la actualización
actualizado = coleccion.find_one({
    "_id": "RA3_PRUEBA_001"
})

print("Documento actualizado:", actualizado)

assert actualizado is not None
assert actualizado["precio"] == 195000
print("Verificación UPDATE: correcta")

# ==========================================
# 4. DELETE - ELIMINAR DOCUMENTO
# ==========================================

print("\n=== DELETE ===")

resultado = coleccion.delete_one({
    "_id": "RA3_PRUEBA_001",
    "tipo": "PRUEBA_RA3"
})

print("Documentos eliminados:", resultado.deleted_count)

# Verificar la eliminación
eliminado = coleccion.find_one({
    "_id": "RA3_PRUEBA_001"
})

print("Documento después de DELETE:", eliminado)

assert resultado.deleted_count == 1
assert eliminado is None

print("Verificación DELETE: correcta")

# ==========================================
# CERRAR CONEXIÓN
# ==========================================

client.close()
