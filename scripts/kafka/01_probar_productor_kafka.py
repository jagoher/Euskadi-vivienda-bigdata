from confluent_kafka import Producer
import json
import socket

from pathlib import Path
import os
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BASE_DIR / ".env")

BOOTSTRAP_SERVERS = os.getenv("BOOTSTRAP_SERVERS")
if not BOOTSTRAP_SERVERS:
    raise RuntimeError("Falta BOOTSTRAP_SERVERS en .env")

TOPIC = os.getenv("KAFKA_TEST_TOPIC", "euskadi_vivienda_prueba_user6")
producer = Producer({
    "bootstrap.servers": BOOTSTRAP_SERVERS,
    "client.id": socket.gethostname()
})

def confirmar_entrega(err, msg):
    if err is not None:
        print(f"ERROR al enviar: {err}")
    else:
        print(f"Entregado: topic={msg.topic()}, particion={msg.partition()}, offset={msg.offset()}")

mensaje = {"municipio": "Bilbao", "tipo": "vivienda", "evento": "prueba_conexion"}
producer.produce(
    topic=TOPIC,
    value=json.dumps(mensaje, ensure_ascii=False).encode("utf-8"),
    callback=confirmar_entrega
)
pendientes = producer.flush(timeout=10)
if pendientes:
    raise RuntimeError(f"Quedan {pendientes} mensajes sin entregar")
print("Prueba de productor Kafka finalizada")
