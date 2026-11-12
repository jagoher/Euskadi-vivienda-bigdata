
import pandas as pd
from pathlib import Path

# ==========================================
# 1. ARCHIVOS
# ==========================================

carpeta = Path("data/processed")

entrada = (
    carpeta / "compraventa_euskadi_pisos_com_integrado_v2.csv"
)

salida = (
    carpeta / "compraventa_euskadi_pisos_com_integrado_v3.csv"
)

# ==========================================
# 2. CARGAR DATOS
# ==========================================

df = pd.read_csv(
    entrada,
    dtype={"id": str}
)

# ==========================================
# 3. NORMALIZAR COORDENADAS
# ==========================================

for campo in ["lat", "lon"]:
    df[campo + "_num"] = pd.to_numeric(
        df[campo].astype(str).str.replace(
            ",", ".", regex=False
        ),
        errors="coerce"
    )

# ==========================================
# 4. DEFINIR CRITERIOS
# ==========================================

claves = [
    "municipio_normalizado",
    "precio",
    "m2",
    "habitaciones",
    "banos",
    "lat_num",
    "lon_num"
]

# Solo comparar registros completos
completos = df[claves].notna().all(axis=1)

df["posible_duplicado_ampliado"] = False
df["grupo_duplicado"] = pd.NA

# ==========================================
# 5. IDENTIFICAR GRUPOS
# ==========================================

candidatos = df.loc[completos].copy()

candidatos["posible_duplicado_ampliado"] = (
    candidatos.duplicated(
        subset=claves,
        keep=False
    )
)

duplicados = candidatos[
    candidatos["posible_duplicado_ampliado"]
].copy()

duplicados["grupo_duplicado"] = (
    duplicados.groupby(
        claves,
        sort=True
    ).ngroup() + 1
)

# ==========================================
# 6. ACTUALIZAR DATASET
# ==========================================

df.loc[
    duplicados.index,
    "posible_duplicado_ampliado"
] = True

df.loc[
    duplicados.index,
    "grupo_duplicado"
] = duplicados["grupo_duplicado"].astype(str)

# ==========================================
# 7. VALIDACIONES
# ==========================================

total = len(df)

marcados = int(
    df["posible_duplicado_ampliado"].sum()
)

grupos = (
    df["grupo_duplicado"].dropna().nunique()
)

assert total == 2968
assert marcados == 70
assert grupos == 34

# ==========================================
# 8. GUARDAR
# ==========================================

df.to_csv(
    salida,
    index=False,
    encoding="utf-8-sig"
)

print("\nCONTROL DE DUPLICADOS PISOS.COM")
print("=" * 50)

print("Anuncios totales:", total)
print("Grupos candidatos:", grupos)
print("Anuncios marcados:", marcados)
print("Anuncios no marcados:", total - marcados)

print("\nARCHIVO GENERADO:")
print(salida)
