
from pathlib import Path
import os
import hashlib

from dotenv import load_dotenv
from hdfs import InsecureClient

# ==========================================
# 1. CONFIGURACION
# ==========================================

BASE_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BASE_DIR / ".env")

HDFS_URL = os.getenv("HDFS_ADDRESS_CLUSTER")
USUARIO = os.getenv("HDFS_USER")
RUTA_BASE = os.getenv("HDFS_BASE")

if not all((HDFS_URL, USUARIO, RUTA_BASE)):
    raise RuntimeError("Faltan variables HDFS en .env")

# ==========================================
# 2. ARCHIVO DE PRUEBA
# ==========================================

NOMBRE = "ep10b_20261027-201118.csv"

ORIGINAL = BASE_DIR / "data" / "raw" / "eustat" / NOMBRE

RUTA_HDFS = (
    f"{RUTA_BASE.rstrip('/')}/raw/eustat/{NOMBRE}"
)

CARPETA_DESCARGAS = BASE_DIR / "data" / "hdfs_verificacion"
CARPETA_DESCARGAS.mkdir(parents=True, exist_ok=True)

DESCARGADO = CARPETA_DESCARGAS / NOMBRE

# ==========================================
# 3. FUNCION SHA-256
# ==========================================

def calcular_sha256(ruta):
    hash_sha256 = hashlib.sha256()

    with open(ruta, "rb") as archivo:
        for bloque in iter(lambda: archivo.read(65536), b""):
            hash_sha256.update(bloque)

    return hash_sha256.hexdigest()

# ==========================================
# 4. DESCARGAR DESDE HDFS
# ==========================================

if not ORIGINAL.is_file():
    raise FileNotFoundError(f"No existe el original: {ORIGINAL}")

client = InsecureClient(HDFS_URL, user=USUARIO)

print("Descargando archivo desde HDFS...")

client.download(
    RUTA_HDFS,
    str(DESCARGADO),
    overwrite=True
)

print(f"Archivo descargado: {DESCARGADO}")

# ==========================================
# 5. COMPARAR ARCHIVOS
# ==========================================

hash_original = calcular_sha256(ORIGINAL)
hash_descargado = calcular_sha256(DESCARGADO)

print("\n====================================")
print("VERIFICACION DE INTEGRIDAD HDFS")
print("====================================")

print(f"Archivo: {NOMBRE}")
print(f"Tamano original: {ORIGINAL.stat().st_size} bytes")
print(f"Tamano descargado: {DESCARGADO.stat().st_size} bytes")

print(f"\nSHA-256 original:   {hash_original}")
print(f"SHA-256 descargado: {hash_descargado}")

if hash_original == hash_descargado:
    print("\nRESULTADO: VERIFICACION CORRECTA")
    print("Los archivos son identicos.")
else:
    print("\nRESULTADO: ERROR DE INTEGRIDAD")
    raise RuntimeError("Los archivos no coinciden")
