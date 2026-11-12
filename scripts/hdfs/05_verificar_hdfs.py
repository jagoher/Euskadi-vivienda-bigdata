
from pathlib import Path
import os

from dotenv import load_dotenv
from hdfs import InsecureClient

BASE_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BASE_DIR / ".env")

url = os.getenv("HDFS_ADDRESS_CLUSTER")
usuario = os.getenv("HDFS_USER")
base = os.getenv("HDFS_BASE")

if not all((url, usuario, base)):
    raise RuntimeError("Faltan variables HDFS en .env")

client = InsecureClient(url, user=usuario)

carpetas = {
    "raw": ".csv",
    "processed": ".csv",
    "mongodb": ".json"
}

total = 0
errores = 0

for carpeta, extension in carpetas.items():

    local = BASE_DIR / "data" / carpeta
    remoto = f"{base.rstrip('/')}/{carpeta}"

    archivos = sorted(
        p for p in local.rglob("*")
        if p.is_file() and p.suffix.lower() == extension
    )

    print(f"\nCARPETA: {carpeta}")

    correctos = 0

    for archivo in archivos:
        relativa = archivo.relative_to(local).as_posix()
        ruta_hdfs = f"{remoto}/{relativa}"

        try:
            estado = client.status(ruta_hdfs)
            tamano_local = archivo.stat().st_size
            tamano_hdfs = estado["length"]

            if tamano_local == tamano_hdfs:
                correctos += 1
            else:
                print(f"TAMANO DISTINTO: {relativa}")
                errores += 1

        except Exception as e:
            print(f"ERROR: {relativa}: {e}")
            errores += 1

    total += correctos
    print(f"Archivos verificados: {correctos}/{len(archivos)}")

print("\n============================")
print("RESUMEN FINAL HDFS")
print("============================")
print(f"Archivos verificados: {total}")
print(f"Errores: {errores}")

if errores == 0:
    print("VERIFICACION CORRECTA")
else:
    print("REVISAR ARCHIVOS")
