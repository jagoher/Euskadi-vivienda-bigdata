from pathlib import Path
import pandas as pd

BASE = Path("data/processed")

entrada = BASE / "compraventa_euskadi_clasificado_v3.csv"
salida = BASE / "compraventa_euskadi_mongodb.jsonl"

df = pd.read_csv(entrada, dtype={"id": str})

# Convertir campos numéricos
columnas_numericas = [
    "precio",
    "m2",
    "habitaciones",
    "banos",
    "lat_num",
    "lon_num",
]

for col in columnas_numericas:
    df[col] = pd.to_numeric(df[col], errors="coerce")

# Metadatos de procedencia
df["fuente_etl"] = "pisos.com"
df["tipo_precio_etl"] = "precio_oferta"

# Exportación a JSON Lines
df.to_json(
    salida,
    orient="records",
    lines=True,
    force_ascii=False
)

print("EXPORTACIÓN MONGODB")
print("===================")
print("Documentos:", len(df))
print("Archivo:", salida)

# Verificar el archivo exportado
verificacion = pd.read_json(
    salida,
    lines=True,
    dtype={"id": str}
)

print("Documentos verificados:", len(verificacion))
print("IDs únicos:", verificacion["id"].nunique())
print("Nulos en precio:", verificacion["precio"].isna().sum())
print("Nulos en superficie:", verificacion["m2"].isna().sum())

assert len(verificacion) == len(df)
assert verificacion["id"].nunique() == len(df)

print("VALIDACIÓN CORRECTA")