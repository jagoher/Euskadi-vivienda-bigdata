import csv
import html
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

base_url = "https://www.pisos.com/venta/pisos-bilbao/"  # con barra final
PAGINAS = 29


def num(patron, textos):
    """Primer número que casa con el patrón en la lista de textos."""
    for t in textos:
        m = re.search(patron, t)
        if m:
            return float(m.group(1).replace(",", "."))
    return None


def extraer_anuncio(a):
    # Precio
    contacto = a.select_one("div.contact-box")
    precio = contacto.get("data-ad-price") if contacto else None
    if not precio:
        p = a.select_one("span.ad-preview__price")
        precio = p.get_text(strip=True) if p else None

    # Descripción
    d = a.select_one("p.ad-preview__description")
    descripcion = d.get_text(" ", strip=True) if d else None

    # Zona y coordenadas desde el JSON-LD
    zona = lat = lon = None
    script = a.select_one('script[type="application/ld+json"]')
    if script and script.string:
        try:
            datos = json.loads(script.string)
            nombre = html.unescape(datos.get("name", ""))
            zona = re.sub(r"^\w+\s+en\s+", "", nombre)
            geo = datos.get("geo", {})
            lat, lon = geo.get("latitude"), geo.get("longitude")
        except json.JSONDecodeError:
            pass

    # Características: "2 habs.", "1 baño", "68 m²", "4ª planta"
    chars = [c.get_text(strip=True) for c in a.select("p.ad-preview__char")]

    return {
        "id": a.get("id"),
        "zona": zona,
        "precio": precio,
        "habitaciones": num(r"(\d+)\s*hab", chars),
        "banos": num(r"(\d+)\s*ba", chars),
        "m2": num(r"(\d+(?:[.,]\d+)?)\s*m", chars),
        "lat": lat,
        "lon": lon,
        "descripcion": descripcion,
    }


pisos = []
vistos = set()

for numero in range(1, PAGINAS + 1):
    url = base_url if numero == 1 else f"{base_url}{numero}/"
    r = requests.get(url, headers=headers, timeout=15)
    r.raise_for_status()

    soup = BeautifulSoup(r.text, "html.parser")
    anuncios = soup.select("div.ad-preview")

    if not anuncios:
        print(f"Pág {numero}: sin anuncios, paro.")
        break

    nuevos = 0
    for a in anuncios:
        piso = extraer_anuncio(a)
        if piso["id"] in vistos:
            continue
        vistos.add(piso["id"])
        pisos.append(piso)
        nuevos += 1

    print(f"Pág {numero}: {len(anuncios)} anuncios, {nuevos} nuevos "
          f"(total {len(pisos)}) -> {r.url}")
    time.sleep(2)

for p in pisos[:3]:
    print(p)

campos = ["id", "zona", "precio", "habitaciones", "banos", "m2",
          "lat", "lon", "descripcion"]
with open(RUTA_SALIDA, "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=campos)
    w.writeheader()
    w.writerows(pisos)