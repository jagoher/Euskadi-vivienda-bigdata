
import json
import pandas as pd
from pathlib import Path

# ==========================================
# 1. CONFIGURACIÓN
# ==========================================

PROYECTO = Path(__file__).resolve().parents[2]

CARPETA_RAW = PROYECTO / "data" / "raw" / "observatorio_alquiler"
CARPETA_PROCESSED = PROYECTO / "data" / "processed"

ARCHIVO_SALIDA = CARPETA_PROCESSED / "alquiler_euskadi_provincias.csv"

provincias = {
    "alava.json": "Álava",
    "guipuzcoa.json": "Guipúzcoa",
    "vizcaya.json": "Vizcaya"
}

# ==========================================
# 2. LEER LOS JSON
# ==========================================

registros = []

for archivo, provincia in provincias.items():

    ruta = CARPETA_RAW / archivo

    with open(ruta, "r", encoding="utf-8") as f:
        datos = json.load(f)

    if datos.get("ok") is not True:
        raise ValueError(f"Respuesta API no válida: {archivo}")

    serie = datos.get("series")

    if not isinstance(serie, list) or not serie:
        raise ValueError(f"Serie vacía o inválida: {archivo}")

    for elemento in serie:

        registros.append({
            "provincia": provincia,
            "periodo": elemento.get("period"),
            "presion": elemento.get("pressure"),
            "oferta": elemento.get("offer"),
            "precio": elemento.get("price")
        })

    print(f"{provincia}: {len(serie)} registros")

# ==========================================
# 3. CREAR Y VALIDAR DATAFRAME
# ==========================================

df = pd.DataFrame(registros)

if df.duplicated(["provincia", "periodo"]).any():
    raise ValueError("Existen provincias y periodos duplicados")

if df[["provincia", "periodo"]].isna().any().any():
    raise ValueError("Hay provincias o periodos sin identificar")

for columna in ["presion", "oferta", "precio"]:
    df[columna] = pd.to_numeric(df[columna], errors="coerce")

df = df.sort_values(
    ["provincia", "periodo"]
).reset_index(drop=True)

# ==========================================
# 4. GUARDAR CSV
# ==========================================

CARPETA_PROCESSED.mkdir(parents=True, exist_ok=True)

df.to_csv(
    ARCHIVO_SALIDA,
    index=False,
    encoding="utf-8-sig"
)

# ==========================================
# 5. RESULTADOS
# ==========================================

print("\n========== VALIDACIÓN ==========")

print("Registros totales:", len(df))
print("Duplicados:", df.duplicated(["provincia", "periodo"]).sum())

print("\nValores ausentes:")
print(df.isna().sum())

print("\nRegistros por provincia:")
print(df.groupby("provincia").size())

print("\nCSV generado:", ARCHIVO_SALIDA)
