
import requests
import pandas as pd
from bs4 import BeautifulSoup
from pathlib import Path

# ==========================================
# 1. CONFIGURACIÓN
# ==========================================

URL = "https://es.eustat.eus/alquiler_vivienda.html"

# Carpeta principal del proyecto
PROYECTO = Path(__file__).resolve().parents[2]

# Carpetas de destino
CARPETA_RAW = PROYECTO / "data" / "raw" / "eustat"
CARPETA_PROCESSED = PROYECTO / "data" / "processed"

CARPETA_RAW.mkdir(parents=True, exist_ok=True)
CARPETA_PROCESSED.mkdir(parents=True, exist_ok=True)

ARCHIVO_HTML = CARPETA_RAW / "eustat_alquiler_original.html"
ARCHIVO_CSV = CARPETA_PROCESSED / "alquiler_municipios_eustat.csv"


# ==========================================
# 2. DESCARGAR HTML DE EUSTAT
# ==========================================

print("Conectando con Eustat...")

respuesta = requests.get(URL, timeout=30)
respuesta.raise_for_status()

# Guardar HTML original
ARCHIVO_HTML.write_bytes(respuesta.content)

print("HTML descargado correctamente.")
print("Guardado en:", ARCHIVO_HTML)


# ==========================================
# 3. WEB SCRAPING CON BEAUTIFULSOUP
# ==========================================

soup = BeautifulSoup(respuesta.content, "html.parser")

tablas = soup.find_all("table")

if not tablas:
    raise ValueError("No se encontraron tablas en la página de Eustat.")

tabla = tablas[0]

columnas = [
    "municipio",
    "renta_m2_media",
    "renta_m2_mediana",
    "renta_m2_p25",
    "renta_m2_p75",
    "alquiler_medio",
    "alquiler_mediana",
    "alquiler_p25",
    "alquiler_p75",
    "superficie_media",
    "superficie_mediana",
    "superficie_p25",
    "superficie_p75"
]

excluidos = {
    "C.A. de Euskadi",
    "Territorios Históricos",
    "Araba/Álava",
    "Bizkaia",
    "Gipuzkoa",
    "Municipios"
}

normalizar = {
    "Munitibar-Arbatzegi Gerrikaitz-": "Munitibar -Arbatzegi Gerrikaitz-",
    "Sopelana": "Sopela",
    "Urduña/Orduña": "Urduña-Orduña"
}

registros = []

for fila in tabla.find_all("tr"):

    celdas = fila.find_all(["th", "td"])
    valores = [c.get_text(" ", strip=True) for c in celdas]

    if len(valores) != 13:
        continue

    nombre = valores[0].strip()

    if not nombre or nombre in excluidos:
        continue

    valores[0] = normalizar.get(nombre, nombre)

    registros.append(valores)


# ==========================================
# 4. CREAR DATAFRAME
# ==========================================

df = pd.DataFrame(registros, columns=columnas)

print("\nDatos extraídos correctamente.")


# ==========================================
# 5. LIMPIEZA Y TRANSFORMACIÓN
# ==========================================

for columna in columnas[1:]:

    df[columna] = (
        df[columna]
        .str.replace(".", "", regex=False)
        .str.replace(",", ".", regex=False)
        .replace({":": None, "": None})
    )

    df[columna] = pd.to_numeric(
        df[columna],
        errors="coerce"
    )


# ==========================================
# 6. GUARDAR CSV PROCESADO
# ==========================================

df.to_csv(
    ARCHIVO_CSV,
    index=False,
    encoding="utf-8-sig"
)

print("\nCSV generado correctamente.")
print("Guardado en:", ARCHIVO_CSV)


# ==========================================
# 7. VALIDACIÓN DE LOS DATOS
# ==========================================

print("\n========== VALIDACIÓN ==========")

print("Municipios:", len(df))

print(
    "Municipios distintos:",
    df["municipio"].nunique()
)

print(
    "Duplicados:",
    df.duplicated("municipio").sum()
)

print(
    "Con alquiler medio disponible:",
    df["alquiler_medio"].notna().sum()
)

print(
    "Sin alquiler medio disponible:",
    df["alquiler_medio"].isna().sum()
)

print("\nDatos de Usansolo:")

print(
    df.loc[
        df["municipio"] == "Usansolo",
        ["municipio", "alquiler_medio", "renta_m2_media"]
    ]
)

print("\nProceso de web scraping finalizado.")
