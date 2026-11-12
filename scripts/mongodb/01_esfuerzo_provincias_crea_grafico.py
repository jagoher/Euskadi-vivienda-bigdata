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
        pipeline = [
            {"$match": {"indicadores.esfuerzo_alquiler_pct": {"$type": "number"}}},
            {"$group": {"_id": "$provincia", "esfuerzo_medio": {"$avg": "$indicadores.esfuerzo_alquiler_pct"}, "municipios": {"$sum": 1}}},
            {"$sort": {"esfuerzo_medio": -1}},
        ]
        rows = list(db.municipios.aggregate(pipeline))
        if not rows:
            raise ValueError("No hay datos de esfuerzo de alquiler")
        sns.set_theme(style="whitegrid")
        fig, ax = plt.subplots(figsize=(10, 6))
        labels = [str(r["_id"]) for r in rows]
        values = [r["esfuerzo_medio"] for r in rows]
        sns.barplot(x=labels, y=values, color="#377eb8", ax=ax)
        ax.axhline(30, color="#c0392b", linestyle="--", linewidth=2, label="Referencia: 30 %")
        for i, (value, row) in enumerate(zip(values, rows)):
            ax.text(i, value + 0.5, f"{value:.2f} %\n(n={row['municipios']})", ha="center", fontsize=10)
        ax.set_ylim(0, max(max(values) + 8, 40))
        ax.set_title("Esfuerzo medio de alquiler por provincia", fontweight="bold")
        ax.set_xlabel("Provincia")
        ax.set_ylabel("Esfuerzo medio (%)")
        ax.legend()
        fig.tight_layout()
        save_and_show(fig, "01_esfuerzo_provincias.png")
    except (PyMongoError, ValueError, KeyError) as exc:
        print(f"ERROR: {exc}")
    finally:
        if client is not None:
            client.close()


if __name__ == "__main__":
    main()
