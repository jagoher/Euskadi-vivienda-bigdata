from confluent_kafka import Consumer, TopicPartition, KafkaException
import json

from pathlib import Path
import os
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BASE_DIR / ".env")

BOOTSTRAP_SERVERS = os.getenv("BOOTSTRAP_SERVERS")
if not BOOTSTRAP_SERVERS:
    raise RuntimeError("Falta BOOTSTRAP_SERVERS en .env")

TOPIC = os.getenv("KAFKA_TOPIC", "euskadi_vivienda_user6")
GRUPO = os.getenv("KAFKA_GROUP", "euskadi_vivienda_consumidor_user6")
consumer = Consumer({
    "bootstrap.servers": BOOTSTRAP_SERVERS,
    "group.id": GRUPO,
    "enable.auto.commit": False,
    "auto.offset.reset": "earliest"
})

# Prueba sobre la particion 0, desde el offset 0.
# Si el topic tiene varias particiones, esta prueba solo lee la particion 0.
consumer.assign([TopicPartition(TOPIC, 0, 0)])
recibidos = 0
intentos_sin_mensaje = 0
print(f"Leyendo anuncios del topic: {TOPIC}")
try:
    while recibidos < 10 and intentos_sin_mensaje < 5:
        msg = consumer.poll(timeout=5.0)
        if msg is None:
            intentos_sin_mensaje += 1
            continue
        if msg.error():
            raise KafkaException(msg.error())
        anuncio = json.loads(msg.value().decode("utf-8"))
        recibidos += 1
        print(f"\nANUNCIO {recibidos}")
        print(f"Offset: {msg.offset()}")
        print(f"Municipio ID: {anuncio.get('municipio_id')}")
        print(f"Precio: {anuncio.get('precio')} EUR")
        print(f"Portal ID: {anuncio.get('id_portal')}")
finally:
    consumer.close()
print(f"\nTotal anuncios recibidos: {recibidos}")
print("Consumidor cerrado")
