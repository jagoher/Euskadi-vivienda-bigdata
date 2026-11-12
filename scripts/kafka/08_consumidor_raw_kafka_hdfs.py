
from pathlib import Path, PurePosixPath
from collections import defaultdict
from dotenv import load_dotenv
from confluent_kafka import Consumer, TopicPartition, KafkaError
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

HDFS_ADDRESS = os.getenv("HDFS_ADDRESS_CLUSTER")
HDFS_USER = os.getenv("HDFS_USER")
HDFS_BASE = os.getenv("HDFS_BASE")

if not all([
    KAFKA_SERVERS,
    TOPIC,
    HDFS_ADDRESS,
    HDFS_USER,
    HDFS_BASE
]):
    raise RuntimeError(
        "Faltan variables de Kafka o HDFS en .env"
    )

RAW_HDFS = HDFS_BASE.rstrip("/") + "/raw"

# True: recuperar solo el archivo de prueba
# False: recuperar todos los archivos RAW del topic
MODO_PRUEBA = True

ARCHIVO_PRUEBA = "eustat/ep10b_20261027-201118.csv"

# El consumidor comienza desde el inicio del topic.
# No utiliza commits anteriores para decidir
# desde donde reconstruir los archivos.
#
# IMPORTANTE: el topic debe conservar los mensajes.
# Si Kafka los ha eliminado por retencion,
# no sera posible recuperar esos fragmentos.

TIEMPO_ESPERA = 30
TIEMPO_MAXIMO = 300

# ==========================================
# 2. CONEXION HDFS
# ==========================================

hdfs_client = InsecureClient(
    HDFS_ADDRESS,
    user=HDFS_USER
)

# ==========================================
# 3. FUNCIONES AUXILIARES
# ==========================================

def calcular_sha256(contenido):
    return hashlib.sha256(contenido).hexdigest()


def validar_ruta(ruta_relativa):

    if not isinstance(ruta_relativa, str):
        raise ValueError("Ruta relativa no valida")

    ruta = PurePosixPath(ruta_relativa)

    if (
        ruta.is_absolute()
        or not ruta.parts
        or any(p in (".", "..") for p in ruta.parts)
        or "\\" in ruta_relativa
        or ":" in ruta_relativa
    ):
        raise ValueError(
            f"Ruta no permitida: {ruta_relativa}"
        )

    return ruta.as_posix()


def guardar_en_hdfs(ruta_relativa, contenido):

    ruta_relativa = validar_ruta(ruta_relativa)

    ruta_hdfs = RAW_HDFS + "/" + ruta_relativa

    carpeta_hdfs = ruta_hdfs.rsplit("/", 1)[0]

    hdfs_client.makedirs(carpeta_hdfs)

    # Si el archivo ya existe y coincide con el
    # original, evitamos escribirlo otra vez.
    if hdfs_client.status(ruta_hdfs, strict=False):

        with hdfs_client.read(ruta_hdfs) as lector:
            existente = lector.read()

        if calcular_sha256(existente) == calcular_sha256(contenido):
            print("El archivo ya existe y es identico.")
            print(f"VERIFICADO: {ruta_hdfs}")
            return ruta_hdfs

    # Escritura del archivo reconstruido
    with hdfs_client.write(
        ruta_hdfs,
        overwrite=True
    ) as escritor:
        escritor.write(contenido)

    # Comprobacion leyendo desde HDFS
    with hdfs_client.read(ruta_hdfs) as lector:
        contenido_hdfs = lector.read()

    if len(contenido_hdfs) != len(contenido):
        raise RuntimeError(
            "El tamano en HDFS no coincide"
        )

    if calcular_sha256(contenido_hdfs) != calcular_sha256(contenido):
        raise RuntimeError(
            "El SHA-256 de HDFS no coincide"
        )

    print(f"Guardado: {ruta_hdfs}")
    print(f"Tamano: {len(contenido_hdfs)} bytes")
    print(f"SHA-256: {calcular_sha256(contenido_hdfs)}")
    print("INTEGRIDAD VERIFICADA")

    return ruta_hdfs


# ==========================================
# 4. CONFIGURAR CONSUMIDOR KAFKA
# ==========================================

consumer = Consumer({
    "bootstrap.servers": KAFKA_SERVERS,
    "group.id": os.getenv(
        "KAFKA_RAW_HDFS_GROUP",
        "euskadi_vivienda_raw_hdfs_user6"
    ) + "_reconstruccion",
    "auto.offset.reset": "earliest",
    "enable.auto.commit": False,
    "enable.partition.eof": True
})

print("======================================")
print("CONSUMIDOR KAFKA -> HDFS")
print("======================================")
print(f"Topic: {TOPIC}")
print(f"Destino: {RAW_HDFS}")
print(f"Modo prueba: {MODO_PRUEBA}")
print(f"Archivo prueba: {ARCHIVO_PRUEBA}")

# ==========================================
# 5. LEER TOPIC DESDE EL PRINCIPIO
# ==========================================

# Consultamos las particiones para leer todo
# el historial disponible, sin depender de
# offsets guardados de ejecuciones anteriores.

metadata = consumer.list_topics(
    topic=TOPIC,
    timeout=15
)

if TOPIC not in metadata.topics:
    raise RuntimeError(
        f"No existe el topic {TOPIC}"
    )

particiones = list(
    metadata.topics[TOPIC].partitions.keys()
)

if not particiones:
    raise RuntimeError(
        "El topic no tiene particiones"
    )

# Guardamos el final del topic en el momento
# de comenzar. Asi el programa termina cuando
# haya leido los mensajes que ya existen.

limites = {}

for particion in particiones:

    low, high = consumer.get_watermark_offsets(
        TopicPartition(TOPIC, particion),
        timeout=15,
        cached=False
    )

    limites[particion] = {
        "inicio": low,
        "fin": high
    }

consumer.assign([
    TopicPartition(
        TOPIC,
        particion,
        limites[particion]["inicio"]
    )
    for particion in particiones
])

print(f"Particiones: {particiones}")
print(f"Limites: {limites}")

# ==========================================
# 6. RECONSTRUCCION DE ARCHIVOS
# ==========================================

transferencias = {}
archivos_guardados = set()
fragmentos_recibidos = 0
mensajes_ignorados = 0

# Ultima posicion leida por particion
posiciones = {
    p: limites[p]["inicio"]
    for p in particiones
}

inicio = time.time()
ultima_actividad = time.time()

try:

    while True:

        # Hemos alcanzado el final del historial
        # disponible al comenzar.
        terminado = all(
            posiciones[p] >= limites[p]["fin"]
            for p in particiones
        )

        if terminado:
            print("\nFin del historial Kafka.")
            break

        if time.time() - inicio > TIEMPO_MAXIMO:
            raise TimeoutError(
                "Tiempo maximo de lectura agotado"
            )

        if time.time() - ultima_actividad > TIEMPO_ESPERA:
            raise TimeoutError(
                "No se reciben mensajes de Kafka"
            )

        msg = consumer.poll(1.0)

        if msg is None:
            continue

        if msg.error():

            if msg.error().code() == KafkaError._PARTITION_EOF:
                continue

            raise RuntimeError(
                f"Error Kafka: {msg.error()}"
            )

        particion = msg.partition()
        offset = msg.offset()

        # No procesar mensajes publicados despues
        # del inicio de esta ejecucion.
        if offset >= limites[particion]["fin"]:
            posiciones[particion] = limites[particion]["fin"]
            continue

        posiciones[particion] = max(
            posiciones[particion],
            offset + 1
        )

        ultima_actividad = time.time()

        try:
            mensaje = json.loads(
                msg.value().decode("utf-8")
            )
        except (ValueError, UnicodeDecodeError):
            mensajes_ignorados += 1
            continue

        if mensaje.get("tipo") != "raw_hdfs_chunk":
            mensajes_ignorados += 1
            continue

        if mensaje.get("version") != 1:
            mensajes_ignorados += 1
            continue

        ruta_relativa = validar_ruta(
            mensaje["ruta_relativa"]
        )

        if (
            MODO_PRUEBA
            and ruta_relativa != ARCHIVO_PRUEBA
        ):
            mensajes_ignorados += 1
            continue

        transfer_id = mensaje["transfer_id"]
        chunk_index = mensaje["chunk_index"]
        total_chunks = mensaje["total_chunks"]
        tamano_total = mensaje["tamano_total"]
        sha256 = mensaje["sha256"]

        if (
            not isinstance(chunk_index, int)
            or not isinstance(total_chunks, int)
            or not isinstance(tamano_total, int)
            or total_chunks < 1
            or chunk_index < 0
            or chunk_index >= total_chunks
            or tamano_total < 0
        ):
            raise ValueError(
                "Metadatos de fragmento invalidos"
            )

        contenido = base64.b64decode(
            mensaje["contenido_base64"],
            validate=True
        )

        # Identificamos cada transferencia mediante
        # su ID unico, no solamente por el nombre.
        if transfer_id not in transferencias:

            transferencias[transfer_id] = {
                "ruta": ruta_relativa,
                "tamano": tamano_total,
                "sha256": sha256,
                "total_chunks": total_chunks,
                "chunks": {}
            }

            print("\n--------------------------------------")
            print(f"Archivo: {ruta_relativa}")
            print(f"Fragmentos esperados: {total_chunks}")

        transferencia = transferencias[transfer_id]

        if (
            transferencia["ruta"] != ruta_relativa
            or transferencia["tamano"] != tamano_total
            or transferencia["sha256"] != sha256
            or transferencia["total_chunks"] != total_chunks
        ):
            raise RuntimeError(
                "Metadatos inconsistentes"
            )

        if chunk_index in transferencia["chunks"]:

            if (
                transferencia["chunks"][chunk_index]
                != contenido
            ):
                raise RuntimeError(
                    "Fragmento duplicado con contenido distinto"
                )

            continue

        transferencia["chunks"][chunk_index] = contenido
        fragmentos_recibidos += 1

        print(
            f"\rFragmentos recibidos: "
            f"{len(transferencia['chunks'])}/{total_chunks}",
            end="",
            flush=True
        )

        # ======================================
        # 7. ARCHIVO COMPLETO
        # ======================================

        if len(transferencia["chunks"]) == total_chunks:

            print()

            contenido_completo = b"".join(
                transferencia["chunks"][i]
                for i in range(total_chunks)
            )

            if len(contenido_completo) != tamano_total:
                raise RuntimeError(
                    "Tamano reconstruido incorrecto"
                )

            sha256_calculado = calcular_sha256(
                contenido_completo
            )

            if sha256_calculado != sha256:
                raise RuntimeError(
                    "SHA-256 reconstruido incorrecto"
                )

            print("Archivo reconstruido correctamente.")
            print(f"SHA-256: {sha256_calculado}")

            guardar_en_hdfs(
                ruta_relativa,
                contenido_completo
            )

            archivos_guardados.add(ruta_relativa)

            # Liberar memoria
            del transferencias[transfer_id]

            # En modo prueba podemos terminar al
            # verificar el archivo seleccionado.
            if MODO_PRUEBA:
                print("\nPRUEBA COMPLETADA")
                break

    # ==========================================
    # 8. COMPROBAR TRANSFERENCIAS PENDIENTES
    # ==========================================

    if transferencias:

        print("\nTRANSFERENCIAS INCOMPLETAS:")

        for transferencia in transferencias.values():

            print(
                f"{transferencia['ruta']}: "
                f"{len(transferencia['chunks'])}/"
                f"{transferencia['total_chunks']}"
            )

        raise RuntimeError(
            "Hay transferencias incompletas"
        )

    if MODO_PRUEBA and ARCHIVO_PRUEBA not in archivos_guardados:
        raise RuntimeError(
            "No se encontro el archivo de prueba completo"
        )

    # No realizamos commits porque este consumidor
    # relee el historial desde el inicio y comprueba
    # los archivos ya existentes en HDFS.
    #
    # Asi, un reinicio no depende de offsets
    # confirmados antes de terminar un archivo.

    print("\n======================================")
    print("RESULTADO FINAL")
    print("======================================")

    print(f"Archivos verificados: {len(archivos_guardados)}")
    print(f"Fragmentos recibidos: {fragmentos_recibidos}")
    print(f"Mensajes ignorados: {mensajes_ignorados}")
    print(f"Tiempo: {time.time() - inicio:.2f} segundos")

    print("CONSUMIDOR FINALIZADO CORRECTAMENTE")

finally:

    consumer.close()
