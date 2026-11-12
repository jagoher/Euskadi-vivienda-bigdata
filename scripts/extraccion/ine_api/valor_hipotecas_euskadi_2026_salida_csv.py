import csv
from pathlib import Path

import requests

url = "https://servicios.ine.es/wstempus/js/ES/DATOS_TABLA/76316?nult=12&det=2"

RAIZ_PROYECTO = Path(__file__).resolve().parents[3]
CARPETA_SALIDA = RAIZ_PROYECTO / "data" / "raw" / "ine_api"
ARCHIVO_SALIDA = CARPETA_SALIDA / "datos_hipotecas_pais_vasco_2026.csv"

respuesta = requests.get(url, timeout=60)
respuesta.raise_for_status()

print(respuesta.status_code)

datos = respuesta.json()
filas = []

for dato in datos:
    if "País Vasco" in dato.get("Nombre", ""):
        for d in dato.get("Data", []):
            if d.get("Anyo") == 2026:
                fila = {
                    "Nombre": dato.get("Nombre"),
                    **d,
                }
                filas.append(fila)

# Guardar los datos en CSV
if filas:
    # Obtener todas las columnas disponibles
    columnas = list(dict.fromkeys(
        clave for fila in filas for clave in fila.keys()
    ))

    CARPETA_SALIDA.mkdir(parents=True, exist_ok=True)

    with open(ARCHIVO_SALIDA, "w", newline="", encoding="utf-8-sig") as archivo:
        escritor = csv.DictWriter(
            archivo,
            fieldnames=columnas,
            delimiter=";",
        )
        escritor.writeheader()
        escritor.writerows(filas)

    print(f"CSV generado correctamente: {len(filas)} registros.")
    print(f"Archivo: {ARCHIVO_SALIDA}")
else:
    print("No se han encontrado registros.")
