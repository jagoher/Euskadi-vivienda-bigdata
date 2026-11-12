
import pandas as pd
from pathlib import Path

# ==========================================
# 1. CONFIGURACIÓN
# ==========================================

carpeta = Path("data/processed")

archivo_base = carpeta / "alquiler_municipios_euskadi_2024_2025.csv"

archivo_ine = (
    carpeta / "ine_precios_vivienda_municipios_normalizado.csv"
)

archivo_reg = (
    carpeta / "registradores_precios_municipios_2025_normalizado.csv"
)

salida = carpeta / "vivienda_euskadi_municipios_integrado.csv"

# ==========================================
# 2. CARGAR DATOS
# ==========================================

base = pd.read_csv(
    archivo_base,
    dtype={"codigo_ine": str}
)

ine = pd.read_csv(archivo_ine)
reg = pd.read_csv(archivo_reg)

# ==========================================
# 3. PREPARAR INE 2025
# ==========================================

ine = ine[ine["anyo"] == 2025].copy()

ine = ine[
    [
        "municipio_normalizado",
        "precio_m2_vivienda",
        "precio_medio_vivienda_eur"
    ]
].rename(
    columns={
        "precio_m2_vivienda": "ine_precio_m2_2025",
        "precio_medio_vivienda_eur": "ine_precio_medio_2025"
    }
)

# ==========================================
# 4. PREPARAR REGISTRADORES 2025
# ==========================================

reg = reg[reg["anyo"] == 2025].copy()

reg = reg[
    [
        "municipio_normalizado",
        "precio_medio_vivienda_eur",
        "precio_m2_eur"
    ]
].rename(
    columns={
        "precio_medio_vivienda_eur": "registradores_precio_medio_2025",
        "precio_m2_eur": "registradores_precio_m2_2025"
    }
)

# ==========================================
# 5. INTEGRAR POR MUNICIPIO
# ==========================================

integrado = base.merge(
    ine,
    left_on="municipio_ine",
    right_on="municipio_normalizado",
    how="left",
    validate="one_to_one"
).drop(columns=["municipio_normalizado"])

integrado = integrado.merge(
    reg,
    left_on="municipio_ine",
    right_on="municipio_normalizado",
    how="left",
    validate="one_to_one"
).drop(columns=["municipio_normalizado"])

# ==========================================
# 6. VALIDACIONES
# ==========================================

print("\nINTEGRACIÓN MUNICIPAL DE VIVIENDA")
print("=" * 50)

print("Municipios:", len(integrado))

print(
    "Con alquiler Eustat:",
    integrado["eustat_alquiler_medio_2024"].notna().sum()
)

print(
    "Con alquiler EMAL:",
    integrado["emal_alquiler_medio_2025"].notna().sum()
)

print(
    "Con compraventa INE:",
    integrado["ine_precio_medio_2025"].notna().sum()
)

print(
    "Con compraventa Registradores:",
    integrado["registradores_precio_medio_2025"].notna().sum()
)

print(
    "Con precio/m2 Registradores:",
    integrado["registradores_precio_m2_2025"].notna().sum()
)

print(
    "Códigos INE duplicados:",
    integrado["codigo_ine"].duplicated().sum()
)

# ==========================================
# 7. GUARDAR RESULTADO
# ==========================================

if len(integrado) != 252:
    raise ValueError("El número de municipios ha cambiado.")

if integrado["codigo_ine"].duplicated().any():
    raise ValueError("Existen códigos INE duplicados.")

integrado.to_csv(
    salida,
    index=False,
    encoding="utf-8-sig"
)

print("\nARCHIVO GENERADO:", salida)
print("\nINTEGRACIÓN FINALIZADA")
