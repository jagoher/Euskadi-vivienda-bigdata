import csv
import json
import re
import time
import requests
from bs4 import BeautifulSoup
from pathlib import Path

# Ruta del proyecto
RAIZ_PROYECTO = Path(__file__).resolve().parents[3]
RUTA_SALIDA = RAIZ_PROYECTO / "data" / "raw" / "portales" / "pisos_com" / "1_pisos_bilbao.csv"

# Crear la carpeta si no existe
RUTA_SALIDA.parent.mkdir(parents=True, exist_ok=True)


headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/131.0.0.0 Safari/537.36",
    "Accept": "text/html,application/json,*/*"
}

base_url = "https://www.pisos.com/venta/pisos-bilbao/"


def extraer_anuncio(a):
    # Precio: primero el atributo numérico, si no, el texto del span
    contacto = a.select_one("div.contact-box")
    precio = contacto.get("data-ad-price") if contacto else None
    if not precio:
        p = a.select_one("span.ad-preview__price")
        precio = p.get_text(strip=True) if p else None

    # Descripción
    d = a.select_one("p.ad-preview__description")
    descripcion = d.get_text(" ", strip=True) if d else None

    # Zona: del JSON-LD ("Piso en Casco Viejo - Zazpi Kaleak")
    zona = None
    script = a.select_one('script[type="application/ld+json"]')
    if script:
        try:
            nombre = json.loads(script.string).get("name", "")
            zona = re.sub(r"^\w+\s+en\s+", "", nombre)  # quita "Piso en "
        except (json.JSONDecodeError, TypeError):
            pass

    return {"zona": zona, "precio": precio, "descripcion": descripcion}


pisos = []

for numero in range(1, 30):
    url = base_url if numero == 1 else f"{base_url}{numero}/"
    r = requests.get(url, headers=headers, timeout=15)
    r.raise_for_status()

    soup = BeautifulSoup(r.text, "html.parser")
    anuncios = soup.select("div.ad-preview")

    if not anuncios:
        print(f"Pág {numero}: sin anuncios, paro.")
        break

    pisos.extend(extraer_anuncio(a) for a in anuncios)
    print(f"Pág {numero}: {len(anuncios)} anuncios (total {len(pisos)})")
    time.sleep(2)

for p in pisos[:5]:
    print(p)

with open(RUTA_SALIDA, "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=["zona", "precio", "descripcion"])
    w.writeheader()
    w.writerows(pisos)