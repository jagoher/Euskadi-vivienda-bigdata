"""Scraping de anuncios de venta en Donostia (pisos.com).

Guarda un CSV nuevo en data/raw/portales/pisos_com/,
sin sobrescribir el dataset anterior.

Uso: python 3_pisos_donostia_corregido.py
Requiere: requests, beautifulsoup4
"""

import csv
import html
import json
import re
import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup


# ==========================================
# CONFIGURACIÓN
# ==========================================

BASE_URL = "https://www.pisos.com/venta/pisos-san_sebastian_donostia/"
PAGINAS = 20
MUNICIPIO = "Donostia"

# Ruta absoluta desde la ubicación del script
# Supone: scripts/extraccion/pisos_com/
RAIZ_PROYECTO = Path(__file__).resolve().parents[3]

CARPETA_SALIDA = (
    RAIZ_PROYECTO / "data" / "raw" / "portales" / "pisos_com"
)

SALIDA = CARPETA_SALIDA / "3_pisos_donostia.csv"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/json,*/*",
}

CAMPOS = [
    "municipio",
    "id",
    "zona",
    "precio",
    "habitaciones",
    "banos",
    "m2",
    "lat",
    "lon",
    "descripcion",
]


# ==========================================
# CONVERSIÓN DE NÚMEROS
# ==========================================

def convertir_numero(texto):
    """Convierte números españoles a valores numéricos.

    Ejemplos:
        1.495 -> 1495
        68,5 -> 68.5

    Un punto con exactamente tres dígitos posteriores
    se interpreta como separador de miles.
    """

    valor = texto.strip().replace(" ", "").replace("\u00a0", "")

    if "." in valor and "," in valor:
        if valor.rfind(",") > valor.rfind("."):
            valor = valor.replace(".", "").replace(",", ".")
        else:
            valor = valor.replace(",", "")

    elif re.fullmatch(r"\d{1,3}(?:\.\d{3})+", valor):
        valor = valor.replace(".", "")

    elif re.fullmatch(r"\d{1,3}(?:,\d{3})+", valor):
        valor = valor.replace(",", "")

    else:
        valor = valor.replace(",", ".")

    return float(valor)


def num(patron, textos):
    """Busca y convierte un número dentro de una lista de textos."""

    for texto in textos:
        match = re.search(patron, texto, flags=re.IGNORECASE)

        if match:
            try:
                return convertir_numero(match.group(1))
            except ValueError:
                pass

    return None


# ==========================================
# EXTRACCIÓN DE ANUNCIOS
# ==========================================

def extraer_anuncio(a):
    """Extrae los datos de un anuncio HTML de pisos.com."""

    # Precio
    contacto = a.select_one("div.contact-box")
    precio = contacto.get("data-ad-price") if contacto else None

    if not precio:
        elemento_precio = a.select_one("span.ad-preview__price")
        precio = (
            elemento_precio.get_text(" ", strip=True)
            if elemento_precio
            else None
        )

    if precio is not None:
        encontrado = re.search(r"\d[\d.,\s\u00a0]*", str(precio))
        precio = (
            int(convertir_numero(encontrado.group(0)))
            if encontrado
            else None
        )

    # Descripción
    descripcion_tag = a.select_one("p.ad-preview__description")
    descripcion = (
        descripcion_tag.get_text(" ", strip=True)
        if descripcion_tag
        else None
    )

    # Zona y coordenadas
    zona = lat = lon = None

    script = a.select_one('script[type="application/ld+json"]')

    if script:
        contenido = script.string or script.get_text()

        if contenido:
            try:
                datos = json.loads(contenido)

                if isinstance(datos, list):
                    datos = next(
                        (
                            d for d in datos
                            if isinstance(d, dict) and d.get("name")
                        ),
                        {},
                    )

                if isinstance(datos, dict):
                    nombre = html.unescape(str(datos.get("name", "")))

                    zona = re.sub(
                        r"^\w+\s+en\s+",
                        "",
                        nombre,
                        flags=re.IGNORECASE,
                    )

                    geo = datos.get("geo") or {}

                    if isinstance(geo, dict):
                        lat = geo.get("latitude")
                        lon = geo.get("longitude")

            except (json.JSONDecodeError, TypeError):
                pass

    # Características
    chars = [
        c.get_text(" ", strip=True)
        for c in a.select("p.ad-preview__char")
    ]

    return {
        "municipio": MUNICIPIO,
        "id": a.get("id"),
        "zona": zona,
        "precio": precio,
        "habitaciones": num(r"(\d+)\s*hab", chars),
        "banos": num(r"(\d+)\s*ba", chars),
        "m2": num(r"(\d[\d.,]*)\s*m(?:²|2|\b)", chars),
        "lat": lat,
        "lon": lon,
        "descripcion": descripcion,
    }


# ==========================================
# PROGRAMA PRINCIPAL
# ==========================================

def main():
    """Descarga anuncios y los guarda en un archivo CSV."""

    sesion = requests.Session()
    sesion.headers.update(HEADERS)

    pisos = []
    vistos = set()

    for pagina in range(1, PAGINAS + 1):

        url = (
            BASE_URL
            if pagina == 1
            else BASE_URL + f"{pagina}/"
        )

        print(f"Página {pagina}: {url}", flush=True)

        try:
            respuesta = sesion.get(url, timeout=20)
            respuesta.raise_for_status()

        except requests.RequestException as exc:
            print(
                f"Error al descargar: {exc}. "
                "Se detiene la extracción."
            )
            break

        soup = BeautifulSoup(respuesta.text, "html.parser")
        anuncios = soup.select("div.ad-preview")

        if not anuncios:
            print(
                "No se encontraron anuncios con el selector "
                "div.ad-preview. Se detiene."
            )
            break

        nuevos = 0

        for anuncio in anuncios:
            piso = extraer_anuncio(anuncio)

            # Evitar anuncios duplicados
            clave = piso["id"] or (
                "sin_id",
                piso["zona"],
                piso["precio"],
                piso["descripcion"],
            )

            if clave in vistos:
                continue

            vistos.add(clave)
            pisos.append(piso)
            nuevos += 1

        print(
            f"  Anuncios encontrados: {len(anuncios)} "
            f"| nuevos: {nuevos}",
            flush=True,
        )

        if nuevos == 0:
            print(
                "La paginación no aporta anuncios nuevos. "
                "Se detiene."
            )
            break

        if pagina < PAGINAS:
            time.sleep(2)

    # ==========================================
    # GUARDADO DEL CSV
    # ==========================================

    if not pisos:
        print("No se obtuvo ningún anuncio; no se crea CSV.")
        return

    # Crear carpeta de salida si no existe
    SALIDA.parent.mkdir(parents=True, exist_ok=True)

    # Evitar sobrescribir el CSV anterior
    if SALIDA.exists():
        print(f"El archivo {SALIDA} ya existe. No se sobrescribe.")
        return

    with SALIDA.open(
        "w",
        newline="",
        encoding="utf-8-sig",
    ) as archivo:

        escritor = csv.DictWriter(
            archivo,
            fieldnames=CAMPOS,
        )

        escritor.writeheader()
        escritor.writerows(pisos)

    print(f"Guardados {len(pisos)} anuncios en {SALIDA.resolve()}")

    print(
        "Revisa los datos: el portal puede cambiar su HTML "
        "y las cifras ambiguas requieren validación."
    )


if __name__ == "__main__":
    main()