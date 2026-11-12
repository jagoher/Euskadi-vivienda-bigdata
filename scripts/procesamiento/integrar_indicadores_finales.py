
from pathlib import Path
import pandas as pd

BASE = Path("data/processed")

alquiler = pd.read_csv(
    BASE / "esfuerzo_alquiler_juvenil_municipios_2024.csv",
    dtype={"codigo_ine": str}
)

compra = pd.read_csv(
    BASE / "accesibilidad_compra_juvenil_municipios.csv",
    dtype={"codigo_ine": str}
)

# Seleccionamos solo los indicadores nuevos de compraventa
columnas_compra = [
    "codigo_ine",
    "ine_precio_medio_2025",
    "registradores_precio_medio_2025",
    "anos_salario_compra_ine",
    "anos_salario_compra_registradores"
]

# Unión uno a uno por código INE
df = alquiler.merge(
    compra[columnas_compra],
    on="codigo_ine",
    how="left",
    validate="one_to_one",
    indicator=True
)

assert (df["_merge"] == "both").all()
df = df.drop(columns="_merge")

# Disponibilidad de indicadores
df["tiene_alquiler"] = df["esfuerzo_alquiler_pct"].notna()
df["tiene_compra"] = df[
    ["anos_salario_compra_ine", "anos_salario_compra_registradores"]
].notna().any(axis=1)

# Información metodológica
df["anyo_salario_referencia"] = 2024
df["anyo_alquiler_referencia"] = 2024
df["anyo_compra_referencia"] = 2025

salida = BASE / "indicadores_vivienda_juvenil_euskadi.csv"
df.to_csv(salida, index=False, encoding="utf-8-sig")

print("TABLA ANALÍTICA FINAL")
print("====================")
print("Municipios:", len(df))
print("Códigos INE únicos:", df["codigo_ine"].nunique())
print("Con indicador alquiler:", df["tiene_alquiler"].sum())
print("Con indicador compra:", df["tiene_compra"].sum())
print("Con ambos indicadores:",
      (df["tiene_alquiler"] & df["tiene_compra"]).sum())
print("Sin indicadores:",
      (~df["tiene_alquiler"] & ~df["tiene_compra"]).sum())
print("\nColumnas:", len(df.columns))
print("Archivo generado:", salida)

assert len(df) == 252
assert df["codigo_ine"].is_unique
assert df["tiene_alquiler"].sum() == 159
assert df["tiene_compra"].sum() == 31

print("\nVALIDACIÓN CORRECTA")
