
import pandas as pd
from pathlib import Path

# ==========================================
# 1. ARCHIVOS
# ==========================================

carpeta = Path("data/processed")

entrada = (
    carpeta / "compraventa_euskadi_pisos_com_integrado_v3.csv"
)

salida = (
    carpeta / "compraventa_euskadi_pisos_com_integrado_v4.csv"
)

# ==========================================
# 2. CARGAR DATOS
# ==========================================

df = pd.read_csv(
    entrada,
    dtype={"id": str}
)

# ==========================================
# 3. CLASIFICACIÓN INICIAL
# ==========================================

df["estado_duplicado"] = "sin_indicios"

df.loc[
    df["posible_duplicado_ampliado"] == True,
    "estado_duplicado"
] = "revisar"

# ==========================================
# 4. NORMALIZAR DESCRIPCIONES
# ==========================================

df["descripcion_normalizada"] = (
    df["descripcion"]
    .fillna("")
    .astype(str)
    .str.strip()
    .str.lower()
)

# ==========================================
# 5. IDENTIFICAR GRUPOS DE ALTA CONFIANZA
# ==========================================

candidatos = df[
    df["posible_duplicado_ampliado"] == True
].copy()

resumen = candidatos.groupby(
    "grupo_duplicado"
).agg(
    anuncios=("id", "size"),
    descripciones_distintas=(
        "descripcion_normalizada", "nunique"
    ),
    descripciones_vacias=(
        "descripcion_normalizada",
        lambda s: (s == "").sum()
    )
)

grupos_alta = resumen[
    (resumen["descripciones_distintas"] == 1)
    & (resumen["descripciones_vacias"] == 0)
].index

df.loc[
    df["grupo_duplicado"].isin(grupos_alta),
    "estado_duplicado"
] = "alta_confianza"

# ==========================================
# 6. ELIMINAR COLUMNA AUXILIAR
# ==========================================

df = df.drop(
    columns=["descripcion_normalizada"]
)

# ==========================================
# 7. VALIDAR RESULTADOS
# ==========================================

conteo = df["estado_duplicado"].value_counts()

print("\nCLASIFICACIÓN DE DUPLICADOS")
print("=" * 50)

print(conteo.to_string())

print("\nGrupos de alta confianza:", len(grupos_alta))
print("Total de anuncios:", len(df))

assert len(df) == 2968
assert len(grupos_alta) == 9
assert (df["estado_duplicado"] == "alta_confianza").sum() == 18
assert (df["estado_duplicado"] == "revisar").sum() == 52

# ==========================================
# 8. GUARDAR
# ==========================================

df.to_csv(
    salida,
    index=False,
    encoding="utf-8-sig"
)

print("\nARCHIVO GENERADO:")
print(salida)
