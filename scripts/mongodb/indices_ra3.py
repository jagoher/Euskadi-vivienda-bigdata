from pymongo import MongoClient

URI = "mongodb://localhost:27017/"
DB_NAME = "EUSKADI_VIVIENDA_BIGDATA_TEST"

if DB_NAME != "EUSKADI_VIVIENDA_BIGDATA_TEST":
    raise RuntimeError("Solo se permite trabajar en TEST")

client = MongoClient(URI, serverSelectionTimeoutMS=5000)
client.admin.command("ping")

db = client[DB_NAME]
anuncios = db["anuncios"]

print("=== INDICES ACTUALES DE ANUNCIOS ===")

for nombre, datos in anuncios.index_information().items():
    print(nombre, datos["key"])

print("\nTotal de anuncios:", anuncios.count_documents({}))

# ==========================================
# EXPLAIN ANTES DEL INDICE
# ==========================================

print("\n=== EXPLAIN ANTES DEL INDICE ===")

filtro = {"municipio": "Bilbao"}

resultado = db.command(
    "explain",
    {
        "find": "anuncios",
        "filter": filtro
    },
    verbosity="executionStats"
)

estadisticas = resultado["executionStats"]

print("Documentos encontrados:", estadisticas["nReturned"])
print("Documentos examinados:", estadisticas["totalDocsExamined"])
print("Claves de indice examinadas:", estadisticas["totalKeysExamined"])
print("Tiempo de ejecucion (ms):", estadisticas["executionTimeMillis"])

print(
    "Plan de ejecucion:",
    resultado["queryPlanner"]["winningPlan"]
)

# ==========================================
# CREACION DEL INDICE SECUNDARIO
# ==========================================

print("\n=== CREACION DEL INDICE ===")

nombre_indice = anuncios.create_index(
    [("municipio", 1)],
    name="idx_municipio_ra3"
)

print("Indice creado o verificado:", nombre_indice)

print("\nIndices actuales:")

for nombre, datos in anuncios.index_information().items():
    print(nombre, datos["key"])

# ==========================================
# EXPLAIN DESPUES DEL INDICE
# ==========================================

print("\n=== EXPLAIN DESPUES DEL INDICE ===")

resultado_despues = db.command(
    "explain",
    {
        "find": "anuncios",
        "filter": {"municipio": "Bilbao"}
    },
    verbosity="executionStats"
)

stats_despues = resultado_despues["executionStats"]

print("Documentos encontrados:", stats_despues["nReturned"])
print("Documentos examinados:", stats_despues["totalDocsExamined"])
print("Claves de indice examinadas:", stats_despues["totalKeysExamined"])
print("Tiempo de ejecucion (ms):", stats_despues["executionTimeMillis"])

print(
    "Plan de ejecucion:",
    resultado_despues["queryPlanner"]["winningPlan"]
)

client.close()