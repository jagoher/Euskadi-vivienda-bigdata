from confluent_kafka import Consumer, KafkaException
import json

from pathlib import Path
import os
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BASE_DIR / ".env")

BOOTSTRAP_SERVERS = os.getenv("BOOTSTRAP_SERVERS")
if not BOOTSTRAP_SERVERS:
    raise RuntimeError("Falta BOOTSTRAP_SERVERS en .env")

TOPIC = os.getenv("KAFKA_TEST_TOPIC", "euskadi_vivienda_prueba_user6")
GRUPO = os.getenv("KAFKA_TEST_GROUP", "euskadi_vivienda_prueba_consumidor_user6")
consumer = Consumer({
    "bootstrap.servers": BOOTSTRAP_SERVERS,
    "group.id": GRUPO,
    "auto.offset.reset": "earliest",
    "enable.auto.commit": False
})
consumer.subscribe([TOPIC])
print(f"Escuchando mensajes del topic: {TOPIC}")
recibidos = 0
try:
    while recibidos < 5:
        msg = consumer.poll(timeout=10.0)
        if msg is None:
            print("No hay mas mensajes disponibles")
            break
        if msg.error():
            raise KafkaException(msg.error())
        texto = msg.value().decode("utf-8")
        try:
            datos = json.loads(texto)
        except json.JSONDecodeError:
            datos = texto
        print(f"Mensaje: topic={msg.topic()}, particion={msg.partition()}, offset={msg.offset()}")
        print(f"Contenido: {datos}")
        recibidos += 1
except KeyboardInterrupt:
    print("Lectura interrumpida")
finally:
    consumer.close()
    print("Consumidor Kafka cerrado")
