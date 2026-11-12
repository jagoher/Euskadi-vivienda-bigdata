
import pandas as pd
from pathlib import Path

# ==========================================
# 1. CONFIGURACIÓN
# ==========================================

carpeta = Path("data/processed")

entrada = carpeta / "compraventa_euskadi_pisos_com_normalizado.csv"
salida = carpeta / "pisos_com_estadisticas_municipios.csv"

# ==========================================
# 2. CARGAR DATOS
# ==========================================

df = pd.read_csv(entrada)

# Asegurar valores numéricos
df["precio"] = pd.to_numeric(df["precio"], errors="coerce")
df["m2"] = pd.to_numeric(df["m2"], errors="coerce")

# ==========================================
# 3. CALCULAR PRECIO POR M2
# ==========================================

df["precio_m2"] = df["precio"] / df["m2"].where(df["m2"] > 0)

# ==========================================
# 4. MARCAR ANUNCIOS PARA REVISIÓN
# ==========================================

columnas_revision = [
    "posible_duplicado",
    "revision_tipo_inmueble",
    "superficie_no_valida",
    "superficie_desconocida"
]

for columna in columnas_revision:
    df[columna] = (
        df[columna].astype("string").str.lower()
        .isin(["true", "1", "si", "sí"])
    )

df["requiere_revision"] = df[columnas_revision].any(axis=1)

# ==========================================
# 5. AGREGAR POR MUNICIPIO
# ==========================================

resumen = df.groupby(
    "municipio_normalizado",
    as_index=False
).agg(
    anuncios_total=("id", "size"),
    anuncios_revision=("requiere_revision", "sum"),
    precio_mediano_oferta_eur=("precio", "median"),
    precio_medio_oferta_eur=("precio", "mean"),
    precio_m2_mediano_oferta_eur=("precio_m2", "median")
)

resumen["anuncios_sin_revision"] = (
    resumen["anuncios_total"] - resumen["anuncios_revision"]
)

# ==========================================
# 6. VALIDACIONES
# ==========================================

print("\nESTADÍSTICAS PISOS.COM")
print("=" * 55)

print("Municipios:", len(resumen))
print("Anuncios totales:", resumen["anuncios_total"].sum())
print("Anuncios marcados para revisión:", resumen["anuncios_revision"].sum())

print("\nRESUMEN POR MUNICIPIO")

print(
    resumen[
        [
            "municipio_normalizado",
            "anuncios_total",
            "anuncios_revision",
            "precio_mediano_oferta_eur"
        ]
    ].to_string(index=False)
)

# ==========================================
# 7. GUARDAR RESULTADO
# ==========================================

resumen.to_csv(
    salida,
    index=False,
    encoding="utf-8-sig"
)

print("\nARCHIVO GENERADO:", salida)
print("\nPROCESAMIENTO FINALIZADO")
