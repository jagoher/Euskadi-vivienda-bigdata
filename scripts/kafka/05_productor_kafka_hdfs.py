
from pathlib import Path
from dotenv import load_dotenv
from confluent_kafka import Producer
import os
import json
import hashlib
import base64
import socket
import uuid

# ==========================================
# 1. CONFIGURACION DESDE .ENV
# ==========================================

BASE_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BASE_DIR / ".env")

KAFKA_SERVERS = os.getenv("BOOTSTRAP_SERVERS")
TOPIC = os.getenv("KAFKA_HDFS_TOPIC")

if not KAFKA_SERVERS or not TOPIC:
    raise RuntimeError(
        "Faltan BOOTSTRAP_SERVERS o KAFKA_HDFS_TOPIC en .env"
    )

# ==========================================
# 2. ARCHIVO QUE VAMOS A ENVIAR
# ==========================================

ARCHIVO = (
    BASE_DIR
    / "data"
    / "processed"
    / "catalogo_municipios_euskadi_2026.csv"
)

if not ARCHIVO.is_file():
    raise FileNotFoundError(
        f"No existe el archivo: {ARCHIVO}"
    )

# ==========================================
# 3. LEER Y PREPARAR LOS DATOS
# ==========================================

contenido = ARCHIVO.read_bytes()

hash_sha256 = hashlib.sha256(contenido).hexdigest()

# Base64 permite transportar los bytes del CSV
# sin modificar su contenido original.
contenido_base64 = base64.b64encode(
    contenido
).decode("ascii")

mensaje = {
    "transfer_id": str(uuid.uuid4()),
    "tipo": "archivo_hdfs",
    "carpeta": "processed",
    "nombre_archivo": ARCHIVO.name,
    "tamano_bytes": len(contenido),
    "sha256": hash_sha256,
    "contenido_base64": contenido_base64
}

mensaje_json = json.dumps(
    mensaje,
    ensure_ascii=False
).encode("utf-8")

# ==========================================
# 4. CONFIGURAR PRODUCTOR KAFKA
# ==========================================

producer = Producer({
    "bootstrap.servers": KAFKA_SERVERS,
    "client.id": socket.gethostname(),
    "message.max.bytes": 1000000
})

entregados = 0
errores = 0

def confirmar_entrega(err, msg):
    global entregados, errores

    if err is not None:
        errores += 1
        print(f"ERROR DE ENTREGA: {err}")
    else:
        entregados += 1
        print("Mensaje entregado correctamente")
        print(f"Topic: {msg.topic()}")
        print(f"Particion: {msg.partition()}")
        print(f"Offset: {msg.offset()}")

# ==========================================
# 5. ENVIAR ARCHIVO A KAFKA
# ==========================================

print("================================")
print("PRODUCTOR KAFKA -> HDFS")
print("================================")

print(f"Archivo: {ARCHIVO.name}")
print(f"Tamano: {len(contenido)} bytes")
print(f"SHA-256: {hash_sha256}")
print(f"Topic: {TOPIC}")

try:
    producer.produce(
        topic=TOPIC,
        key=mensaje["transfer_id"].encode("utf-8"),
        value=mensaje_json,
        callback=confirmar_entrega
    )

    pendientes = producer.flush(timeout=30)

    print("\nRESULTADO")
    print(f"Entregados: {entregados}")
    print(f"Errores: {errores}")
    print(f"Pendientes: {pendientes}")

    if entregados != 1 or errores != 0 or pendientes != 0:
        raise RuntimeError(
            "No se ha confirmado la entrega del archivo"
        )

except Exception as e:
    print(f"Error al enviar el archivo: {e}")
    raise
