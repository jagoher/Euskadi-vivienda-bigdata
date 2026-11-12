
from pathlib import Path
import pandas as pd

BASE = Path("data/processed")

vivienda = pd.read_csv(
    BASE / "vivienda_euskadi_municipios_integrado.csv",
    dtype={"codigo_ine": str}
)

salarios = pd.read_csv(
    BASE / "salarios_juveniles_euskadi.csv"
)

# Seleccionar salarios territoriales de 2024
salarios_2024 = salarios[
    (salarios["anyo"] == 2024)
    & (salarios["dimension"] == "territorio")
    & (salarios["categoria"] != "Euskadi")
].copy()

# Normalizar nombres de provincia
equivalencias = {
    "Álava": "Araba/Álava",
    "Bizkaia": "Bizkaia",
    "Gipuzkoa": "Gipuzkoa"
}

salarios_2024["provincia"] = (
    salarios_2024["categoria"].replace(equivalencias)
)

salarios_2024 = salarios_2024[
    ["provincia", "salario_neto_mensual"]
]

# Unir por provincia
df = vivienda.merge(
    salarios_2024,
    on="provincia",
    how="left",
    validate="many_to_one"
)

# Calcular esfuerzo de alquiler
df["esfuerzo_alquiler_pct"] = (
    df["eustat_alquiler_medio_2024"]
    / df["salario_neto_mensual"]
    * 100
).round(2)

df["supera_30_pct"] = (
    df["esfuerzo_alquiler_pct"] > 30
).astype("boolean")

df.loc[
    df["esfuerzo_alquiler_pct"].isna(),
    "supera_30_pct"
] = pd.NA

# Guardar resultado
columnas = [
    "codigo_ine",
    "municipio_ine",
    "provincia",
    "eustat_alquiler_medio_2024",
    "salario_neto_mensual",
    "esfuerzo_alquiler_pct",
    "supera_30_pct"
]

resultado = df[columnas]

salida = BASE / "esfuerzo_alquiler_juvenil_municipios_2024.csv"
resultado.to_csv(salida, index=False, encoding="utf-8-sig")

print("RESULTADO ESFUERZO ALQUILER")
print("==========================")
print("Municipios totales:", len(resultado))
print("Con esfuerzo calculado:", resultado["esfuerzo_alquiler_pct"].notna().sum())
print("Sin salario provincial:", resultado["salario_neto_mensual"].isna().sum())
print("Municipios que superan el 30%:", (resultado["supera_30_pct"] == True).sum())
print("\nTOP 10 MAYOR ESFUERZO:")
print(
    resultado.nlargest(10, "esfuerzo_alquiler_pct")[
        ["municipio_ine", "provincia", "esfuerzo_alquiler_pct"]
    ].to_string(index=False)
)
print("\nArchivo generado:", salida)
