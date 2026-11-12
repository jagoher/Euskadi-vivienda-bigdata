
import os
import matplotlib.pyplot as plt
import seaborn as sns

from pathlib import Path
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.errors import PyMongoError

# ==========================================
# CONFIGURACIÓN
# ==========================================

RAIZ = Path(__file__).resolve().parents[2]

load_dotenv(RAIZ / ".env")

MONGODB_URI = os.getenv("MONGODB_URI")
DATABASE_NAME = os.getenv("DATABASE_NAME")

SALIDA = RAIZ / "resultados" / "graficos"
SALIDA.mkdir(parents=True, exist_ok=True)

client = None

try:
    if not MONGODB_URI or not DATABASE_NAME:
        raise ValueError("Faltan variables en el .env")

    # ==========================================
    # CONEXIÓN
    # ==========================================

    client = MongoClient(
        MONGODB_URI,
        serverSelectionTimeoutMS=5000
    )

    client.admin.command("ping")

    db = client[DATABASE_NAME]

    if "municipios" not in db.list_collection_names():
        raise ValueError("La colección municipios no existe")

    # ==========================================
    # CONSULTA PYMONGO
    # ==========================================

    filtro = {
        "indicadores.esfuerzo_alquiler_pct": {
            "$type": "number",
            "$lte": 30
        }
    }

    proyeccion = {
        "_id": 0,
        "nombre": 1,
        "indicadores.esfuerzo_alquiler_pct": 1
    }

    resultados = list(
        db.municipios.find(filtro, proyeccion)
        .sort("indicadores.esfuerzo_alquiler_pct", 1)
    )

    if not resultados:
        raise ValueError("No hay municipios para representar")

    nombres = [m["nombre"] for m in resultados]

    esfuerzos = [
        m["indicadores"]["esfuerzo_alquiler_pct"]
        for m in resultados
    ]

    # ==========================================
    # GRÁFICO
    # ==========================================

    sns.set_theme(style="whitegrid")

    fig, ax = plt.subplots(figsize=(12, 6))

    sns.barplot(
        x=esfuerzos,
        y=nombres,
        color="seagreen",
        ax=ax
    )

    # Línea de referencia del 30 %
    ax.axvline(
        x=30,
        color="red",
        linestyle="--",
        linewidth=2,
        label="Umbral del 30 %"
    )

    # Etiquetas de porcentaje
    for i, valor in enumerate(esfuerzos):
        ax.text(
            valor + 0.15,
            i,
            f"{valor:.2f} %",
            va="center"
        )

    ax.set_title(
        "Municipios con esfuerzo de alquiler ≤ 30 %",
        fontsize=15,
        fontweight="bold"
    )

    ax.set_xlabel("Esfuerzo de alquiler (%)")
    ax.set_ylabel("Municipio")
    ax.set_xlim(0, 35)
    ax.legend()

    plt.tight_layout()

    # ==========================================
    # GUARDAR Y MOSTRAR
    # ==========================================

    archivo = SALIDA / "04_municipios_asequibles.png"

    plt.savefig(
        archivo,
        dpi=300,
        bbox_inches="tight"
    )

    print(f"Gráfico guardado en: {archivo}")
    print(f"Municipios representados: {len(resultados)}")

    plt.show()
    plt.close(fig)

except (PyMongoError, ValueError, KeyError) as error:
    print(f"ERROR: {error}")

finally:
    if client is not None:
        client.close()