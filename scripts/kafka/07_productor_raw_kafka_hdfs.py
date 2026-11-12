
from pathlib import Path
from dotenv import load_dotenv
from confluent_kafka import Producer

import os
import json
import base64
import hashlib
import uuid
import time
import math

# ==========================================
# 1. CONFIGURACION
# ==========================================

BASE_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BASE_DIR / ".env")

KAFKA_SERVERS = os.getenv("BOOTSTRAP_SERVERS")
TOPIC = os.getenv("KAFKA_HDFS_TOPIC")

if not KAFKA_SERVERS or not TOPIC:
    raise RuntimeError(
        "Faltan BOOTSTRAP_SERVERS o "
        "KAFKA_HDFS_TOPIC en .env"
    )

RAW_DIR = BASE_DIR / "data" / "raw"

# Fragmentos de 128 KiB
CHUNK_SIZE = 128 * 1024

# True: enviar solamente el archivo de prueba
# False: enviar todos los archivos de data/raw
MODO_PRUEBA = False

# Archivo grande para comprobar fragmentacion
ARCHIVO_PRUEBA = RAW_DIR / "ine" / "34010210.xls"

if not RAW_DIR.is_dir():
    raise FileNotFoundError(
        f"No existe la carpeta: {RAW_DIR}"
    )

# ==========================================
# 2. INVENTARIO DE ARCHIVOS
# ==========================================

archivos = sorted(
    archivo
    for archivo in RAW_DIR.rglob("*")
    if archivo.is_file()
)

if not archivos:
    raise RuntimeError(
        "No se encontraron archivos en data/raw"
    )

tamano_total = sum(
    archivo.stat().st_size
    for archivo in archivos
)

print("======================================")
print("PRODUCTOR RAW -> KAFKA -> HDFS")
print("======================================")

print(f"Carpeta origen: {RAW_DIR}")
print(f"Topic: {TOPIC}")
print(f"Archivos encontrados: {len(archivos)}")
print(f"Tamano total: {tamano_total / 1048576:.2f} MB")
print(f"Tamano fragmento: {CHUNK_SIZE} bytes")

# ==========================================
# 3. SELECCIONAR ARCHIVOS
# ==========================================

if MODO_PRUEBA:

    if not ARCHIVO_PRUEBA.is_file():
        raise FileNotFoundError(
            f"No existe: {ARCHIVO_PRUEBA}"
        )

    archivos = [ARCHIVO_PRUEBA]

    print("\nMODO PRUEBA ACTIVADO")
    print(
        f"Archivo seleccionado: "
        f"{ARCHIVO_PRUEBA.relative_to(RAW_DIR)}"
    )

else:

    print("\nMODO COMPLETO ACTIVADO")
    print(f"Archivos seleccionados: {len(archivos)}")

# ==========================================
# 4. CONFIGURAR PRODUCTOR KAFKA
# ==========================================

producer = Producer({
    "bootstrap.servers": KAFKA_SERVERS,
    "client.id": "euskadi-vivienda-raw-producer",
    "acks": "all",
    "enable.idempotence": True,
    "message.max.bytes": 1000000
})

mensajes_entregados = 0
errores = 0

def confirmar_entrega(err, msg):
    global mensajes_entregados, errores

    if err is not None:
        errores += 1
        print(f"ERROR DE ENTREGA: {err}")
    else:
        mensajes_entregados += 1

# ==========================================
# 5. FUNCION PARA CALCULAR SHA-256
# ==========================================

def calcular_sha256(ruta):

    hash_archivo = hashlib.sha256()

    with ruta.open("rb") as f:

        for bloque in iter(
            lambda: f.read(1024 * 1024),
            b""
        ):
            hash_archivo.update(bloque)

    return hash_archivo.hexdigest()

# ==========================================
# 6. ENVIAR ARCHIVOS A KAFKA
# ==========================================

inicio = time.time()

mensajes_enviados = 0
archivos_enviados = 0

for archivo in archivos:

    ruta_relativa = archivo.relative_to(
        RAW_DIR
    ).as_posix()

    tamano = archivo.stat().st_size

    sha256 = calcular_sha256(archivo)

    total_chunks = max(
        1,
        math.ceil(tamano / CHUNK_SIZE)
    )

    transfer_id = str(uuid.uuid4())

    print("\n--------------------------------------")
    print(f"Archivo: {ruta_relativa}")
    print(f"Tamano: {tamano} bytes")
    print(f"Fragmentos: {total_chunks}")
    print(f"SHA-256: {sha256}")

    entregados_antes = mensajes_entregados
    errores_antes = errores

    with archivo.open("rb") as f:

        for chunk_index in range(total_chunks):

            contenido = f.read(CHUNK_SIZE)

            mensaje = {
                "tipo": "raw_hdfs_chunk",
                "version": 1,
                "transfer_id": transfer_id,
                "ruta_relativa": ruta_relativa,
                "tamano_total": tamano,
                "sha256": sha256,
                "chunk_index": chunk_index,
                "total_chunks": total_chunks,
                "contenido_base64": base64.b64encode(
                    contenido
                ).decode("ascii")
            }

            payload = json.dumps(
                mensaje,
                ensure_ascii=False
            ).encode("utf-8")

            while True:

                try:

                    producer.produce(
                        topic=TOPIC,
                        key=transfer_id.encode("utf-8"),
                        value=payload,
                        on_delivery=confirmar_entrega
                    )

                    break

                except BufferError:
                    producer.poll(1)

            producer.poll(0)

            mensajes_enviados += 1

    # Esperar confirmacion de entrega
    pendientes = producer.flush(timeout=120)

    entregados_archivo = (
        mensajes_entregados - entregados_antes
    )

    errores_archivo = (
        errores - errores_antes
    )

    if (
        pendientes != 0
        or errores_archivo != 0
        or entregados_archivo != total_chunks
    ):
        raise RuntimeError(
            f"Error enviando {ruta_relativa}. "
            f"Entregados: {entregados_archivo}, "
            f"Esperados: {total_chunks}, "
            f"Errores: {errores_archivo}, "
            f"Pendientes: {pendientes}"
        )

    archivos_enviados += 1

    print(
        f"Fragmentos entregados: "
        f"{entregados_archivo}/{total_chunks}"
    )

    print("ARCHIVO ENVIADO CORRECTAMENTE A KAFKA")

# ==========================================
# 7. RESULTADO FINAL
# ==========================================

pendientes = producer.flush(timeout=120)

duracion = time.time() - inicio

print("\n======================================")
print("RESULTADO FINAL")
print("======================================")

print(f"Archivos enviados: {archivos_enviados}")
print(f"Mensajes producidos: {mensajes_enviados}")
print(f"Mensajes entregados: {mensajes_entregados}")
print(f"Errores: {errores}")
print(f"Pendientes: {pendientes}")
print(f"Tiempo: {duracion:.2f} segundos")

if (
    errores == 0
    and pendientes == 0
    and mensajes_entregados == mensajes_enviados
):
    print("ENVIO A KAFKA COMPLETADO")
else:
    raise RuntimeError(
        "La transferencia no se completo"
    )
