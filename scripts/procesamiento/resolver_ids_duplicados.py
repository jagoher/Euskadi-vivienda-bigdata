from pathlib import Path
import pandas as pd

BASE = Path("data/processed")

entrada = BASE / "compraventa_euskadi_clasificado_v2.csv"
salida = BASE / "compraventa_euskadi_clasificado_v3.csv"
auditoria = BASE / "auditoria_ids_duplicados.csv"

df = pd.read_csv(entrada, dtype={"id": str})

# Detectar IDs duplicados
df["id_repetido_etl"] = df.duplicated(
    subset=["id"],
    keep=False
)

# Registrar los casos originales para auditoría
duplicados = df[df["id_repetido_etl"]].copy()
duplicados.to_csv(
    auditoria,
    index=False,
    encoding="utf-8-sig"
)

# Priorizar registros con zona informada
df["zona_informada_etl"] = (
    df["zona"].notna()
    & df["zona"].astype(str).str.strip().ne("")
)

# Priorizar registros con descripción informada
df["descripcion_informada_etl"] = (
    df["descripcion"].notna()
    & df["descripcion"].astype(str).str.strip().ne("")
)

# Ordenar para elegir el registro más completo
df = df.sort_values(
    by=[
        "id",
        "zona_informada_etl",
        "descripcion_informada_etl"
    ],
    ascending=[True, False, False],
    kind="stable"
)

# Un documento por ID
df_unicos = df.drop_duplicates(
    subset=["id"],
    keep="first"
).copy()

# Los IDs repetidos necesitan validación municipal
df_unicos["revision_municipio_etl"] = (
    df_unicos["revision_municipio_etl"].fillna(False).astype(bool)
    | df_unicos["id_repetido_etl"]
)

# Guardar
df_unicos.to_csv(
    salida,
    index=False,
    encoding="utf-8-sig"
)

print("\nRESULTADO ETL V3")
print("====================")
print("Registros originales:", len(df))
print("IDs duplicados:", duplicados["id"].nunique())
print("Registros repetidos:", len(duplicados))
print("Registros únicos:", len(df_unicos))
print("Registros eliminados de la vista analítica:",
      len(df) - len(df_unicos))
print("Pendientes de revisión municipal:",
      df_unicos["revision_municipio_etl"].sum())

print("\nArchivo analítico:", salida)
print("Archivo auditoría:", auditoria)

assert df_unicos["id"].is_unique
assert len(df_unicos) == 2952

print("\nVALIDACIÓN CORRECTA")