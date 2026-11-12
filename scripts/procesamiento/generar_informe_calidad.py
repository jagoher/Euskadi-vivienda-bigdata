
from pathlib import Path
from datetime import datetime
import pandas as pd

BASE = Path("data/processed")
RESULTADOS = Path("resultados")
RESULTADOS.mkdir(parents=True, exist_ok=True)

archivos = {
    "Catalogo municipios": "catalogo_municipios_euskadi_2026.csv",
    "Vivienda oficial": "vivienda_euskadi_municipios_integrado.csv",
    "Anuncios clasificados": "compraventa_euskadi_clasificado_v3.csv",
    "Salarios juveniles": "salarios_juveniles_euskadi.csv",
    "Alquiler API": "alquiler_euskadi_provincias.csv",
    "Economia juvenil": "economia_juvenil_euskadi.csv",
    "Esfuerzo alquiler": "esfuerzo_alquiler_juvenil_municipios_2024.csv",
    "Accesibilidad compra": "accesibilidad_compra_juvenil_municipios.csv",
    "Indicadores finales": "indicadores_vivienda_juvenil_euskadi.csv"
}

resumen = []
detalle = []

for nombre, archivo in archivos.items():
    ruta = BASE / archivo

    if not ruta.exists():
        print("NO ENCONTRADO:", ruta)
        continue

    df = pd.read_csv(
        ruta,
        dtype={"codigo_ine": str, "id": str}
    )

    nulos = int(df.isna().sum().sum())
    duplicados = int(df.duplicated().sum())

    resumen.append({
        "dataset": nombre,
        "archivo": archivo,
        "filas": len(df),
        "columnas": len(df.columns),
        "celdas_nulas": nulos,
        "filas_duplicadas": duplicados
    })

    detalle.append(f"### {nombre}\n")
    detalle.append(f"- Archivo: `{archivo}`")
    detalle.append(f"- Registros: {len(df)}")
    detalle.append(f"- Columnas: {len(df.columns)}")
    detalle.append(f"- Celdas nulas: {nulos}")
    detalle.append(f"- Filas completamente duplicadas: {duplicados}")

    if "codigo_ine" in df.columns:
        detalle.append(
            f"- Codigos INE unicos: {df['codigo_ine'].nunique()}"
        )

    if "id" in df.columns:
        detalle.append(
            f"- IDs de anuncio unicos: {df['id'].nunique()}"
        )

    detalle.append("\n")

tabla = pd.DataFrame(resumen)

salida_csv = RESULTADOS / "resumen_calidad_etl.csv"
tabla.to_csv(salida_csv, index=False, encoding="utf-8-sig")

informe = [
    "# Informe de calidad del ETL",
    "",
    "## Proyecto EUSKADI_VIVIENDA_BIGDATA",
    "",
    f"Fecha de generacion: {datetime.now():%Y-%m-%d}",
    "",
    "## 1. Objetivo",
    "",
    "Integrar datos oficiales, datos obtenidos mediante API "
    "y anuncios inmobiliarios para analizar la accesibilidad "
    "a la vivienda de la poblacion joven en Euskadi.",
    "",
    "## 2. Fuentes y datasets procesados",
    "",
    tabla.to_markdown(index=False),
    "",
    "## 3. Validaciones por dataset",
    "",
    *detalle,
    "## 4. Transformaciones principales",
    "",
    "- Normalizacion de municipios y codigos INE.",
    "- Integracion de fuentes oficiales de alquiler y compraventa.",
    "- Limpieza y clasificacion de anuncios inmobiliarios.",
    "- Deduplicacion de anuncios mediante identificador.",
    "- Conservacion de registros pendientes de revision.",
    "- Integracion de salarios juveniles por territorio.",
    "- Calculo del esfuerzo economico de alquiler.",
    "- Calculo de anos de salario equivalentes al precio de compra.",
    "- Integracion final de indicadores municipales.",
    "",
    "## 5. Limitaciones metodologicas",
    "",
    "- No todos los municipios tienen precios oficiales publicados.",
    "- Los anuncios representan precios de oferta, no ventas cerradas.",
    "- Los salarios territoriales no representan salarios municipales.",
    "- El alquiler de referencia corresponde a 2024.",
    "- Los precios de compraventa corresponden a 2025.",
    "- Existen anuncios pendientes de revision manual.",
    "- Las fuentes INE y Registradores se mantienen separadas.",
    "",
    "## 6. Interpretacion de valores nulos",
    "",
    "Los valores ausentes se conservan como nulos. "
    "No se sustituyen por cero ni por medias municipales "
    "sin una justificacion metodologica.",
    ""
]

salida_md = RESULTADOS / "informe_calidad_etl.md"
salida_md.write_text(
    "\n".join(informe),
    encoding="utf-8"
)

print("INFORME DE CALIDAD ETL")
print("======================")
print("Datasets procesados:", len(tabla))
print("Total registros por dataset:", tabla["filas"].sum())
print("Informe:", salida_md)
print("Resumen:", salida_csv)
print("\nDETALLE:")
print(tabla.to_string(index=False))
