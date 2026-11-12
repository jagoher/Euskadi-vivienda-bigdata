
from pathlib import Path
import pandas as pd

# ==========================================
# 1. RUTAS
# ==========================================

ORIGEN = Path(
    "data/raw/observatorio_vivienda/"
    "EMAL.-Barrios-Municipios.-2016-2026_es.xlsx"
)

DESTINO = Path("data/processed")
DESTINO.mkdir(parents=True, exist_ok=True)

# ==========================================
# 2. LEER EXCEL
# ==========================================

df = pd.read_excel(
    ORIGEN,
    sheet_name="T2.2",
    header=None,
    dtype={0: str}
)

# Filas municipales principales: 5 a 77
municipios = df.iloc[5:78].copy()

municipios = municipios.rename(
    columns={
        0: "codigo_ine",
        1: "municipio"
    }
)

municipios["codigo_ine"] = (
    municipios["codigo_ine"]
    .astype(str)
    .str.strip()
    .str.zfill(5)
)

municipios["municipio"] = (
    municipios["municipio"]
    .astype(str)
    .str.replace(
        r"\s*\(1\)$",
        "",
        regex=True
    )
    .str.strip()
)

# ==========================================
# 3. VALIDAR MUNICIPIOS
# ==========================================

if municipios["codigo_ine"].duplicated().any():
    raise ValueError("Existen códigos INE duplicados")

print("Municipios encontrados:", len(municipios))

# ==========================================
# 4. EXTRAER SERIES ANUALES
# ==========================================

columnas_anuales = {
    columna: anyo
    for columna, anyo in zip(
        range(2, 12),
        range(2016, 2026)
    )
}

anual = municipios[
    ["codigo_ine", "municipio"]
    + list(columnas_anuales.keys())
].copy()

anual = anual.rename(columns=columnas_anuales)

anual = anual.melt(
    id_vars=["codigo_ine", "municipio"],
    var_name="anyo",
    value_name="renta_mensual_eur"
)

anual["anyo"] = anual["anyo"].astype(int)

anual["renta_mensual_eur"] = pd.to_numeric(
    anual["renta_mensual_eur"],
    errors="coerce"
)

anual = anual.sort_values(
    ["codigo_ine", "anyo"]
).reset_index(drop=True)

# ==========================================
# 5. EXTRAER ALQUILERES VIGENTES
# ==========================================

vigentes = municipios[
    ["codigo_ine", "municipio", 13]
].copy()

vigentes = vigentes.rename(
    columns={13: "renta_mensual_eur"}
)

vigentes["fecha_referencia"] = "2025-12-31"

vigentes["renta_mensual_eur"] = pd.to_numeric(
    vigentes["renta_mensual_eur"],
    errors="coerce"
)

vigentes = vigentes[
    [
        "codigo_ine",
        "municipio",
        "fecha_referencia",
        "renta_mensual_eur"
    ]
]

# ==========================================
# 6. GUARDAR ARCHIVOS
# ==========================================

archivo_anual = (
    DESTINO / "emal_alquiler_municipios_anual.csv"
)

archivo_vigentes = (
    DESTINO / "emal_alquileres_vigentes_2025.csv"
)

anual.to_csv(
    archivo_anual,
    index=False,
    encoding="utf-8-sig"
)

vigentes.to_csv(
    archivo_vigentes,
    index=False,
    encoding="utf-8-sig"
)

# ==========================================
# 7. VALIDACION
# ==========================================

print("\n===================================")
print("RESULTADO EMAL MUNICIPIOS")
print("===================================")

print("Municipios:", anual["codigo_ine"].nunique())
print("Registros anuales:", len(anual))
print(
    "Rentas anuales disponibles:",
    anual["renta_mensual_eur"].notna().sum()
)
print(
    "Rentas anuales ausentes:",
    anual["renta_mensual_eur"].isna().sum()
)

print("\nALQUILERES VIGENTES:")
print("Registros:", len(vigentes))
print(
    "Rentas disponibles:",
    vigentes["renta_mensual_eur"].notna().sum()
)

print("\nDATOS 2025:")
print(
    anual[
        anual["anyo"] == 2025
    ][["municipio", "renta_mensual_eur"]]
    .head(12)
    .to_string(index=False)
)

print("\nArchivos generados:")
print(archivo_anual)
print(archivo_vigentes)

print("\nPROCESAMIENTO FINALIZADO")
