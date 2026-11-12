
from pathlib import Path
import pandas as pd

# ==========================================
# 1. RUTAS
# ==========================================

ORIGEN = Path(
    "data/raw/ine_api/datos_hipotecas_pais_vasco_2026.csv"
)

DESTINO = Path(
    "data/processed/ine_hipotecas_viviendas_euskadi_2026.csv"
)

# ==========================================
# 2. CARGAR DATOS
# ==========================================

df = pd.read_csv(ORIGEN, sep=";")

# ==========================================
# 3. SELECCIONAR HIPOTECAS DE VIVIENDAS
# ==========================================

df = df[
    df["Nombre"].str.startswith("Viviendas.", na=False)
].copy()

# ==========================================
# 4. IDENTIFICAR INDICADORES
# ==========================================

df["indicador"] = pd.NA

df.loc[
    df["Nombre"].str.contains(
        "Número de hipotecas", regex=False
    ),
    "indicador"
] = "numero_hipotecas"

df.loc[
    df["Nombre"].str.contains(
        "Importe de hipotecas", regex=False
    ),
    "indicador"
] = "importe_miles_euros"

if df["indicador"].isna().any():
    raise ValueError("Hay indicadores sin identificar")

# ==========================================
# 5. ORGANIZAR DATOS POR MES
# ==========================================

df["Valor"] = pd.to_numeric(
    df["Valor"], errors="coerce"
)

if df.duplicated(
    subset=["NombrePeriodo", "indicador"]
).any():
    raise ValueError("Hay registros duplicados")

resultado = df.pivot(
    index="NombrePeriodo",
    columns="indicador",
    values="Valor"
).reset_index()

resultado.columns.name = None

resultado = resultado.rename(
    columns={"NombrePeriodo": "periodo"}
)

# ==========================================
# 6. CALCULAR IMPORTE MEDIO
# ==========================================

resultado["importe_medio_euros"] = (
    resultado["importe_miles_euros"] * 1000
    / resultado["numero_hipotecas"].replace(0, float("nan"))
)

resultado["territorio"] = "Euskadi"
resultado["datos_provisionales"] = True

# ==========================================
# 7. ORDENAR Y GUARDAR
# ==========================================

resultado = resultado[
    [
        "territorio",
        "periodo",
        "numero_hipotecas",
        "importe_miles_euros",
        "importe_medio_euros",
        "datos_provisionales"
    ]
].sort_values("periodo")

DESTINO.parent.mkdir(parents=True, exist_ok=True)

resultado.to_csv(
    DESTINO,
    index=False,
    encoding="utf-8-sig"
)

# ==========================================
# 8. RESUMEN
# ==========================================

print("Archivo generado:", DESTINO)
print("Meses:", len(resultado))

print(
    "Total hipotecas:",
    int(resultado["numero_hipotecas"].sum())
)

print(
    "Importe total (miles de euros):",
    resultado["importe_miles_euros"].sum()
)

print("\nDATOS PROCESADOS:")
print(resultado.to_string(index=False))

print("\nPROCESAMIENTO FINALIZADO")
