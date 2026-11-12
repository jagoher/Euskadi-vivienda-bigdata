
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

RUTA_BASE = RUTA_BASE.rstrip("/")

# Evitar borrar rutas fuera del proyecto
RUTA_ESPERADA = f"/user/{USUARIO}/euskadi_vivienda"

if RUTA_BASE != RUTA_ESPERADA:
    raise RuntimeError("Ruta HDFS inesperada. Operacion cancelada.")

client = InsecureClient(HDFS_URL, user=USUARIO)

# ==========================================
# 2. MOSTRAR ARCHIVOS
# ==========================================

carpetas = ["raw", "processed", "mongodb"]
archivos_a_borrar = []

for carpeta in carpetas:
    ruta = f"{RUTA_BASE}/{carpeta}"

    for directorio, _, archivos in client.walk(ruta):
        for archivo in archivos:
            archivos_a_borrar.append(
                f"{directorio.rstrip('/')}/{archivo}"
            )

print(f"Archivos encontrados: {len(archivos_a_borrar)}")

for archivo in archivos_a_borrar:
    print(archivo)

# ==========================================
# 3. CONFIRMACION
# ==========================================

confirmacion = input(
    "\nEscribe BORRAR para eliminar estos archivos: "
)

if confirmacion != "BORRAR":
    print("Operacion cancelada.")
    raise SystemExit(0)

# ==========================================
# 4. ELIMINAR ARCHIVOS
# ==========================================

eliminados = 0

for archivo in archivos_a_borrar:
    if client.delete(archivo):
        eliminados += 1
        print(f"ELIMINADO: {archivo}")
    else:
        print(f"NO ELIMINADO: {archivo}")

print("\nRESULTADO")
print(f"Archivos encontrados: {len(archivos_a_borrar)}")
print(f"Archivos eliminados: {eliminados}")

# ==========================================
# 5. COMPROBAR CARPETAS
# ==========================================

for carpeta in carpetas:
    ruta = f"{RUTA_BASE}/{carpeta}"
    restantes = sum(
        len(archivos)
        for _, _, archivos in client.walk(ruta)
    )
    print(f"{carpeta}: {restantes} archivos restantes")
