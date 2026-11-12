import json
from pathlib import Path

import requests

URL = "https://servicios.ine.es/wstempus/js/ES/DATOS_TABLA/6150?tip=AM&nult=12"

RAIZ_PROYECTO = Path(__file__).resolve().parents[3]
CARPETA_SALIDA = RAIZ_PROYECTO / "data" / "raw" / "ine_api"
ARCHIVO_SALIDA = CARPETA_SALIDA / "datos_euskadi_total_viviendas.json"

respuesta = requests.get(URL, timeout=60)
respuesta.raise_for_status()
datos = respuesta.json()

resultados = []

for dato in datos:
    nombre = dato["Nombre"].lower()

    if any(lugar in nombre for lugar in [
        "país vasco", "álava", "araba",
        "guipúzcoa", "gipuzkoa", "vizcaya", "bizkaia"
    ]):
        print(dato)
        resultados.append(dato)

CARPETA_SALIDA.mkdir(parents=True, exist_ok=True)

with open(ARCHIVO_SALIDA, "w", encoding="utf-8") as archivo:
    json.dump(resultados, archivo, ensure_ascii=False, indent=4)

print(f"Guardados {len(resultados)} registros en {ARCHIVO_SALIDA}")
