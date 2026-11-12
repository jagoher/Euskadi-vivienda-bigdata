
import pandas as pd
from pathlib import Path

# ==========================================
# 1. CONFIGURACIÓN
# ==========================================

carpeta = Path("data/processed")

archivo_eustat = carpeta / "alquiler_municipios_eustat.csv"
archivo_ine = carpeta / "catalogo_municipios_euskadi_2026.csv"

salida = carpeta / "alquiler_municipios_euskadi_integrado.csv"

# ==========================================
# 2. CARGAR DATOS
# ==========================================

eustat = pd.read_csv(archivo_eustat)

ine = pd.read_csv(
    archivo_ine,
    dtype={"codigo_ine": str}
)

# ==========================================
# 3. NORMALIZAR NOMBRES
# ==========================================

equivalencias = {
    "Arrankudiaga": "Arrankudiaga-Zollo",
    "Donostia / San Sebastián": "Donostia/San Sebastián",
    "Munitibar -Arbatzegi Gerrikaitz-": "Munitibar-Arbatzegi Gerrikaitz",
    "Ribera Baja/Erribera Beitia": "Ribera Baja/Erriberabeitia",
    "Urduña-Orduña": "Urduña/Orduña",
}

eustat["municipio_eustat"] = eustat["municipio"]

eustat["municipio"] = (
    eustat["municipio"].replace(equivalencias)
)

# ==========================================
# 4. UNIR EUSTAT CON INE
# ==========================================

integrado = eustat.merge(
    ine,
    left_on="municipio",
    right_on="municipio_ine",
    how="left",
    validate="one_to_one"
)

# ==========================================
# 5. ORDENAR COLUMNAS
# ==========================================

columnas_inicio = [
    "codigo_ine",
    "municipio_ine",
    "provincia",
    "municipio_eustat",
]

otras_columnas = [
    c for c in integrado.columns
    if c not in columnas_inicio + ["municipio"]
]

integrado = integrado[
    columnas_inicio + otras_columnas
]

# ==========================================
# 6. VALIDACIONES
# ==========================================

print("\nINTEGRACIÓN EUSTAT + INE")
print("=" * 50)

print("Municipios:", len(integrado))

print(
    "Sin código INE:",
    integrado["codigo_ine"].isna().sum()
)

print(
    "Códigos duplicados:",
    integrado["codigo_ine"].duplicated().sum()
)

print(
    "Con alquiler medio:",
    integrado["alquiler_medio"].notna().sum()
)

print(
    "Sin alquiler medio:",
    integrado["alquiler_medio"].isna().sum()
)

print("\nMUNICIPIOS POR PROVINCIA")
print(integrado.groupby("provincia").size())

# ==========================================
# 7. GUARDAR RESULTADO
# ==========================================

if (
    len(integrado) != 252
    or integrado["codigo_ine"].isna().any()
    or integrado["codigo_ine"].duplicated().any()
):
    raise ValueError("La integración no ha superado las validaciones.")

integrado.to_csv(
    salida,
    index=False,
    encoding="utf-8-sig"
)

print("\nARCHIVO GENERADO:", salida)
print("\nINTEGRACIÓN FINALIZADA")
