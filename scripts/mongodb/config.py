import os
from pathlib import Path
from dotenv import load_dotenv

# --------------------------------------------------
# RUTAS DEL PROYECTO
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parents[2]

DATA_DIR = BASE_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
MONGODB_DIR = DATA_DIR / "mongodb"

RESULTADOS_DIR = BASE_DIR / "resultados"
DOCS_DIR = BASE_DIR / "docs"


# --------------------------------------------------
# VARIABLES DE ENTORNO
# --------------------------------------------------

load_dotenv(BASE_DIR / ".env")

MONGODB_URI = os.getenv(
    "MONGODB_URI",
    "mongodb://localhost:27017/"
)

DATABASE_NAME = os.getenv(
    "DATABASE_NAME",
    "EUSKADI_VIVIENDA_BIGDATA"
)


# --------------------------------------------------
# COLECCIONES DE MONGODB
# --------------------------------------------------

COLLECTIONS = {
    "municipios": "municipios",
    "anuncios": "anuncios",
    "alquiler": "mercado_alquiler",
    "salarios": "salarios",
    "economia": "economia_juvenil"
}
