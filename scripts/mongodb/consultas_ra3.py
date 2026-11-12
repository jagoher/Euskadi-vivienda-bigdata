
from pymongo import MongoClient

# ==========================================
# CONFIGURACIÓN
# ==========================================

URI = "mongodb://localhost:27017/"
DB_NAME = "EUSKADI_VIVIENDA_BIGDATA_TEST"

if DB_NAME != "EUSKADI_VIVIENDA_BIGDATA_TEST":
    raise RuntimeError("Solo se permite trabajar en TEST")

client = MongoClient(URI, serverSelectionTimeoutMS=5000)
client.admin.command("ping")

db = client[DB_NAME]
anuncios = db["anuncios"]

# ==========================================
# CONSULTA 1 - VIVIENDAS EN VENTA <= 200.000 €
# ==========================================

print("\n=== CONSULTA 1: VIVIENDAS EN VENTA <= 200.000 € ===")

filtro = {
    "operacion": "venta",
    "precio": {"$lte": 200000}
}

total = anuncios.count_documents(filtro)

print("Total de anuncios encontrados:", total)

resultados = anuncios.find(
    filtro,
    {
        "_id": 0,
        "municipio": 1,
        "precio": 1,
        "caracteristicas.m2": 1
    }
).sort("precio", 1).limit(10)

for anuncio in resultados:
    print(anuncio)

# ==========================================
# CONSULTA 2 - SUPERFICIE Y HABITACIONES
# ==========================================

print("\n=== CONSULTA 2: VIVIENDAS DE 80 M2 Y 3 HABITACIONES ===")

filtro2 = {
    "caracteristicas.m2": {"$gte": 80},
    "caracteristicas.habitaciones": {"$gte": 3}
}

total2 = anuncios.count_documents(filtro2)
print("Total de anuncios encontrados:", total2)

resultados2 = anuncios.find(
    filtro2,
    {
        "_id": 0,
        "municipio": 1,
        "precio": 1,
        "caracteristicas.m2": 1,
        "caracteristicas.habitaciones": 1
    }
).sort("precio", 1).limit(10)

for anuncio in resultados2:
    print(anuncio)


# ==========================================
# CONSULTA 3 - CONDICIONES COMBINADAS
# ==========================================

print("\n=== CONSULTA 3: VIVIENDAS EN BILBAO O GETXO ===")

filtro3 = {
    "municipio": {"$in": ["Bilbao", "Getxo"]},
    "operacion": "venta",
    "precio": {"$gte": 150000, "$lte": 350000},
    "caracteristicas.m2": {"$gte": 70}
}

total3 = anuncios.count_documents(filtro3)
print("Total de anuncios encontrados:", total3)

resultados3 = anuncios.find(
    filtro3,
    {
        "_id": 0,
        "municipio": 1,
        "precio": 1,
        "caracteristicas.m2": 1
    }
).sort("precio", 1).limit(10)

for anuncio in resultados3:
    print(anuncio)

# ==========================================
# CONSULTA 4 - ARRAY CON $elemMatch
# ==========================================

print("\n=== CONSULTA 4: PRESION ALQUILER 2026 > 150 ===")

mercado = db["mercado_alquiler"]

filtro4 = {
    "serie": {
        "$elemMatch": {
            "anyo": 2026,
            "presion": {"$gt": 150}
        }
    }
}

total4 = mercado.count_documents(filtro4)
print("Territorios encontrados:", total4)

resultados4 = mercado.find(
    filtro4,
    {
        "_id": 0,
        "nombre": 1,
        "territorio_id": 1,
        "serie": {
            "$elemMatch": {
                "anyo": 2026,
                "presion": {"$gt": 150}
            }
        }
    }
)

for territorio in resultados4:
    print(territorio)

# ==========================================
# CONSULTA 5 - ECONOMÍA JUVENIL
# ==========================================

print("\n=== CONSULTA 5: INDICADORES JUVENILES 2024 Y 2026 ===")

economia = db["economia_juvenil"]

filtro5 = {
    "anyo": {"$in": [2024, 2026]},
    "valor": {"$type": "number"}
}

total5 = economia.count_documents(filtro5)
print("Indicadores encontrados:", total5)

resultados5 = economia.find(
    filtro5,
    {
        "_id": 0,
        "anyo": 1,
        "indicador": 1,
        "categoria": 1,
        "unidad": 1,
        "valor": 1
    }
).sort([("anyo", 1), ("indicador", 1)]).limit(10)

for indicador in resultados5:
    print(indicador)

client.close()
