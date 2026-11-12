from pathlib import Path
import pandas as pd

base = Path("data/processed")

entrada = base / "compraventa_euskadi_clasificado.csv"
salida = base / "compraventa_euskadi_clasificado_v2.csv"

df = pd.read_csv(entrada, dtype={"id": str})

habitaciones = pd.to_numeric(
    df["habitaciones"], errors="coerce"
)

banos = pd.to_numeric(
    df["banos"], errors="coerce"
)

# Solo reclasificar anuncios pendientes
condicion = (
    df["tipo_inmueble_etl"].eq("revisar")
    & habitaciones.gt(0)
    & banos.gt(0)
)

df.loc[
    condicion, "tipo_inmueble_etl"
] = "vivienda_probable"

# Mantener la trazabilidad
df["criterio_clasificacion_etl"] = "descripcion"

df.loc[
    df["tipo_inmueble_etl"].eq("vivienda_probable"),
    "criterio_clasificacion_etl"
] = "habitaciones_y_banos"

df.loc[
    df["tipo_inmueble_etl"].eq("revisar"),
    "criterio_clasificacion_etl"
] = "evidencia_insuficiente"

df.loc[
    df["tipo_inmueble_etl"].eq("no_residencial"),
    "criterio_clasificacion_etl"
] = "revision_manual"

df.to_csv(salida, index=False, encoding="utf-8-sig")

print("\nCLASIFICACION V2")
print("====================")
print(df["tipo_inmueble_etl"].value_counts())

print("\nTotal:", len(df))
print("Archivo:", salida)