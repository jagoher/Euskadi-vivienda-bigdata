from pathlib import Path
import pandas as pd

BASE = Path("data/processed")

ENTRADA = BASE / "compraventa_euskadi_pisos_com_integrado_v4.csv"
SALIDA = BASE / "compraventa_euskadi_clasificado.csv"

df = pd.read_csv(ENTRADA, dtype={"id": str})

# Conservar todos los anuncios
df["tipo_inmueble_etl"] = "revisar"

# Identificar viviendas por indicios explícitos
patron_vivienda = (
    r"\b(piso|vivienda|apartamento|chalet|"
    r"adosado|atico|ático|duplex|dúplex|"
    r"casa|dormitorios?)\b"
)

es_vivienda = df["descripcion"].fillna("").str.contains(
    patron_vivienda,
    case=False,
    regex=True
)

df.loc[es_vivienda, "tipo_inmueble_etl"] = "vivienda"

# Tres inmuebles no residenciales identificados
no_residenciales = [
    "68427042962.1061",
    "67569845551.1061",
    "66750866361.107100",
]

df.loc[
    df["id"].isin(no_residenciales),
    "tipo_inmueble_etl"
] = "no_residencial"

# Registrar discrepancia municipal detectada
df["revision_municipio_etl"] = False

df.loc[
    df["id"] == "66750866361.107100",
    "revision_municipio_etl"
] = True

# Guardar sin eliminar registros
df.to_csv(SALIDA, index=False, encoding="utf-8-sig")

print("\nCLASIFICACIÓN ETL")
print("====================")
print(df["tipo_inmueble_etl"].value_counts())

print("\nTotal registros:", len(df))
print("Archivo generado:", SALIDA)