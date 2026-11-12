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

TOPIC = os.getenv("KAFKA_TOPIC", "euskadi_vivienda_user6")
ARCHIVO = BASE_DIR / "data" / "mongodb" / "compraventa_euskadi_clasificado_v3.json"
if not ARCHIVO.is_file():
    raise FileNotFoundError(f"No existe el archivo: {ARCHIVO}")

with ARCHIVO.open("r", encoding="utf-8-sig") as f:
    anuncios = json.load(f)
if not isinstance(anuncios, list):
    raise ValueError("Se esperaba una lista de anuncios JSON")
print(f"Anuncios disponibles: {len(anuncios)}")

producer = Producer({
    "bootstrap.servers": BOOTSTRAP_SERVERS,
    "client.id": socket.gethostname()
})
resultado = {"entregados": 0, "errores": 0}

def confirmar_entrega(err, msg):
    if err is not None:
        resultado["errores"] += 1
        print(f"ERROR: {err}")
    else:
        resultado["entregados"] += 1
        print(f"Entregado: particion={msg.partition()}, offset={msg.offset()}")

for anuncio in anuncios[:10]:
    mensaje = json.dumps(anuncio, ensure_ascii=False, default=str).encode("utf-8")
    producer.produce(topic=TOPIC, value=mensaje, callback=confirmar_entrega)
    producer.poll(0)

pendientes = producer.flush(timeout=30)
print("\nRESULTADO DEL ENVIO")
print(f"Topic: {TOPIC}")
print(f"Entregados: {resultado['entregados']}")
print(f"Errores: {resultado['errores']}")
print(f"Pendientes: {pendientes}")
if resultado["errores"] or pendientes:
    raise RuntimeError("El envio no se ha completado correctamente")
