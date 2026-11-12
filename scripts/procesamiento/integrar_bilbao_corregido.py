
import pandas as pd
from pathlib import Path

# ==========================================
# 1. CONFIGURACIÓN
# ==========================================

carpeta = Path("data/processed")

archivo_general = (
    carpeta / "compraventa_euskadi_pisos_com_normalizado.csv"
)

archivo_bilbao = (
    carpeta / "bilbao_pisos_com_corregido.csv"
)

archivo_salida = (
    carpeta / "compraventa_euskadi_pisos_com_integrado_v2.csv"
)

# ==========================================
# 2. CARGAR DATOS
# ==========================================

general = pd.read_csv(
    archivo_general,
    dtype={"id": str}
)

bilbao = pd.read_csv(
    archivo_bilbao,
    dtype={"id": str}
)

print("\nINTEGRACIÓN PISOS.COM")
print("=" * 55)

print("Registros originales:", len(general))
print("Bilbao corregido:", len(bilbao))

# ==========================================
# 3. CONSERVAR LOS OTROS 11 MUNICIPIOS
# ==========================================

otros = general[
    general["municipio_normalizado"] != "Bilbao"
].copy()

# ==========================================
# 4. IDENTIFICAR MUNICIPIO Y ORIGEN
# ==========================================

bilbao["municipio"] = "Bilbao"
bilbao["municipio_original"] = "Bilbao"
bilbao["municipio_normalizado"] = "Bilbao"

bilbao["archivo_origen"] = (
    "1_pisos_bilbao_corregido.csv"
)

# ==========================================
# 5. CONVERTIR CAMPOS NUMÉRICOS
# ==========================================

for campo in [
    "precio",
    "m2",
    "habitaciones",
    "banos"
]:
    bilbao[campo] = pd.to_numeric(
        bilbao[campo],
        errors="coerce"
    )

# ==========================================
# 6. VALIDAR PRECIOS
# ==========================================

bilbao["precio_no_valido"] = (
    bilbao["precio"].isna()
    | (bilbao["precio"] <= 0)
)

# ==========================================
# 7. DETECTAR POSIBLES DUPLICADOS
# ==========================================

bilbao["posible_duplicado"] = (
    bilbao["id"].duplicated(keep=False)
)

# ==========================================
# 8. DETECTAR TIPOS DE INMUEBLE SOSPECHOSOS
# ==========================================

# Mismas palabras utilizadas en
# limpiar_pisos_com.py.
#
# No se eliminan los anuncios.
# Solo se marcan para revisión.

patron = (
    r"\b(?:parcela|terreno|garaje|trastero|"
    r"local comercial|solar|finca rustica|"
    r"finca rústica|isla)\b"
)

bilbao["revision_tipo_inmueble"] = (
    bilbao["descripcion"]
    .fillna("")
    .str.contains(
        patron,
        case=False,
        regex=True
    )
)

# ==========================================
# 9. VALIDAR SUPERFICIES
# ==========================================

bilbao["superficie_no_valida"] = (
    bilbao["m2"].notna()
    & (bilbao["m2"] <= 0)
)

bilbao["superficie_desconocida"] = (
    bilbao["m2"].isna()
)

# ==========================================
# 10. UNIFICAR COLUMNAS
# ==========================================

bilbao = bilbao.reindex(
    columns=general.columns
)

integrado = pd.concat(
    [otros, bilbao],
    ignore_index=True
)

# ==========================================
# 11. VALIDACIONES
# ==========================================

assert len(otros) == 2111, (
    "El número de anuncios de otros municipios ha cambiado."
)

assert len(bilbao) == 857, (
    "El número de anuncios de Bilbao no es el esperado."
)

assert len(integrado) == 2968, (
    "El total de anuncios no coincide."
)

assert (
    integrado["municipio_normalizado"].nunique() == 12
), "El número de municipios no coincide."

# ==========================================
# 12. MOSTRAR RESULTADOS
# ==========================================

print("\nRESULTADOS DE INTEGRACIÓN")
print("=" * 55)

print("Otros municipios:", len(otros))
print("Bilbao corregido:", len(bilbao))
print("Total integrado:", len(integrado))

print(
    "Municipios:",
    integrado["municipio_normalizado"].nunique()
)

print("\nCALIDAD DE DATOS DE BILBAO")
print("=" * 55)

print(
    "Precios no válidos:",
    bilbao["precio_no_valido"].sum()
)

print(
    "Posibles duplicados por ID:",
    bilbao["posible_duplicado"].sum()
)

print(
    "Revisión tipo inmueble:",
    bilbao["revision_tipo_inmueble"].sum()
)

print(
    "Superficies no válidas:",
    bilbao["superficie_no_valida"].sum()
)

print(
    "Superficies desconocidas:",
    bilbao["superficie_desconocida"].sum()
)

print(
    "Superficies disponibles:",
    bilbao["m2"].notna().sum()
)

# ==========================================
# 13. GUARDAR RESULTADO
# ==========================================

integrado.to_csv(
    archivo_salida,
    index=False,
    encoding="utf-8-sig"
)

print("\nARCHIVO GENERADO:")
print(archivo_salida)

print("\nINTEGRACIÓN FINALIZADA")

