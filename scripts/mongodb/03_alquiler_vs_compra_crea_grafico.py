import os
from pathlib import Path

import matplotlib.pyplot as plt
import seaborn as sns
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.errors import PyMongoError

ROOT = Path(__file__).resolve().parent
for candidate in (ROOT, *ROOT.parents):
    if (candidate / ".env").is_file():
        ROOT = candidate
        break
load_dotenv(ROOT / ".env")
OUTPUT_DIR = ROOT / "resultados" / "graficos"


def get_database():
    uri = os.getenv("MONGODB_URI")
    name = os.getenv("DATABASE_NAME")
    if not uri or not name:
        raise ValueError("Configura MONGODB_URI y DATABASE_NAME en .env")
    client = MongoClient(uri, serverSelectionTimeoutMS=5000)
    try:
        client.admin.command("ping")
        db = client[name]
        if "municipios" not in db.list_collection_names():
            raise ValueError("No existe la colección municipios")
        return client, db
    except Exception:
        client.close()
        raise


def save_and_show(fig, filename):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUTPUT_DIR / filename
    fig.savefig(path, dpi=300, bbox_inches="tight")
    print(f"Gráfico guardado en: {path}")
    plt.show()
    plt.close(fig)

def main():
    client = None
    try:
        client, db = get_database()
        if "anuncios" not in db.list_collection_names():
            raise ValueError("No existe la colección anuncios")
        pipeline = [
            {"$match": {
                "operacion": "venta",
                "precio": {"$type": "number", "$gt": 0},
                "calidad.precio_no_valido": {"$ne": True},
                "calidad.posible_duplicado": {"$ne": True},
                "calidad.posible_duplicado_ampliado": {"$ne": True},
                "municipio_id": {"$type": "string"},
            }},
            {"$group": {"_id": "$municipio_id", "precio_medio": {"$avg": "$precio"}, "anuncios": {"$sum": 1}}},
            {"$lookup": {"from": "municipios", "localField": "_id", "foreignField": "_id", "as": "municipio"}},
            {"$unwind": "$municipio"},
            {"$match": {
                "municipio.indicadores.esfuerzo_alquiler_pct": {"$type": "number"},
                "municipio.indicadores.salario_neto_mensual": {"$type": "number", "$gt": 0},
            }},
            {"$project": {
                "_id": 0,
                "nombre": "$municipio.nombre",
                "esfuerzo": "$municipio.indicadores.esfuerzo_alquiler_pct",
                "anuncios": 1,
                "anios_teoricos": {"$divide": ["$precio_medio", {"$multiply": ["$municipio.indicadores.salario_neto_mensual", 12]}]},
            }},
            {"$sort": {"esfuerzo": 1}},
        ]
        rows = list(db.anuncios.aggregate(pipeline))
        if not rows:
            raise ValueError("No hay municipios con datos suficientes para el gráfico")
        sns.set_theme(style="whitegrid")
        fig, ax = plt.subplots(figsize=(12, 8))
        x = [r["esfuerzo"] for r in rows]
        y = [r["anios_teoricos"] for r in rows]
        ax.scatter(x, y, s=95, color="#2a9d8f", edgecolor="white", linewidth=0.8, zorder=3)
        for row in rows:
            ax.annotate(row["nombre"], (row["esfuerzo"], row["anios_teoricos"]),
                        xytext=(5, 5), textcoords="offset points", fontsize=9)
        ax.axvline(30, color="#c0392b", linestyle="--", linewidth=1.5, label="Referencia alquiler: 30 %")
        ax.set_xlim(min(25, min(x) - 3), max(x) + 12)
        ax.set_ylim(0, max(y) * 1.15)
        ax.set_title("Esfuerzo de alquiler frente a años teóricos para comprar", fontweight="bold")
        ax.set_xlabel("Esfuerzo de alquiler (%)")
        ax.set_ylabel("Años de salario neto para cubrir el precio medio anunciado")
        ax.legend(loc="upper left")
        fig.text(0.01, 0.01,
                 "Indicador teórico: precio anunciado / (salario mensual de referencia × 12). No contempla gastos ni ahorro real.",
                 fontsize=8.5)
        fig.tight_layout(rect=(0, 0.04, 1, 1))
        save_and_show(fig, "03_alquiler_vs_compra.png")
    except (PyMongoError, ValueError, KeyError, ZeroDivisionError) as exc:
        print(f"ERROR: {exc}")
    finally:
        if client is not None:
            client.close()


if __name__ == "__main__":
    main()
