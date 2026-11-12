
from pathlib import Path, PurePosixPath
from dotenv import load_dotenv
from confluent_kafka import Consumer, KafkaException
from hdfs import InsecureClient
import os
import json
import base64
import hashlib
import time

# ==========================================
# 1. CONFIGURACION
# ==========================================

BASE_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BASE_DIR / ".env")

KAFKA_SERVERS = os.getenv("BOOTSTRAP_SERVERS")
TOPIC = os.getenv("KAFKA_HDFS_TOPIC")
HDFS_URL = os.getenv("HDFS_ADDRESS_CLUSTER")
HDFS_USER = os.getenv("HDFS_USER")
HDFS_BASE = os.getenv("HDFS_BASE")

GROUP = os.getenv(
    "KAFKA_HDFS_GROUP",
    "euskadi_vivienda_hdfs_consumidor_user6"
)

if not all((
    KAFKA_SERVERS, TOPIC, HDFS_URL,
    HDFS_USER, HDFS_BASE
)):
    raise RuntimeError("Faltan variables en .env")

HDFS_BASE = HDFS_BASE.rstrip("/")

RUTA_ESPERADA = (
    f"/user/{HDFS_USER}/euskadi_vivienda"
)

if HDFS_BASE != RUTA_ESPERADA:
    raise RuntimeError("Ruta HDFS inesperada")

# ==========================================
# 2. CONEXIONES
# ==========================================

hdfs = InsecureClient(HDFS_URL, user=HDFS_USER)

consumer = Consumer({
    "bootstrap.servers": KAFKA_SERVERS,
    "group.id": GROUP,
    "auto.offset.reset": "earliest",
    "enable.auto.commit": False
})

consumer.subscribe([TOPIC])

print("================================")
print("CONSUMIDOR KAFKA -> HDFS")
print("================================")
print(f"Topic: {TOPIC}")
print(f"Destino: {HDFS_BASE}")

# ==========================================
# 3. CONSUMIR Y GUARDAR
# ==========================================

procesados = 0
inicio = time.monotonic()

try:
    while procesados < 1:

        msg = consumer.poll(2.0)

        if msg is None:
            if time.monotonic() - inicio > 30:
                print("No se recibieron mensajes en 30 segundos")
                break
            continue

        if msg.error():
            raise KafkaException(msg.error())

        mensaje = json.loads(msg.value().decode("utf-8"))

        if mensaje.get("tipo") != "archivo_hdfs":
            print("Mensaje de otro tipo. Omitido.")
            consumer.commit(message=msg, asynchronous=False)
            continue

        carpeta = mensaje["carpeta"]
        nombre = mensaje["nombre_archivo"]

        # Evitar rutas fuera del proyecto
        if carpeta not in ("raw", "processed", "mongodb"):
            raise ValueError("Carpeta no permitida")

        ruta_relativa = PurePosixPath(nombre)

        if (
            ruta_relativa.is_absolute()
            or ".." in ruta_relativa.parts
            or "\\" in nombre
        ):
            raise ValueError("Nombre de archivo no permitido")

        contenido = base64.b64decode(
            mensaje["contenido_base64"],
            validate=True
        )

        sha_calculado = hashlib.sha256(
            contenido
        ).hexdigest()

        if sha_calculado != mensaje["sha256"]:
            raise ValueError("SHA-256 incorrecto")

        if len(contenido) != mensaje["tamano_bytes"]:
            raise ValueError("Tamano incorrecto")

        ruta_hdfs = (
            f"{HDFS_BASE}/{carpeta}/{ruta_relativa}"
        )

        print(f"\nArchivo recibido: {nombre}")
        print(f"Bytes: {len(contenido)}")
        print(f"Offset Kafka: {msg.offset()}")

        # Crear carpeta destino si no existe
        directorio = str(PurePosixPath(ruta_hdfs).parent)
        hdfs.makedirs(directorio)

        # Escribir el archivo en HDFS
        with hdfs.write(
            ruta_hdfs,
            overwrite=True
        ) as writer:
            writer.write(contenido)

        # Leer de nuevo desde HDFS
        with hdfs.read(ruta_hdfs) as reader:
            contenido_hdfs = reader.read()

        sha_hdfs = hashlib.sha256(
            contenido_hdfs
        ).hexdigest()

        if sha_hdfs != mensaje["sha256"]:
            raise RuntimeError(
                "El archivo HDFS no coincide con el original"
            )

        # Confirmar offset solo tras verificar HDFS
        consumer.commit(
            message=msg,
            asynchronous=False
        )

        procesados += 1

        print(f"Guardado en HDFS: {ruta_hdfs}")
        print(f"SHA-256 original: {mensaje['sha256']}")
        print(f"SHA-256 HDFS:    {sha_hdfs}")
        print("INTEGRIDAD VERIFICADA")

finally:
    consumer.close()

print("\nRESULTADO")
print(f"Archivos procesados: {procesados}")
