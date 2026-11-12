
from pathlib import Path
import pandas as pd

# ==========================================
# 1. CONFIGURACION
# ==========================================

ORIGEN = Path(
    "data/processed/compraventa_euskadi_pisos_com.csv"
)

DESTINO_LIMPIO = Path(
    "data/processed/compraventa_euskadi_pisos_com_limpio.csv"
)

DESTINO_REVISION = Path(
    "data/processed/compraventa_euskadi_pisos_com_revision.csv"
)

# ==========================================
# 2. CARGAR DATOS
# ==========================================

df = pd.read_csv(ORIGEN, dtype={"id": "string"})

print("REGISTROS ORIGINALES:", len(df))

# ==========================================
# 3. DETECTAR PRECIOS NO VALIDOS
# ==========================================

df["precio"] = pd.to_numeric(
    df["precio"], errors="coerce"
)

df["precio_no_valido"] = (
    df["precio"].isna() | (df["precio"] <= 0)
)

print(
    "Precios no validos:",
    df["precio_no_valido"].sum()
)

# ==========================================
# 4. DETECTAR DUPLICADOS
# ==========================================

# Comparar las columnas originales,
# sin incluir las nuevas columnas de control.

columnas_originales = [
    c for c in df.columns
    if c != "precio_no_valido"
]

df["posible_duplicado"] = df.duplicated(
    subset=columnas_originales,
    keep="first"
)

print(
    "Posibles duplicados:",
    df["posible_duplicado"].sum()
)

# ==========================================
# 5. DETECTAR ANUNCIOS SOSPECHOSOS
# ==========================================

# Estas palabras solo indican que hay que
# revisar el anuncio, no que sea incorrecto.

patron = (
    r"\b(?:parcela|terreno|garaje|trastero|"
    r"local comercial|solar|finca rustica|"
    r"finca rústica|isla)\b"
)

df["revision_tipo_inmueble"] = (
    df["descripcion"]
    .fillna("")
    .str.contains(
        patron,
        case=False,
        regex=True
    )
)

print(
    "Anuncios sospechosos:",
    df["revision_tipo_inmueble"].sum()
)

# ==========================================
# 6. MARCAR SUPERFICIES
# ==========================================

df["m2"] = pd.to_numeric(
    df["m2"], errors="coerce"
)

df["superficie_no_valida"] = (
    df["m2"].notna() & (df["m2"] <= 0)
)

df["superficie_desconocida"] = (
    df["m2"].isna()
)

# ==========================================
# 7. CREAR DATASET LIMPIO
# ==========================================

# Excluir solamente precios no validos.
# Mantener duplicados y anuncios sospechosos
# marcados para una revision posterior.

df_limpio = df[
    ~df["precio_no_valido"]
].copy()

# ==========================================
# 8. CREAR DATASET DE REVISION
# ==========================================

df_revision = df[
    df["precio_no_valido"]
    | df["posible_duplicado"]
    | df["revision_tipo_inmueble"]
    | df["superficie_no_valida"]
].copy()

# ==========================================
# 9. GUARDAR RESULTADOS
# ==========================================

DESTINO_LIMPIO.parent.mkdir(
    parents=True, exist_ok=True
)

df_limpio.to_csv(
    DESTINO_LIMPIO,
    index=False,
    encoding="utf-8-sig"
)

df_revision.to_csv(
    DESTINO_REVISION,
    index=False,
    encoding="utf-8-sig"
)

# ==========================================
# 10. RESUMEN FINAL
# ==========================================

print("\n========== RESUMEN ==========")

print("Registros originales:", len(df))

print("Registros limpios:", len(df_limpio))

print("Registros para revision:", len(df_revision))

print(
    "Municipios:",
    df_limpio["municipio"].nunique()
)

print(
    "Duplicados marcados:",
    df_limpio["posible_duplicado"].sum()
)

print(
    "Superficies desconocidas:",
    df_limpio["superficie_desconocida"].sum()
)

print(
    "Precio mediano:",
    df_limpio["precio"].median()
)

print("\nArchivos generados:")
print(DESTINO_LIMPIO)
print(DESTINO_REVISION)

print("\nLIMPIEZA FINALIZADA")
