
from pathlib import Path
import json
import requests

# URL de la API del Observatorio del Alquiler
BASE_URL = (
    "https://barometro-admin.barometro-alquiler-admin.workers.dev"
    "/api/chart-data/provincia"
)

# Provincias de Euskadi
provincias = ["vizcaya", "alava", "guipuzcoa"]

# Carpeta raíz del proyecto
PROYECTO = Path(__file__).resolve().parents[2]

# Carpeta donde guardaremos los datos originales
carpeta = PROYECTO / "data" / "raw" / "observatorio_alquiler"
carpeta.mkdir(parents=True, exist_ok=True)

# Descargar datos de cada provincia
for provincia in provincias:

    url = f"{BASE_URL}/{provincia}"
    archivo = carpeta / f"{provincia}.json"

    print(f"\nDescargando datos de {provincia}...")

    try:
        respuesta = requests.get(url, timeout=30)
        respuesta.raise_for_status()

        datos = respuesta.json()

        with open(archivo, "w", encoding="utf-8") as f:
            json.dump(datos, f, ensure_ascii=False, indent=4)

        print(f"OK: {archivo.name}")

    except (requests.RequestException, ValueError, OSError) as error:
        print(f"ERROR en {provincia}: {error}")

print("\nProceso de descarga finalizado.")
