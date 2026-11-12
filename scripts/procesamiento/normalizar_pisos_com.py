
import pandas as pd
from pathlib import Path

carpeta = Path("data/processed")

entrada = carpeta / "compraventa_euskadi_pisos_com_limpio.csv"
salida = carpeta / "compraventa_euskadi_pisos_com_normalizado.csv"

# Cargar anuncios
df = pd.read_csv(entrada)

# Conservar municipio original
df["municipio_original"] = df["municipio"]

# Normalizar denominaciones
equivalencias = {
    "Donostia": "Donostia/San Sebastián"
}

df["municipio_normalizado"] = (
    df["municipio"].replace(equivalencias)
)

# Comprobar coincidencias con catálogo INE
catalogo = pd.read_csv(
    carpeta / "catalogo_municipios_euskadi_2026.csv",
    dtype={"codigo_ine": str}
)

sin_coincidencia = df.loc[
    ~df["municipio_normalizado"].isin(catalogo["municipio_ine"]),
    "municipio_normalizado"
].unique()

print("\nNORMALIZACIÓN PISOS.COM")
print("=" * 45)

print("Anuncios:", len(df))
print("Municipios:", df["municipio_normalizado"].nunique())
print("Nombres sin coincidencia:", len(sin_coincidencia))
print("Municipios sin coincidencia:", sin_coincidencia.tolist())

if len(sin_coincidencia) > 0:
    raise ValueError("Existen municipios sin correspondencia con INE.")

df.to_csv(
    salida,
    index=False,
    encoding="utf-8-sig"
)

print("\nARCHIVO GENERADO:", salida)
print("NORMALIZACIÓN FINALIZADA")
