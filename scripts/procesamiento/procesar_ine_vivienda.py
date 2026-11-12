
from pathlib import Path
import pandas as pd

# 1. Rutas
origen = Path("data/raw/ine_api/indicadores_vivienda_euskadi.csv")
destino = Path("data/processed/ine_precios_vivienda_municipios.csv")

# 2. Cargar datos
df = pd.read_csv(origen)

# 3. Seleccionar indicadores de compraventa
df = df[df["indicador"] == "precio medio"].copy()

# 4. Identificar las seis series
series = {
    "Precio medio de la vivienda (Euros)":
        "precio_medio_vivienda_eur",

    "Precio medio de la vivienda tipo piso (Euros)":
        "precio_medio_piso_eur",

    "Precio medio de la vivienda tipo unifamiliar (Euros)":
        "precio_medio_unifamiliar_eur",

    "Precio medio por metro cuadrado de la vivienda (Euros/m2)":
        "precio_m2_vivienda",

    "Precio medio por metro cuadrado de la vivienda tipo piso (Euros/m2)":
        "precio_m2_piso",

    "Precio medio por metro cuadrado de la vivienda tipo unifamiliar (Euros/m2)":
        "precio_m2_unifamiliar"
}

# 5. Identificar indicador a partir de la serie
df["tipo_indicador"] = pd.NA

for texto, columna in series.items():
    mascara = df["serie"].str.contains(
        texto, regex=False, na=False
    )
    df.loc[mascara, "tipo_indicador"] = columna

# 6. Comprobar que todas las series se identificaron
if df["tipo_indicador"].isna().any():
    raise ValueError("Hay series sin clasificar")

# 7. Comprobar que no hay claves duplicadas
claves = ["municipio", "anyo", "tipo_indicador"]

if df.duplicated(subset=claves).any():
    raise ValueError("Hay indicadores duplicados")

# 8. Convertir a formato ancho
resultado = df.pivot(
    index=["municipio", "anyo"],
    columns="tipo_indicador",
    values="valor"
).reset_index()

resultado.columns.name = None

# 9. Ordenar
resultado = resultado.sort_values(
    ["municipio", "anyo"]
)

# 10. Guardar
destino.parent.mkdir(parents=True, exist_ok=True)

resultado.to_csv(
    destino,
    index=False,
    encoding="utf-8-sig"
)

# 11. Resumen
print("Archivo generado:", destino)
print("Registros:", len(resultado))
print("Municipios:", resultado["municipio"].nunique())
print("Años:", sorted(resultado["anyo"].unique()))

print("\nValores nulos:")
print(resultado.isna().sum().to_string())

print("\nPrimeras filas:")
print(resultado.head().to_string(index=False))
