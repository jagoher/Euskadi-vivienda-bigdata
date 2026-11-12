
from pathlib import Path
import os

from dotenv import load_dotenv
from hdfs import InsecureClient

# ==========================================
# 1. LEER CONFIGURACION DESDE .ENV
# ==========================================

BASE_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BASE_DIR / ".env")

HDFS_URL = os.getenv("HDFS_ADDRESS_CLUSTER")
USUARIO = os.getenv("HDFS_USER")
RUTA_BASE = os.getenv("HDFS_BASE")

if not all((HDFS_URL, USUARIO, RUTA_BASE)):
    raise RuntimeError(
        "Faltan variables en .env: "
        "HDFS_ADDRESS_CLUSTER, HDFS_USER o HDFS_BASE"
    )

if not RUTA_BASE.startswith(f"/user/{USUARIO}/"):
    raise ValueError(
        "HDFS_BASE no corresponde a HDFS_USER"
    )

# ==========================================
# 2. CONECTAR CON HDFS
# ==========================================

# InsecureClient no necesita PASSWORD_CLUSTER
client = InsecureClient(
    HDFS_URL,
    user=USUARIO
)

# ==========================================
# 3. CREAR CARPETAS
# ==========================================

try:
    for carpeta in ["raw", "processed", "mongodb"]:
        ruta = f"{RUTA_BASE.rstrip('/')}/{carpeta}"

        client.makedirs(ruta)
        print(f"Carpeta creada o existente: {ruta}")

    # ======================================
    # 4. COMPROBAR ESTRUCTURA
    # ======================================

    print("\nContenido del proyecto en HDFS:")
    print(client.list(RUTA_BASE))

except Exception as e:
    print(f"Error al acceder a HDFS: {e}")
    raise
