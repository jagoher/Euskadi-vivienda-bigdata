
import pandas as pd
from pathlib import Path

# ==========================================
# 1. CONFIGURACIÓN
# ==========================================

archivo = Path("data/raw/ine_api/diccionario26.xlsx")

salida = Path(
    "data/processed/catalogo_municipios_euskadi_2026.csv"
)

# ==========================================
# 2. LEER EL EXCEL DEL INE
# ==========================================

df = pd.read_excel(
    archivo,
    dtype=str,
    header=1
)

print("COLUMNAS:", df.columns.tolist())
print("REGISTROS TOTALES:", len(df))

# ==========================================
# 3. FILTRAR MUNICIPIOS DE EUSKADI
# ==========================================

provincias = {
    "01": "Araba/Álava",
    "20": "Gipuzkoa",
    "48": "Bizkaia"
}

df["CPRO"] = df["CPRO"].str.zfill(2)
df["CMUN"] = df["CMUN"].str.zfill(3)

euskadi = df[
    df["CPRO"].isin(provincias)
].copy()

euskadi["provincia"] = (
    euskadi["CPRO"].map(provincias)
)

print("\nMUNICIPIOS DE EUSKADI")
print("=" * 45)

print("Total:", len(euskadi))

print(
    euskadi.groupby("provincia").size()
)

# ==========================================
# 4. CREAR CÓDIGO INE MUNICIPAL
# ==========================================

euskadi["codigo_ine"] = (
    euskadi["CPRO"] + euskadi["CMUN"]
)

# ==========================================
# 5. CREAR CATÁLOGO MUNICIPAL
# ==========================================

catalogo = euskadi[
    ["codigo_ine", "NOMBRE", "provincia"]
].copy()

catalogo = catalogo.rename(
    columns={"NOMBRE": "municipio_ine"}
)

catalogo = catalogo.sort_values(
    ["provincia", "municipio_ine"]
).reset_index(drop=True)

# ==========================================
# 6. VALIDAR DATOS
# ==========================================

print("\nVALIDACIÓN")
print("=" * 45)

print("Municipios:", len(catalogo))

print(
    "Códigos INE duplicados:",
    catalogo["codigo_ine"].duplicated().sum()
)

print(
    "Municipios sin nombre:",
    catalogo["municipio_ine"].isna().sum()
)

print(
    "Municipios sin provincia:",
    catalogo["provincia"].isna().sum()
)

print("\nGALDAKAO Y USANSOLO")

print(
    catalogo[
        catalogo["municipio_ine"].str.contains(
            "Galdakao|Usansolo",
            case=False,
            na=False
        )
    ].to_string(index=False)
)

# ==========================================
# 7. GUARDAR CSV
# ==========================================

salida.parent.mkdir(
    parents=True,
    exist_ok=True
)

catalogo.to_csv(
    salida,
    index=False,
    encoding="utf-8-sig"
)

print("\nARCHIVO GENERADO:")
print(salida)

print("\nFILAS:", len(catalogo))
print("COLUMNAS:", catalogo.columns.tolist())

print("\nPROCESAMIENTO FINALIZADO")
