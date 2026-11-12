import csv
import re
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

import requests

URL = "https://servicios.ine.es/wstempus/js/es/DATOS_TABLA/69330?tip=AM"
RAIZ_PROYECTO = Path(__file__).resolve().parents[3]
CARPETA_SALIDA = RAIZ_PROYECTO / "data" / "raw" / "ine_api"
ARCHIVO = CARPETA_SALIDA / "indicadores_vivienda_euskadi.csv"
ANYOS = {2024, 2025}

INDICADORES = ["precio medio", "alquiler mensual medio"]

MUNICIPIOS_EUSKADI = [
    "Vitoria-Gasteiz", "Barakaldo", "Basauri", "Bilbao",
    "Durango", "Erandio", "Galdakao", "Getxo", "Leioa",
    "Portugalete", "Santurtzi", "Sestao", "Arrasate",
    "Donostia", "Eibar", "Errenteria", "Hernani",
    "Irun", "Tolosa", "Zarautz",
]


def normalizar(texto):
    """Minúsculas y sin tildes: 'Irún' -> 'irun'."""
    texto = unicodedata.normalize("NFD", texto or "")
    texto = "".join(c for c in texto if unicodedata.category(c) != "Mn")
    return texto.lower()


MUNICIPIOS_NORM = {normalizar(m): m for m in MUNICIPIOS_EUSKADI}


def buscar_municipio(nombre_serie):
    """Devuelve el municipio de Euskadi que aparece en el nombre, o None."""
    n = normalizar(nombre_serie)
    for clave, original in MUNICIPIOS_NORM.items():
        if re.search(rf"\b{re.escape(clave)}\b", n):
            return original
    return None


def fecha_legible(valor):
    """Acepta milisegundos (int/float) o texto tipo ISO; devuelve YYYY-MM-DD."""
    if valor is None or valor == "":
        return None
    # Milisegundos desde 1970 (número o número en texto)
    try:
        ms = float(valor)
        return datetime.fromtimestamp(ms / 1000, tz=timezone.utc).strftime("%Y-%m-%d")
    except (TypeError, ValueError):
        pass
    # Texto ISO, p. ej. "2024-01-01T00:00:00.000+01:00"
    try:
        return datetime.fromisoformat(str(valor).replace("Z", "+00:00")).strftime("%Y-%m-%d")
    except ValueError:
        return str(valor)  # si no se reconoce, lo dejo tal cual


respuesta = requests.get(URL, timeout=60)
respuesta.raise_for_status()
datos = respuesta.json()
print("Número de series:", len(datos))

filas = []
for serie in datos:
    nombre = serie.get("Nombre", "")
    nombre_norm = normalizar(nombre)

    indicador = next((i for i in INDICADORES if i in nombre_norm), None)
    if not indicador:
        continue

    municipio = buscar_municipio(nombre)
    if not municipio:
        continue

    for reg in serie.get("Data", []):
        if reg.get("Anyo") not in ANYOS:
            continue
        filas.append({
            "municipio": municipio,
            "indicador": indicador,
            "anyo": reg.get("Anyo"),
            "periodo": reg.get("NombrePeriodo") or reg.get("FK_Periodo"),
            "fecha": fecha_legible(reg.get("Fecha")),
            "valor": reg.get("Valor"),
            "secreto": reg.get("Secreto"),
            "unidad_id": serie.get("FK_Unidad"),
            "cod_serie": serie.get("COD"),
            "serie": nombre,
        })

if not filas:
    print("No se encontraron filas. Ejemplos de nombres de serie para ajustar filtros:")
    for s in datos[:10]:
        print(" -", s.get("Nombre"))
else:
    filas.sort(key=lambda f: (f["indicador"], f["municipio"], f["anyo"], str(f["periodo"])))
    CARPETA_SALIDA.mkdir(parents=True, exist_ok=True)
    with open(ARCHIVO, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(filas[0].keys()))
        w.writeheader()
        w.writerows(filas)
    print(f"Guardadas {len(filas)} filas en {ARCHIVO}")