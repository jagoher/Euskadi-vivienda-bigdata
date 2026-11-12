
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

salarios = salarios[
    (salarios["anyo"] == 2024)
    & (salarios["dimension"] == "territorio")
    & (salarios["categoria"] != "Euskadi")
].copy()

salarios["provincia"] = salarios["categoria"].replace({
    "Álava": "Araba/Álava"
})

df = vivienda.merge(
    salarios[["provincia", "salario_neto_mensual"]],
    on="provincia",
    how="left",
    validate="many_to_one"
)

salario_anual = df["salario_neto_mensual"] * 12

df["anos_salario_compra_ine"] = (
    df["ine_precio_medio_2025"] / salario_anual
).round(2)

df["anos_salario_compra_registradores"] = (
    df["registradores_precio_medio_2025"] / salario_anual
).round(2)

columnas = [
    "codigo_ine",
    "municipio_ine",
    "provincia",
    "salario_neto_mensual",
    "ine_precio_medio_2025",
    "registradores_precio_medio_2025",
    "anos_salario_compra_ine",
    "anos_salario_compra_registradores"
]

resultado = df[columnas]

salida = BASE / "accesibilidad_compra_juvenil_municipios.csv"
resultado.to_csv(salida, index=False, encoding="utf-8-sig")

print("ACCESIBILIDAD A LA COMPRA")
print("========================")
print("Municipios totales:", len(resultado))
print("Con indicador INE:",
      resultado["anos_salario_compra_ine"].notna().sum())
print("Con indicador Registradores:",
      resultado["anos_salario_compra_registradores"].notna().sum())
print("Con alguna fuente:",
      resultado[
          ["anos_salario_compra_ine",
           "anos_salario_compra_registradores"]
      ].notna().any(axis=1).sum())

print("\nTOP 10 MAYOR DIFICULTAD (INE):")
print(
    resultado.nlargest(10, "anos_salario_compra_ine")[
        ["municipio_ine", "anos_salario_compra_ine"]
    ].to_string(index=False)
)

print("\nArchivo generado:", salida)

assert len(resultado) == 252
assert resultado["codigo_ine"].is_unique
