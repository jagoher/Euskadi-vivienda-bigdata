
import pandas as pd
from pathlib import Path

# ==========================================
# 1. CONFIGURACIÓN
# ==========================================

carpeta = Path("data/processed")

archivo_base = carpeta / "alquiler_municipios_euskadi_integrado.csv"
archivo_emal = carpeta / "emal_alquileres_vigentes_2025_normalizado.csv"

salida = carpeta / "alquiler_municipios_euskadi_2024_2025.csv"

# ==========================================
# 2. CARGAR DATOS
# ==========================================

base = pd.read_csv(
    archivo_base,
    dtype={"codigo_ine": str}
)

emal = pd.read_csv(
    archivo_emal,
    dtype={"codigo_ine": str}
)

base["codigo_ine"] = base["codigo_ine"].str.zfill(5)
emal["codigo_ine"] = emal["codigo_ine"].str.zfill(5)

# ==========================================
# 3. PREPARAR DATOS DE EMAL
# ==========================================

emal = emal[
    ["codigo_ine", "fecha_referencia", "renta_mensual_eur"]
].copy()

emal = emal.rename(
    columns={
        "fecha_referencia": "emal_fecha_referencia",
        "renta_mensual_eur": "emal_alquiler_medio_2025"
    }
)

# ==========================================
# 4. INTEGRAR POR CÓDIGO INE
# ==========================================

integrado = base.merge(
    emal,
    on="codigo_ine",
    how="left",
    validate="one_to_one"
)

# Renombrar el indicador de Eustat
integrado = integrado.rename(
    columns={
        "alquiler_medio": "eustat_alquiler_medio_2024"
    }
)

# ==========================================
# 5. VALIDAR
# ==========================================

print("\nINTEGRACIÓN EUSTAT + EMAL")
print("=" * 50)

print("Municipios:", len(integrado))

print(
    "Con alquiler Eustat 2024:",
    integrado["eustat_alquiler_medio_2024"].notna().sum()
)

print(
    "Con alquiler EMAL 2025:",
    integrado["emal_alquiler_medio_2025"].notna().sum()
)

print(
    "Con ambos indicadores:",
    (
        integrado["eustat_alquiler_medio_2024"].notna()
        & integrado["emal_alquiler_medio_2025"].notna()
    ).sum()
)

print(
    "Sin ninguno de los dos:",
    (
        integrado["eustat_alquiler_medio_2024"].isna()
        & integrado["emal_alquiler_medio_2025"].isna()
    ).sum()
)

print(
    "Códigos INE duplicados:",
    integrado["codigo_ine"].duplicated().sum()
)

# ==========================================
# 6. GUARDAR CSV
# ==========================================

if len(integrado) != 252:
    raise ValueError("Se ha alterado el número de municipios.")

if integrado["codigo_ine"].duplicated().any():
    raise ValueError("Se han generado códigos INE duplicados.")

integrado.to_csv(
    salida,
    index=False,
    encoding="utf-8-sig"
)

print("\nARCHIVO GENERADO:", salida)
print("\nINTEGRACIÓN FINALIZADA")
