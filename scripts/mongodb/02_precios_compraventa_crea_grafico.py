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
            {"$project": {"_id": 0, "nombre": "$municipio.nombre", "precio_medio": 1, "anuncios": 1}},
            {"$sort": {"precio_medio": 1}},
        ]
        rows = list(db.anuncios.aggregate(pipeline))
        if not rows:
            raise ValueError("No se encontraron anuncios válidos enlazados con municipios")
        sns.set_theme(style="whitegrid")
        fig, ax = plt.subplots(figsize=(12, max(6, len(rows) * 0.48 + 2)))
        labels = [r["nombre"] for r in rows]
        values = [r["precio_medio"] for r in rows]
        sns.barplot(x=values, y=labels, color="#4c78a8", ax=ax)
        for i, row in enumerate(rows):
            ax.text(row["precio_medio"] + max(values) * 0.012, i,
                    f"{row['precio_medio']:,.0f} €  ·  {row['anuncios']} anuncios",
                    va="center", fontsize=9)
        ax.set_xlim(0, max(values) * 1.47)
        ax.set_title("Precio medio anunciado de compraventa por municipio", fontweight="bold")
        ax.set_xlabel("Precio medio de oferta (€)")
        ax.set_ylabel("Municipio")
        fig.text(0.01, 0.01, "Precios de anuncios, no precios de compraventas cerradas.", fontsize=9)
        fig.tight_layout(rect=(0, 0.035, 1, 1))
        save_and_show(fig, "02_precios_compraventa.png")
    except (PyMongoError, ValueError, KeyError) as exc:
        print(f"ERROR: {exc}")
    finally:
        if client is not None:
            client.close()


if __name__ == "__main__":
    main()
