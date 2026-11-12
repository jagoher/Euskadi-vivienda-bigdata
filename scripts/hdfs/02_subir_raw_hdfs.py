
from pathlib import Path
import os

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
    raise RuntimeError("Faltan variables de HDFS en .env")

# ==========================================
# 2. CARPETAS ORIGEN Y DESTINO
# ==========================================

ORIGEN = BASE_DIR / "data" / "raw"
DESTINO = f"{RUTA_BASE.rstrip('/')}/raw"

if not ORIGEN.is_dir():
    raise FileNotFoundError(f"No existe: {ORIGEN}")

archivos = sorted(ORIGEN.rglob("*.csv"))

print(f"Archivos CSV encontrados: {len(archivos)}")

if not archivos:
    raise RuntimeError("No se encontraron archivos CSV")

# ==========================================
# 3. CONEXION Y SUBIDA
# ==========================================

client = InsecureClient(HDFS_URL, user=USUARIO)

subidos = 0
errores = 0

for archivo in archivos:
    # Conservar subcarpetas si las hubiera
    relativa = archivo.relative_to(ORIGEN).as_posix()
    ruta_hdfs = f"{DESTINO}/{relativa}"

    try:
        client.upload(
            ruta_hdfs,
            str(archivo),
            overwrite=True
        )

        print(f"SUBIDO: {relativa}")
        subidos += 1

    except Exception as e:
        print(f"ERROR en {relativa}: {e}")
        errores += 1

# ==========================================
# 4. RESUMEN
# ==========================================

print("\nRESULTADO")
print(f"CSV encontrados: {len(archivos)}")
print(f"Subidos: {subidos}")
print(f"Errores: {errores}")
