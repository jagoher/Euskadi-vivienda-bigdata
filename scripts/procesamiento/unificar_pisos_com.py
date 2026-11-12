
from pathlib import Path
import pandas as pd

ORIGEN = Path("data/raw/portales/pisos_com")
DESTINO = Path("data/processed/compraventa_euskadi_pisos_com.csv")

MUNICIPIOS = {
    "1": "Bilbao",
    "2": "Vitoria-Gasteiz",
    "3": "Donostia",
    "4": "Barakaldo",
    "5": "Getxo",
    "6": "Irun",
    "7": "Santurtzi",
    "8": "Portugalete",
    "9": "Basauri",
    "10": "Errenteria",
    "11": "Leioa",
    "12": "Durango",
}

COLUMNAS = [
    "municipio", "id", "zona", "precio",
    "habitaciones", "banos", "m2",
    "lat", "lon", "descripcion", "archivo_origen"
]

tablas = []

for numero, municipio in MUNICIPIOS.items():
    archivos = list(ORIGEN.glob(f"{numero}_pisos_*.csv"))

    if len(archivos) != 1:
        raise ValueError(
            f"Se esperaba un CSV para {municipio}: {archivos}"
        )

    archivo = archivos[0]
    df = pd.read_csv(archivo, dtype={"id": "string"})

    # Conservar la procedencia original
    df["archivo_origen"] = archivo.name
    df["municipio"] = municipio

    # Normalizar columnas
    df = df.reindex(columns=COLUMNAS)
    tablas.append(df)

    print(f"{municipio}: {len(df)} anuncios")

resultado = pd.concat(tablas, ignore_index=True)

DESTINO.parent.mkdir(parents=True, exist_ok=True)
resultado.to_csv(DESTINO, index=False, encoding="utf-8-sig")

print("\nCSV unificado:", DESTINO)
print("Total de anuncios:", len(resultado))
print("Municipios:", resultado["municipio"].nunique())
print("Columnas:", len(resultado.columns))
